from flask import Flask, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart-attendance"

def db():
    return sqlite3.connect("attendance.db")

def setup():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll TEXT UNIQUE,
            phone TEXT,
            course TEXT,
            semester TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT,
            date TEXT,
            time TEXT
        )
    """)
    con.commit()
    con.close()

@app.route("/")
def home():
    return """
    <h1>Smart Attendance System</h1>
    <a href="/register">Register Student</a><br><br>
    <a href="/login">Student Login</a><br><br>
    <a href="/admin">Admin</a>
    """

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        phone = request.form["phone"]
        course = request.form["course"]
        semester = request.form["semester"]

        con = db()

        try:
            con.execute(
                "INSERT INTO students (name, roll, phone, course, semester) VALUES (?, ?, ?, ?, ?)",
                (name, roll, phone, course, semester)
            )
            con.commit()
            message = "Student registered successfully"
        except sqlite3.IntegrityError:
            message = "Roll number already exists"

        con.close()

        return f"""
        <h2>{message}</h2>
        <a href="/">Home</a>
        """

    return """
    <h2>Student Registration</h2>

    <form method="POST">
        Name:<br>
        <input name="name" required><br><br>

        Roll Number:<br>
        <input name="roll" required><br><br>

        Phone:<br>
        <input name="phone" required><br><br>

        Course:<br>
        <input name="course" required><br><br>

        Semester:<br>
        <input name="semester" required><br><br>

        <button type="submit">Register</button>
    </form>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        roll = request.form["roll"]

        con = db()
        student = con.execute(
            "SELECT * FROM students WHERE roll = ?",
            (roll,)
        ).fetchone()
        con.close()

        if student:
            session["roll"] = roll
            return redirect("/dashboard")

        return """
        <h3>Student not found</h3>
        <a href="/login">Try Again</a>
        """

    return """
    <h2>Student Login</h2>

    <form method="POST">
        Roll Number:<br>
        <input name="roll" required><br><br>

        <button type="submit">Login</button>
    </form>
    """

@app.route("/dashboard")
def dashboard():
    if "roll" not in session:
        return redirect("/login")

    roll = session["roll"]

    con = db()
    student = con.execute(
        "SELECT * FROM students WHERE roll = ?",
        (roll,)
    ).fetchone()

    records = con.execute(
        "SELECT date, time FROM attendance WHERE roll = ? ORDER BY date DESC",
        (roll,)
    ).fetchall()

    con.close()

    attendance = ""

    for record in records:
        attendance += f"<tr><td>{record[0]}</td><td>{record[1]}</td><td>Present</td></tr>"

    if not attendance:
        attendance = "<tr><td colspan='3'>No attendance records</td></tr>"

    return f"""
    <h1>Student Dashboard</h1>

    <p>Name: {student[1]}</p>
    <p>Roll Number: {student[2]}</p>
    <p>Phone: {student[3]}</p>
    <p>Course: {student[4]}</p>
    <p>Semester: {student[5]}</p>

    <br>

    <a href="/mark-attendance">
        <button>Mark Attendance</button>
    </a>

    <h2>Attendance History</h2>

    <table border="1" cellpadding="10">
        <tr>
            <th>Date</th>
            <th>Time</th>
            <th>Status</th>
        </tr>
        {attendance}
    </table>

    <br>
    <a href="/logout">Logout</a>
    """

@app.route("/mark-attendance")
def mark_attendance():
    if "roll" not in session:
        return redirect("/login")

    roll = session["roll"]
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")

    con = db()

    existing = con.execute(
        "SELECT * FROM attendance WHERE roll = ? AND date = ?",
        (roll, date)
    ).fetchone()

    if existing:
        message = "Attendance already marked today"
    else:
        con.execute(
            "INSERT INTO attendance (roll, date, time) VALUES (?, ?, ?)",
            (roll, date, time)
        )
        con.commit()
        message = "Attendance marked successfully"

    con.close()

    return f"""
    <h2>{message}</h2>
    <a href="/dashboard">Back to Dashboard</a>
    """

@app.route("/admin")
def admin():
    con = db()

    students = con.execute("""
        SELECT students.name, students.roll, students.course,
        COUNT(attendance.id)
        FROM students
        LEFT JOIN attendance
        ON students.roll = attendance.roll
        GROUP BY students.roll
    """).fetchall()

    con.close()

    rows = ""

    for student in students:
        rows += f"""
        <tr>
            <td>{student[0]}</td>
            <td>{student[1]}</td>
            <td>{student[2]}</td>
            <td>{student[3]}</td>
        </tr>
        """

    return f"""
    <h1>Admin Dashboard</h1>

    <table border="1" cellpadding="10">
        <tr>
            <th>Name</th>
            <th>Roll Number</th>
            <th>Course</th>
            <th>Attendance Count</th>
        </tr>
        {rows}
    </table>

    <br>
    <a href="/">Home</a>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    setup()
    app.run(debug=True)