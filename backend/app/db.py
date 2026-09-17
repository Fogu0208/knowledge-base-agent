"""本地 SQLite：文档元数据 + 演示用业务数据（给 SQL 工具喂的样例）。"""
import sqlite3

from app.config import settings


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.APP_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """create table if not exists documents (
                doc_id     text primary key,
                filename   text not null,
                chunks     integer not null,
                created_at text default (datetime('now', 'localtime'))
            )"""
        )
        # 演示业务表：让 SQL 查询工具有真实数据可查
        conn.executescript(
            """
            create table if not exists products (
                id integer primary key, name text, category text,
                price real, stock integer
            );
            create table if not exists orders (
                id integer primary key, product_id integer,
                quantity integer, amount real, created_at text
            );
            """
        )
        if conn.execute("select count(*) from products").fetchone()[0] == 0:
            conn.executemany(
                "insert into products(name, category, price, stock) values (?,?,?,?)",
                [
                    ("机械键盘 K87", "数码外设", 399.0, 120),
                    ("无线鼠标 M3", "数码外设", 129.0, 300),
                    ("降噪耳机 E7", "音频设备", 999.0, 50),
                    ("显示器支架 S1", "桌面配件", 199.0, 80),
                ],
            )
            conn.executemany(
                "insert into orders(product_id, quantity, amount, created_at) values (?,?,?,?)",
                [
                    (1, 2, 798.0, "2026-09-01 10:15"),
                    (2, 1, 129.0, "2026-09-03 14:20"),
                    (3, 1, 999.0, "2026-09-05 09:30"),
                    (1, 1, 399.0, "2026-09-08 21:05"),
                    (4, 3, 597.0, "2026-09-12 16:40"),
                    (2, 2, 258.0, "2026-09-15 11:00"),
                ],
            )


def list_documents() -> list:
    with _conn() as conn:
        rows = conn.execute(
            "select doc_id, filename, chunks, created_at from documents order by created_at desc"
        ).fetchall()
    return [dict(r) for r in rows]


def insert_document(doc_id: str, filename: str, chunks: int) -> None:
    with _conn() as conn:
        conn.execute(
            "insert into documents(doc_id, filename, chunks) values (?,?,?)",
            (doc_id, filename, chunks),
        )


def delete_document(doc_id: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("delete from documents where doc_id = ?", (doc_id,))
    return cur.rowcount > 0
