from datetime import date
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .database import get_db

main_bp = Blueprint("main", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Only admin users can access that page.", "error")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)

    return wrapped_view


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            flash(f"Welcome, {user['full_name']}.", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@main_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))


@main_bp.route("/")
@login_required
def dashboard():
    db = get_db()
    totals = {
        "students": db.execute("SELECT COUNT(*) AS total FROM students").fetchone()["total"],
        "classes": db.execute("SELECT COUNT(*) AS total FROM classes").fetchone()["total"],
        "records": db.execute("SELECT COUNT(*) AS total FROM attendance_records").fetchone()["total"],
    }
    recent_records = db.execute(
        """
        SELECT ar.id, ar.attendance_date, ar.status, s.full_name, c.name AS class_name
        FROM attendance_records ar
        JOIN students s ON s.id = ar.student_id
        JOIN classes c ON c.id = ar.class_id
        ORDER BY ar.attendance_date DESC, ar.id DESC
        LIMIT 10
        """
    ).fetchall()
    classes = db.execute("SELECT * FROM classes ORDER BY name").fetchall()
    return render_template(
        "dashboard.html",
        totals=totals,
        recent_records=recent_records,
        classes=classes,
        today=date.today().isoformat(),
    )


@main_bp.route("/students", methods=["GET", "POST"])
@login_required
@admin_required
def students():
    db = get_db()
    if request.method == "POST":
        student_number = request.form["student_number"].strip()
        full_name = request.form["full_name"].strip()
        grade_level = request.form["grade_level"].strip()

        if not student_number or not full_name or not grade_level:
            flash("All student fields are required.", "error")
        else:
            try:
                db.execute(
                    """
                    INSERT INTO students (student_number, full_name, grade_level)
                    VALUES (?, ?, ?)
                    """,
                    (student_number, full_name, grade_level),
                )
                db.commit()
                flash("Student added successfully.", "success")
                return redirect(url_for("main.students"))
            except Exception:
                flash("Student number must be unique.", "error")

    student_rows = db.execute(
        "SELECT * FROM students ORDER BY full_name"
    ).fetchall()
    return render_template("students.html", students=student_rows)


@main_bp.route("/classes", methods=["GET", "POST"])
@login_required
@admin_required
def classes():
    db = get_db()
    if request.method == "POST":
        name = request.form["name"].strip()
        section = request.form["section"].strip()
        schedule = request.form["schedule"].strip()

        if not name or not section or not schedule:
            flash("All class fields are required.", "error")
        else:
            db.execute(
                "INSERT INTO classes (name, section, schedule) VALUES (?, ?, ?)",
                (name, section, schedule),
            )
            db.commit()
            flash("Class added successfully.", "success")
            return redirect(url_for("main.classes"))

    class_rows = db.execute("SELECT * FROM classes ORDER BY name").fetchall()
    students = db.execute("SELECT * FROM students ORDER BY full_name").fetchall()
    return render_template("classes.html", classes=class_rows, students=students)


@main_bp.route("/enroll", methods=["POST"])
@login_required
@admin_required
def enroll():
    db = get_db()
    student_id = request.form["student_id"]
    class_id = request.form["class_id"]

    try:
        db.execute(
            "INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)",
            (student_id, class_id),
        )
        db.commit()
        flash("Student enrolled successfully.", "success")
    except Exception:
        flash("That student is already enrolled in the selected class.", "error")
    return redirect(url_for("main.classes"))


@main_bp.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    db = get_db()
    selected_class_id = request.args.get("class_id", type=int)
    if request.method == "POST":
        selected_class_id = int(request.form["class_id"])
        attendance_date = request.form["attendance_date"]

        enrolled_students = db.execute(
            """
            SELECT s.id, s.full_name
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            WHERE e.class_id = ?
            ORDER BY s.full_name
            """,
            (selected_class_id,),
        ).fetchall()

        for student in enrolled_students:
            status = request.form.get(f"status_{student['id']}", "Present")
            remarks = request.form.get(f"remarks_{student['id']}", "").strip()
            db.execute(
                """
                INSERT INTO attendance_records (student_id, class_id, attendance_date, status, remarks)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_id, class_id, attendance_date)
                DO UPDATE SET status = excluded.status, remarks = excluded.remarks
                """,
                (student["id"], selected_class_id, attendance_date, status, remarks),
            )

        db.commit()
        flash("Attendance saved successfully.", "success")
        return redirect(url_for("main.attendance", class_id=selected_class_id))

    classes = db.execute("SELECT * FROM classes ORDER BY name").fetchall()
    enrolled_students = []
    if selected_class_id:
        enrolled_students = db.execute(
            """
            SELECT s.id, s.student_number, s.full_name, s.grade_level
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            WHERE e.class_id = ?
            ORDER BY s.full_name
            """,
            (selected_class_id,),
        ).fetchall()

    attendance_summary = db.execute(
        """
        SELECT c.name AS class_name, ar.attendance_date, ar.status, COUNT(*) AS total
        FROM attendance_records ar
        JOIN classes c ON c.id = ar.class_id
        GROUP BY c.name, ar.attendance_date, ar.status
        ORDER BY ar.attendance_date DESC, c.name
        LIMIT 15
        """
    ).fetchall()
    return render_template(
        "attendance.html",
        classes=classes,
        enrolled_students=enrolled_students,
        selected_class_id=selected_class_id,
        today=date.today().isoformat(),
        attendance_summary=attendance_summary,
    )
