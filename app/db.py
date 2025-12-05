import duckdb
import json

DB_PATH = "finsolve.db"

def get_conn():
    return duckdb.connect(DB_PATH, read_only=False)

def init_db():
    con = get_conn()

    # --- Document Chunks ---
    con.execute("""
        CREATE TABLE IF NOT EXISTS doc_chunks (
            chunk_id TEXT PRIMARY KEY,
            file_name TEXT,
            role TEXT,
            department TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Chat Logs ---
    # IMPORTANT: DuckDB will auto-generate the rowid if you don't specify id
    con.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER,      -- will be filled automatically by rowid if left NULL
            username TEXT,
            role TEXT,
            query TEXT,
            doc_chunk_ids TEXT,
            answer_preview TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.close()


def log_doc_chunk(chunk_id, file_name, role, department, source):
    con = get_conn()
    con.execute("""
        INSERT OR REPLACE INTO doc_chunks
        (chunk_id, file_name, role, department, source)
        VALUES (?, ?, ?, ?, ?)
    """, (chunk_id, file_name, role, department, source))
    con.close()


def log_chat(username, role, query, chunk_ids, answer_text):
    con = get_conn()

    # Insert NULL into id → DuckDB assigns automatic internal rowid
    con.execute("""
        INSERT INTO chat_logs (id, username, role, query, doc_chunk_ids, answer_preview)
        VALUES (NULL, ?, ?, ?, ?, ?)
    """, (
        username,
        role,
        query,
        json.dumps(chunk_ids),
        answer_text[:200] if answer_text else ""
    ))
    con.close()
