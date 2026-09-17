# 项目介绍 · 知识库 Agent 助手

> 一个基于 LangGraph 的多工具 ReAct Agent 应用：LLM 自主决定「检索知识库 / 联网搜索 / 查数据库」，
> 全链路 SSE 流式输出，前端实时渲染 token 与工具调用过程。
>
> **技术栈**：Python · FastAPI · LangChain / LangGraph · Milvus · SSE · Vue 3 · TypeScript · Vite

---

## 一、项目概览

| 项目 | 说明 |
| --- | --- |
| 定位 | 个人独立开发的 Agent 应用，用于验证「LLM 自主工具编排 + RAG + 流式交互」的完整工程落地 |
| 代码规模 | 后端 13 个文件 / 前端 10 个文件，无脚手架代码，全部手写 |
| 核心能力 | 多轮对话 · 工具自主路由 · 知识库 RAG · 流式响应 · 会话记忆 · 文档入库管道 |
| 运行成本 | 只用到一个 OpenAI 兼容的 LLM API Key；Milvus 单机 Docker 一键启动 |

**一句话演示脚本**：

1. 问「这个月卖得最好的商品是什么」→ Agent 自主生成 SQL 查询数据库并汇总回答
2. 问「最近 AI Agent 有什么新进展」→ Agent 切换为联网搜索工具
3. 上传一份 PDF 后问文档里的细节 → Agent 走 Milvus 向量检索，回答附带来源片段

---

## 二、系统架构

```
                        用户
                         │
        ┌────────────────▼─────────────────┐
        │  Vue3 + TypeScript 前端           │
        │  流式对话 UI / 知识库管理页        │
        └────────────────┬─────────────────┘
                         │ POST /api/chat/stream (SSE)
        ┌────────────────▼─────────────────┐
        │  FastAPI 后端                     │
        │  SSE 流式响应 / 会话管理 / 路由    │
        └────────────────┬─────────────────┘
                         │
        ┌────────────────▼─────────────────┐
        │  LangGraph ReAct Agent（核心）     │
        │  推理循环 · 工具调用 · 会话记忆     │
        └───┬──────────────┬───────────────┬┘
            │              │               │
      ┌─────▼─────┐  ┌─────▼─────┐  ┌──────▼──────┐
      │ Milvus    │  │ 联网搜索   │  │ SQL 查询    │
      │ 向量检索   │  │ (ddgs)    │  │ (SQLite)    │
      └─────▲─────┘  └───────────┘  └─────────────┘
            │
   ┌────────┴─────────────────────────┐
   │ 知识入库后台管道（文档上传触发）    │
   │ 解析 → 切分 → Embedding → 入库    │
   └──────────────────────────────────┘
```

**数据流**：前端 POST 问题 → FastAPI 组装历史消息 → Agent 进入推理循环 →
每轮通过 `astream_events` 吐出「token / 工具开始 / 工具结束」三类事件 →
SSE 实时推送前端 → 前端逐 token 渲染并展示工具调用状态 → 本轮结束写入会话记忆。

---

## 三、技术选型与理由

| 选型 | 为什么这么选 |
| --- | --- |
| **LangGraph** `create_react_agent` | 相比手写 while 循环调 LLM，直接用图编排拿到成熟的工具调用循环 + 事件流；相比 LangChain 旧版 AgentExecutor，LangGraph 的事件粒度更细（能拿到 token 级、工具级事件），且便于后续接入持久化 checkpoint |
| **SSE 而非 WebSocket** | 本场景只需服务端单向推送（token 流 + 工具状态），SSE 基于 HTTP、无需额外协议协商与心跳维护，实现与部署成本都更低 |
| **Milvus** | 面向大规模向量的专用库，支持 HNSW / FLAT 多索引策略与元数据过滤，为后续「多知识库隔离、混合检索」留了扩展位 |
| **OpenAI 兼容协议** | LLM 与 Embedding 客户端统一走 `langchain-openai`，通过 `base_url` 切换服务商（OpenAI / DeepSeek / 硅基流动），并把两者拆成独立配置——因为部分厂商（如 DeepSeek）只提供对话模型不提供 embedding |
| **Vue3 + TS** | 组合式 API 适合流式状态管理；TS 为 SSE 事件定义联合类型，让前端事件分发具备类型收敛 |
| **fetch 手动解析 SSE** | `EventSource` 只支持 GET，无法携带 POST body，故用 fetch + ReadableStream 手写帧解析 |

---

## 四、核心实现解析

### 1. Agent 推理循环与流式事件协议

`backend/app/agent.py` 是整个项目的核心。通过 `astream_events(version="v2")` 消费 LangGraph 的运行事件，
把底层事件翻译成三种稳定的业务事件推送前端：

| 事件 | 触发时机 | 前端表现 |
| --- | --- | --- |
| `token` | LLM 每吐出一个增量 token | 逐字追加到气泡，形成打字机效果 |
| `tool_start` | Agent 决定调用某个工具 | 气泡上方出现工具调用状态条（含工具名与入参） |
| `tool_end` | 工具执行结束 | 状态条标记完成，此时 Agent 获得 observation 继续推理 |

事件协议采用标准 SSE 帧格式（`event: xxx\ndata: {json}\n\n`），
好处是既可以用浏览器消费，也可以直接用 `curl -N` 调试验证。

### 2. 工具即接口：docstring 决定路由准确率

三个工具（`backend/app/tools.py`）本质上只是三个带中文 docstring 的函数。
LLM 仅通过**函数名 + docstring** 判断该不该调用，因此描述里的适用场景说明是刻意设计的，
例如知识库检索工具明确写了「涉及已上传文档/资料/笔记内容的问题优先使用此工具」，
显著降低了工具误选率。这也是 Agent 工程与普通后端开发最大的思维差异之一。

### 3. RAG 知识入库管道

`backend/app/ingestion.py` 实现完整链路：**PDF/文本解析（pypdf）→ 递归字符切分
（chunk_size=500 / overlap=80）→ Embedding → 写入 Milvus**，同时在 SQLite 记录文档元数据。

设计要点：
- **overlap 的作用**：相邻切片保留重叠内容，避免关键句正好被切分点截断，导致两侧切片都检索不到
- **元数据随切片入库**：每个切片携带 `doc_id / filename / chunk_index`，检索结果可直接回溯来源文件名并支持按文档精准删除
- **懒加载连接**：Milvus 客户端用 `lru_cache` 单例 + 懒连接，未启动 Milvus 时后端仍可正常运行，仅该工具降级提示，不影响其他工具

### 4. 会话记忆管理

`backend/app/memory.py` 按 `session_id` 隔离多轮上下文，仅保留最近 20 条消息。
这是简单但必要的成本控制：Agent 每轮都会把完整历史塞回 prompt，不裁剪会导致 token 消耗随对话轮数线性增长。

---

## 五、实测效果

真实运行记录（模型：Qwen2.5-72B-Instruct，经 OpenAI 兼容接口调用）：

**输入**：这个月卖得最好的商品是什么？销量多少？

**Agent 行为**：自主选择 `query_structured_data` 工具，并生成了如下 SQL：

```sql
SELECT p.name, SUM(o.quantity) as total_sales
FROM products p JOIN orders o ON p.id = o.product_id
WHERE o.created_at >= date('now', 'start of month')
GROUP BY p.id ORDER BY total_sales DESC
```

**输出**：显示器支架 S1，销量为 3 件 —— 与数据库中实际数据一致。

该过程完整覆盖了「决策 → 生成工具入参 → 执行 → 观察结果 → 生成最终回答」的 ReAct 完整循环。

---

## 六、遇到的问题与解决

| 问题 | 定位过程 | 解决方案 |
| --- | --- | --- |
| 流式回答时前端气泡一直卡在加载态 | 先用 `curl -N` 直连后端确认 SSE 流正常，再经 Vite 代理复测仍正常，最终定位为前端问题：**直接修改数组内原始对象的属性绕过了 Vue3 的 Proxy 响应式**，赋值不触发依赖更新 | 用 `reactive()` 包装消息对象，使其后续属性修改可被追踪，界面恢复逐 token 渲染 |
| `EventSource` 无法发送 POST 请求 | 阅读 API 规范确认其仅支持 GET | 改用 fetch + ReadableStream 手动切分 `\n\n` 帧并解析 `event/data` 字段 |
| 依赖版本互相冲突导致导入报错 | 从 traceback 逐层回读，发现 langchain 与 langchain-core 大版本不匹配 | 锁定一套互相兼容的版本（langchain 0.3.27 / langgraph 0.2.76），并在独立虚拟环境中安装，避免与其他项目互相污染 |

---

## 七、后续规划（已设计未实现）

1. **召回质量量化**：接入 RAGAS 评估 faithfulness / answer relevancy，把 RAG 效果从"感觉还行"变成可度量指标
2. **混合检索**：Milvus 向量召回 + BM25 关键词召回融合，改善专有名词与精确匹配场景的召回率
3. **记忆持久化**：会话记忆从进程内存迁移至 Redis / 数据表，支持服务重启后继续对话
4. **可观测性**：落地 Agent 运行轨迹（每次工具调用链路与耗时），便于线上问题定位与效果分析

---

## 八、项目结构

```
backend/
├── app/
│   ├── main.py          FastAPI 入口：CORS、路由挂载、启动建表
│   ├── config.py        配置中心，全部从 .env 读取
│   ├── llm.py           LLM / Embedding 客户端（单例）
│   ├── agent.py         ★ ReAct Agent 与 SSE 事件流（核心）
│   ├── tools.py         ★ 三个工具：知识库检索 / 联网搜索 / SQL
│   ├── ingestion.py     ★ 知识入库管道
│   ├── vectorstore.py   Milvus 连接（懒加载单例）
│   ├── memory.py        会话记忆与历史裁剪
│   ├── db.py            SQLite：文档元数据 + 演示业务数据
│   └── routers/         chat.py（SSE 接口）、documents.py（文档管理）
frontend/
└── src/
    ├── api.ts           ★ fetch 手动解析 SSE 事件流
    ├── types.ts         SSE 事件的 TS 联合类型定义
    └── components/      ChatPanel / MessageItem / DocPanel
```

---

## 九、本地运行

```bash
# 1. 启动 Milvus（可选，仅知识库工具需要）
docker compose up -d

# 2. 后端
cd backend
cp .env.example .env      # 填入 OpenAI 兼容的 LLM API Key
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. 前端
cd frontend
npm install
npm run dev               # http://localhost:5173
```
