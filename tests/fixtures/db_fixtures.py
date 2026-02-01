import sqlite3
from typing import Iterable, Tuple


def exec_sql(db_path: str, statements: Iterable[Tuple[str, tuple]]) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for sql, params in statements:
        cursor.execute(sql, params)
    conn.commit()
    conn.close()


def fetch_one(db_path: str, sql: str, params: tuple = ()) -> tuple:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    row = cursor.fetchone()
    conn.close()
    return row


def fetch_all(db_path: str, sql: str, params: tuple = ()) -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows
