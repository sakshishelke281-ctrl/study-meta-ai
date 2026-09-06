from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash
from ai_helper import get_syllabus_answer, get_exam_notes

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "study-meta-ai-secret")


# ==============================
# DATABASE CONNECTION
# ==============================

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host="localhost",
        database="study meta ai",
        user="postgres",
        password=os.getenv("DB_PASSWORD", "55555"),
        port="5432"
    )

# ==============================
# HOME
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        course = request.form["course"]
        semester = request.form["semester"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO student
            (name, email, password, course, semester)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            name,
            email,
            hashed_password,
            course,
            semester
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT student_id, name, password
            FROM student
            WHERE email = %s
        """, (email,))

        student = cur.fetchone()

        cur.close()
        conn.close()

        if student and check_password_hash(student[2], password):

            session["student_id"] = student[0]
            session["student_name"] = student[1]

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")


# ==============================
# SUBJECTS & TOPICS
# ==============================

@app.route("/subjects")
def subjects():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.subject_name, t.topic_name
        FROM subject s
        LEFT JOIN topic t
        ON s.subject_id = t.subject_id
        ORDER BY s.subject_id, t.topic_id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    subjects_data = {}

    for subject_name, topic_name in rows:

        if subject_name not in subjects_data:
            subjects_data[subject_name] = []

        if topic_name:
            subjects_data[subject_name].append(topic_name)

    return render_template(
        "subjects.html",
        subjects=subjects_data
    )


# ==============================
# DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["student_name"]
    )


# ==============================
# ASK AI
# ==============================

@app.route("/ask", methods=["GET", "POST"])
def ask():

    if "student_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        question = request.form["question"]

        student_id = session["student_id"]

        # Generate AI answer
        answer = get_syllabus_answer(question)

        conn = get_db_connection()
        cur = conn.cursor()

        # Save question
        cur.execute("""
            INSERT INTO query
            (student_id, question)
            VALUES (%s, %s)
            RETURNING query_id
        """, (
            student_id,
            question
        ))

        query_id = cur.fetchone()[0]

        # Save AI answer
        cur.execute("""
            INSERT INTO answers
            (query_id, answer)
            VALUES (%s, %s)
            RETURNING answer_id
        """, (
            query_id,
            answer
        ))

        answer_id = cur.fetchone()[0]

        conn.commit()

        cur.close()
        conn.close()

        return render_template(
            "answer.html",
            question=question,
            answer=answer,
            answer_id=answer_id
        )

    return render_template("ask.html")


# ==============================
# FEEDBACK
# ==============================

@app.route("/feedback", methods=["POST"])
def feedback():

    if "student_id" not in session:
        return redirect(url_for("login"))

    rating = request.form["rating"]
    comment = request.form["comment"]
    answer_id = request.form["answer_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO feedback
        (answer_id, rating, comment)
        VALUES (%s, %s, %s)
    """, (
        answer_id,
        rating,
        comment
    ))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("dashboard"))


# ==============================
# HISTORY
# ==============================

@app.route("/history")
def history():

    if "student_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT q.question, a.answer, q.created_at
        FROM query q
        LEFT JOIN answers a
        ON q.query_id = a.query_id
        WHERE q.student_id = %s
        ORDER BY q.created_at DESC
    """, (
        session["student_id"],
    ))

    history_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "history.html",
        history=history_data
    )


# ==============================
# AI NOTES / SUMMARY
# ==============================

@app.route("/notes", methods=["GET", "POST"])
def notes():

    if "student_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        topic = request.form["topic"]
        subject = request.form["subject"]

        notes_content = get_exam_notes(topic, subject)

        return render_template(
            "notes.html",
            topic=topic,
            subject=subject,
            notes=notes_content
        )

    return render_template("notes.html")


# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app.run(debug=True)