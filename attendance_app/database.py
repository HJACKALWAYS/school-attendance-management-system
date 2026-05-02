import sqlite3
from pathlib import Path

from flask import Flask, current_app, g
from werkzeug.security import generate_password_hash


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
    user_count = db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    if not user_count:
        db.executemany(
            """
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    "System Administrator",
                    "admin",
                    generate_password_hash("admin123"),
                    "admin",
                ),
                (
                    "Faculty Teacher",
                    "teacher",
                    generate_password_hash("teacher123"),
                    "teacher",
                ),
            ],
        )

    class_count = db.execute("SELECT COUNT(*) AS total FROM classes").fetchone()["total"]
    if class_count:
        return

    sample_classes = [
        ("Grade 7 Mathematics", "A", "Mon/Wed/Fri 8:00 AM"),
        ("Grade 7 English", "A", "Tue/Thu 10:00 AM"),
        ("Grade 8 Science", "B", "Tue/Thu 9:30 AM"),
        ("Grade 8 Filipino", "B", "Mon/Wed 1:00 PM"),
        ("Grade 9 History", "C", "Mon/Wed/Fri 11:00 AM"),
        ("Grade 10 ICT", "A", "Tue/Thu 2:00 PM"),
    ]
    db.executemany(
        "INSERT INTO classes (name, section, schedule) VALUES (?, ?, ?)",
        sample_classes,
    )

    sample_students = [
        ("2026-001", "Maria Santos", "Grade 7"),
        ("2026-002", "John Cruz", "Grade 7"),
        ("2026-003", "Anne Reyes", "Grade 8"),
        ("2026-004", "Paolo Garcia", "Grade 7"),
        ("2026-005", "Sofia Mendoza", "Grade 7"),
        ("2026-006", "Miguel Torres", "Grade 8"),
        ("2026-007", "Jasmine Flores", "Grade 8"),
        ("2026-008", "Carlo Dela Cruz", "Grade 8"),
        ("2026-009", "Bianca Ramos", "Grade 9"),
        ("2026-010", "Nathan Villanueva", "Grade 9"),
        ("2026-011", "Erika Bautista", "Grade 9"),
        ("2026-012", "Lance Navarro", "Grade 10"),
        ("2026-013", "Andrea Lim", "Grade 10"),
        ("2026-014", "Joshua Aquino", "Grade 10"),
        ("2026-015", "Trisha Gutierrez", "Grade 10"),
    ]
    db.executemany(
        "INSERT INTO students (student_number, full_name, grade_level) VALUES (?, ?, ?)",
        sample_students,
    )

    class_rows = db.execute("SELECT id, name FROM classes").fetchall()
    student_rows = db.execute("SELECT id, grade_level FROM students").fetchall()
    class_ids_by_grade = {
        "Grade 7": [row["id"] for row in class_rows if row["name"].startswith("Grade 7")],
        "Grade 8": [row["id"] for row in class_rows if row["name"].startswith("Grade 8")],
        "Grade 9": [row["id"] for row in class_rows if row["name"].startswith("Grade 9")],
        "Grade 10": [row["id"] for row in class_rows if row["name"].startswith("Grade 10")],
    }
    enrollments = []
    for student in student_rows:
        for class_id in class_ids_by_grade.get(student["grade_level"], []):
            enrollments.append((student["id"], class_id))

    db.executemany(
        "INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)",
        enrollments,
    )


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'teacher')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
