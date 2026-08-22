import datetime
import sqlite3

from app.config import load_config

class OptimisticLockError(Exception):
    pass


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    "Index" INTEGER PRIMARY KEY AUTOINCREMENT,
    TaskID TEXT,
    TaskName TEXT NOT NULL,
    TaskDescription TEXT,
    Activity TEXT,
    ProjectName TEXT,
    USERID TEXT,
    Status TEXT,
    StartDate TEXT,
    FinishedDate TEXT,
    Estimation REAL,
    Actual REAL,
    CreatedDate TEXT,
    ModifiedDate TEXT,
    RecordStatus TEXT NOT NULL DEFAULT 'Active'
)
"""


def get_connection():
    config = load_config()
    conn = sqlite3.connect(config["db_path"])
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn):
    conn.execute(SCHEMA_SQL)
    conn.commit()


def init_db():
    conn = get_connection()
    create_schema(conn)
    return conn


def create_task(conn, data):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        """
        INSERT INTO tasks (
            TaskID, TaskName, TaskDescription, Activity, ProjectName, USERID, Status,
            StartDate, FinishedDate, Estimation, Actual, CreatedDate, ModifiedDate, RecordStatus
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["TaskID"],
            data["TaskName"],
            data["TaskDescription"],
            data["Activity"],
            data["ProjectName"],
            data["USERID"],
            data["Status"],
            data["StartDate"],
            data["FinishedDate"],
            data["Estimation"],
            data["Actual"],
            now,
            now,
            "Active",
        ),
    )
    conn.commit()
    return cursor.lastrowid


def update_task(conn, index, loaded_modified_date, data):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        """
        UPDATE tasks SET
            TaskID=?, TaskName=?, TaskDescription=?, Activity=?, ProjectName=?, USERID=?, Status=?,
            StartDate=?, FinishedDate=?, Estimation=?, Actual=?, ModifiedDate=?
        WHERE "Index"=? AND ModifiedDate=?
        """,
        (
            data["TaskID"],
            data["TaskName"],
            data["TaskDescription"],
            data["Activity"],
            data["ProjectName"],
            data["USERID"],
            data["Status"],
            data["StartDate"],
            data["FinishedDate"],
            data["Estimation"],
            data["Actual"],
            now,
            index,
            loaded_modified_date,
        ),
    )
    conn.commit()

    if cursor.rowcount == 0:
        raise OptimisticLockError(
            f"Task {index} was modified since it was loaded (or no longer exists). Reload and try again."
        )

    return now


def get_task(conn, index):
    return conn.execute('SELECT * FROM tasks WHERE "Index"=?', (index,)).fetchone()


def soft_delete_task(conn, index):
    cursor = conn.execute('UPDATE tasks SET RecordStatus=? WHERE "Index"=?', ("Deleted", index))
    conn.commit()
    return cursor.rowcount > 0


def search_tasks(conn, task_id="", userid="", task_name="", include_deleted=False):
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if not include_deleted:
        query += " AND RecordStatus != 'Deleted'"

    if task_id:
        query += " AND TaskID LIKE ?"
        params.append(f"%{task_id}%")

    if userid:
        query += " AND USERID LIKE ?"
        params.append(f"%{userid}%")

    if task_name:
        query += " AND TaskName LIKE ?"
        params.append(f"%{task_name}%")

    query += ' ORDER BY "Index" DESC'

    return conn.execute(query, params).fetchall()
