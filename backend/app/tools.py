"""Agent 可调用的三个工具。

每个工具就是一个带 docstring 的普通函数——
LLM 只能看到函数名 + docstring + 参数 schema，
所以 docstring 写得越清楚，Agent 的工具选择就越准。
"""
import json
import sqlite3

from langchain_core.tools import tool

from app.config import settings


@tool
def knowledge_base_search(query: str) -> str:
    """在用户上传的文档知识库中检索与问题相关的原文片段。
    当问题可能涉及已上传的文档、资料、笔记、产品手册等内容时优先使用本工具。"""
    try:
        from app.vectorstore import get_vectorstore  # 懒加载，避免启动时连 Milvus

        docs = get_vectorstore().similarity_search(query, k=4)
    except Exception as e:  # Milvus 没启动 / 网络问题，都告诉 Agent 而不是直接崩
        return f"知识库检索失败（{e}）。请改用 web_search 或基于已知信息回答。"

    if not docs:
        return "知识库中没有找到相关内容，请尝试用 web_search 补充。"

    parts = []
    for i, d in enumerate(docs, 1):
        source = d.metadata.get("filename", "未知来源")
        parts.append(f"[片段{i} | 来源: {source}]\n{d.page_content}")
    return "\n\n".join(parts)


@tool
def web_search(query: str) -> str:
    """联网搜索实时信息。当问题涉及最新动态、实时数据，或知识库中没有相关内容时使用。"""
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
    except Exception as e:
        return f"联网搜索失败：{e}"

    if not results:
        return "没有搜到结果。"
    return "\n\n".join(
        f"[{r.get('title', '')}]\n{r.get('body', '')}" for r in results
    )


@tool
def query_structured_data(sql: str) -> str:
    """查询示例业务数据库（SQLite，只读）。库中有两张表：
    products(id, name, category, price, stock) 商品表；
    orders(id, product_id, quantity, amount, created_at) 订单表。
    只允许 SELECT 语句。"""
    if not sql.strip().lower().startswith("select"):
        return "只允许 SELECT 查询。"
    conn = sqlite3.connect(settings.APP_DB_PATH)
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return json.dumps([cols] + [list(r) for r in rows], ensure_ascii=False)[:2000]
    except Exception as e:
        return f"SQL 执行失败：{e}"
    finally:
        conn.close()


TOOLS = [knowledge_base_search, web_search, query_structured_data]
