import sqlite3
from pathlib import Path

from flask import Flask, current_app, g


def get_db():
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE"]).resolve()
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app: Flask):
    def _connect_db():
        db_path = Path(app.config["DATABASE"]).resolve()
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize():
        db = _connect_db()
        db.executescript(SCHEMA_SQL)
        _seed_data(db)
        db.commit()
        db.close()

    app.teardown_appcontext(close_db)

    with app.app_context():
        _initialize()


def _seed_data(db):
    class_count = db.execute("SELECT COUNT(*) AS total FROM classes").fetchone()["total"]
    if class_count:
        return

    db.executemany(
        "INSERT INTO classes (name, section, schedule) VALUES (?, ?, ?)",
        [
            ("Grade 7 Mathematics", "A", "Mon/Wed/Fri 8:00 AM"),
            ("Grade 8 Science", "B", "Tue/Thu 9:30 AM"),
        ],
    )

    db.executemany(
        "INSERT INTO students (student_number, full_name, grade_level) VALUES (?, ?, ?)",
        [
            ("2026-001", "Maria Santos", "Grade 7"),
            ("2026-002", "John Cruz", "Grade 7"),
            ("2026-003", "Anne Reyes", "Grade 8"),
        ],
    )

    enrollments = [
        (1, 1),
        (2, 1),
        (3, 2),
    ]
    db.executemany(
        "INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)",
        enrollments,
    )


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    grade_level TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    section TEXT NOT NULL,
    schedule TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    UNIQUE(student_id, class_id),
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(class_id) REFERENCES classes(id)
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Late', 'Absent')),
    remarks TEXT,
    UNIQUE(student_id, class_id, attendance_date),
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(class_id) REFERENCES classes(id)
);
"""
