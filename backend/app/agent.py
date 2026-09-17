"""Agent 核心：langgraph 的 create_react_agent + SSE 流式事件。

一次提问在服务端发生的完整链路：
1. 取出该 session 的历史消息，拼上本轮用户输入
2. ReAct 循环：LLM 决定是调工具还是直接回答
   - 调工具 → on_tool_start / on_tool_end 事件 → 前端显示"正在检索…"
   - 直接回答 → on_chat_model_stream 事件 → 前端逐 token 渲染
3. 全部结束后把最终消息列表写回会话记忆
"""
import json
from typing import AsyncGenerator

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from app.llm import get_llm
from app.memory import load_history, save_messages
from app.tools import TOOLS

SYSTEM_PROMPT = """你是一个知识库 Agent 助手，可以自主决定如何回答用户的问题。

可用工具：
- knowledge_base_search：检索用户上传的文档知识库
- web_search：联网搜索实时信息
- query_structured_data：查询业务数据库（商品 / 订单）

决策原则：
1. 问题涉及已上传文档或私有资料 → 优先检索知识库
2. 问题涉及最新动态、实时数据 → 联网搜索
3. 问题涉及商品、订单、销量等数据 → 查数据库
4. 引用知识库片段时注明来源文件名；工具失败时不要编造，说明失败原因
回答用简洁的中文。"""


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


_agent = None


def get_agent():
    """Agent 实例全局单例（无状态，会话状态由 memory 模块管理）。"""
    global _agent
    if _agent is None:
        _agent = create_react_agent(get_llm(), TOOLS, prompt=SYSTEM_PROMPT)
    return _agent


async def stream_answer(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    history: list[AnyMessage] = load_history(session_id)
    inputs = {"messages": history + [HumanMessage(content=user_message)]}
    final_messages: list[AnyMessage] = []

    try:
        agent = get_agent()
        async for event in agent.astream_events(inputs, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                # LLM 正在生成 token
                token = event["data"]["chunk"].content
                if token:
                    yield _sse("token", {"content": token})

            elif kind == "on_tool_start":
                yield _sse("tool_start", {
                    "name": event["name"],
                    "input": str(event["data"].get("input", ""))[:200],
                })

            elif kind == "on_tool_end":
                yield _sse("tool_end", {"name": event["name"]})

            elif kind == "on_chain_end" and event.get("name") in ("LangGraph", "agent", "tools"):
                # 每个节点结束时都会带最新 messages，最后一次的就是完整结果
                output = event["data"].get("output")
                if isinstance(output, dict) and "messages" in output:
                    final_messages = output["messages"]

        if final_messages:
            save_messages(session_id, final_messages)
        yield _sse("done", {})

    except Exception as e:
        yield _sse("error", {"message": str(e)})
