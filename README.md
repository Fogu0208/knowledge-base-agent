# 知识库 Agent 助手

一个可写进简历的多工具 Agent 项目：LLM 自主决定「检索知识库 / 联网搜索 / 查数据库」，
SSE 流式输出回答全过程，前端实时展示每一次工具调用。

> 更完整的设计思路、技术选型理由与实测记录见 [docs/PROJECT_INTRO.md](docs/PROJECT_INTRO.md)

## 架构

```
用户
 │
 Vue3 + TS 前端 ── 流式对话 UI / 知识库文档管理
 │
 FastAPI 后端 ── SSE 流式输出 / 会话管理
 │
 LangChain ReAct Agent ── 工具调用循环 / 会话记忆
 ├─ Milvus 检索（RAG，知识库问答）
 ├─ 联网搜索（实时信息）
 └─ SQL 查询（结构化数据，SQLite 演示库）

 后台入库管道：文档上传 → 解析切分 → Embedding → Milvus
```

## 技术栈

后端：Python 3.10+ / FastAPI / LangChain + LangGraph / Milvus / SQLite
前端：Vue 3 / TypeScript / Vite

## 快速开始

### 1. 启动 Milvus（需要 Docker）

```bash
docker compose up -d        # etcd + minio + milvus，约 1 分钟就绪
```

### 2. 配置并启动后端

```bash
cd backend
cp .env.example .env        # 填入你的 LLM API Key（支持 OpenAI / DeepSeek / 硅基流动等 OpenAI 兼容接口）
pip install -r requirements.txt
uvicorn app.main:app --reload
```

注意：embedding 模型和对话模型可以用不同服务商（.env 里分开配置），
DeepSeek 没有 embedding 接口，需要另配一家。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

### 4. 演示三个工具路由（面试演示脚本）

1. **SQL 工具**：问「这个月卖得最好的商品是什么」→ Agent 生成 SQL 查 orders 表
2. **联网搜索**：问「最近 AI Agent 有什么新进展」→ Agent 调 web_search
3. **RAG**：在「知识库」页上传一份 PDF/笔记 → 问文档里的细节 → Agent 检索 Milvus 并引用来源回答

## 项目结构

```
backend/app/
├── main.py          FastAPI 入口（CORS、路由挂载、启动建表）
├── config.py        全部配置，从 .env 读取
├── llm.py           LLM / Embedding 客户端（单例）
├── agent.py         ★ ReAct Agent + SSE 流式事件（核心）
├── tools.py         ★ 三个工具：知识库检索 / 联网搜索 / SQL
├── vectorstore.py   Milvus 连接（懒加载单例）
├── ingestion.py     ★ 知识入库管道：解析→切分→向量化→入库
├── memory.py        会话记忆（按 session_id 隔离 + 裁剪）
├── db.py            SQLite：文档元数据 + 演示业务数据
└── routers/         chat.py（SSE 接口）、documents.py（上传/列表/删除）

frontend/src/
├── App.vue          布局与 Tab 切换
├── api.ts           ★ fetch 手动解析 SSE 流（EventSource 不支持 POST）
├── types.ts         类型定义
└── components/
    ├── ChatPanel.vue    聊天面板（发送、流式渲染、工具状态）
    ├── MessageItem.vue  消息气泡 + 工具调用状态 chip
    └── DocPanel.vue     知识库管理（上传/删除文档）
```

## 建议的进阶路线（每条都是面试加分项）

1. **召回评估**：接入 RAGAS，对知识库问答做 faithfulness / answer relevancy 打分，量化 RAG 效果
2. **混合检索**：Milvus 向量检索 + SQLite 全文检索（BM25），加权融合
3. **记忆持久化**：会话记忆从内存换成 Redis / 表存储，支持跨重启
4. **流式优化**：工具入参也流式透传给前端（function calling 参数增量解析）
5. **可观测**：记录每次 Agent 运行的工具调用轨迹，做一个简单的 trace 页面

## 简历写法参考

> 基于 LangChain/LangGraph 构建多工具 ReAct Agent 应用：Agent 自主路由至
> Milvus 知识库检索（RAG）、联网搜索与 SQL 查询；FastAPI SSE 实现全链路流式输出，
> 前端（Vue3 + TS）实时渲染 token 与工具调用状态；自建文档入库管道
> （解析→递归切分→Embedding→Milvus），并设计会话级短期记忆与历史裁剪策略。

面试要点：能讲清 ReAct 循环一轮发生了什么（决策→工具→观察→再决策）、
为什么 SSE 用 fetch 而不是 EventSource、切分时 chunk_overlap 的作用、
工具 docstring 如何影响路由准确率。
