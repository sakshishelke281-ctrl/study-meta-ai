from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash
from ai_helper import get_syllabus_answer, get_exam_notes


app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "study-meta-ai-secret"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

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


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    conn = get_db_connection()
    cur = conn.cursor()

    # -------------------------
    # STUDENT TABLE
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS student (
            student_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            course VARCHAR(100),
            semester VARCHAR(20)
        );
    """)

    # -------------------------
    # SUBJECT TABLE
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subject (
            subject_id SERIAL PRIMARY KEY,
            subject_name VARCHAR(100) NOT NULL
        );
    """)

    # -------------------------
    # TOPIC TABLE
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS topic (
            topic_id SERIAL PRIMARY KEY,
            subject_id INT REFERENCES subject(subject_id),
            topic_name VARCHAR(150) NOT NULL
        );
    """)

    # -------------------------
    # QUERY TABLE
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS query (
            query_id SERIAL PRIMARY KEY,
            student_id INT REFERENCES student(student_id),
            topic_id INT REFERENCES topic(topic_id),
            question TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -------------------------
    # ANSWERS TABLE
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            answer_id SERIAL PRIMARY KEY,
            query_id INT REFERENCES query(query_id),
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -------------------------
    # FEEDBACK TABLE
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id SERIAL PRIMARY KEY,
            answer_id INT REFERENCES answers(answer_id),
            rating INT,
            comment TEXT
        );
    """)

    # =====================================================
    # SUBJECTS
    # =====================================================

    subjects = [
        "DBMS",
        "Data Structures",
        "Software Engineering",
        "Java"
    ]

    for subject_name in subjects:

        cur.execute("""
            INSERT INTO subject (subject_name)
            SELECT %s
            WHERE NOT EXISTS (
                SELECT 1
                FROM subject
                WHERE subject_name = %s
            )
        """, (
            subject_name,
            subject_name
        ))

    # =====================================================
    # TOPICS
    # =====================================================

    topics = {

        "DBMS": [
            "Database Basics",
            "ER Model",
            "SQL",
            "Normalization",
            "Transactions"
        ],

        "Data Structures": [
            "Arrays",
            "Linked List",
            "Stack and Queue",
            "Trees",
            "Graphs"
        ],

        "Software Engineering": [
            "SDLC",
            "Agile Model",
            "Waterfall Model",
            "Software Testing",
            "Software Maintenance"
        ],

        "Java": [
            "OOP",
            "Classes and Objects",
            "Inheritance",
            "Exception Handling",
            "Collections"
        ]
    }

    for subject_name, topic_list in topics.items():

        cur.execute(
            """
            SELECT subject_id
            FROM subject
            WHERE subject_name = %s
            """,
            (subject_name,)
        )

        subject = cur.fetchone()

        if subject:

            subject_id = subject[0]

            for topic_name in topic_list:

                cur.execute("""
                    INSERT INTO topic
                    (subject_id, topic_name)

                    SELECT %s, %s

                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM topic
                        WHERE subject_id = %s
                        AND topic_name = %s
                    )
                """, (
                    subject_id,
                    topic_name,
                    subject_id,
                    topic_name
                ))

    conn.commit()

    cur.close()
    conn.close()


# =========================================================
# INITIALIZE DATABASE ON STARTUP
# =========================================================

try:
    init_database()

except Exception as e:
    print("Database initialization skipped:", e)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

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
            (
                name,
                email,
                password,
                course,
                semester
            )

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


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                student_id,
                name,
                password

            FROM student

            WHERE email = %s
        """, (email,))

        student = cur.fetchone()

        cur.close()
        conn.close()

        if student and check_password_hash(
            student[2],
            password
        ):

            session["student_id"] = student[0]
            session["student_name"] = student[1]

            return redirect(
                url_for("dashboard")
            )

        return "Invalid email or password"

    return render_template("login.html")


# =========================================================
# SUBJECTS & TOPICS
# =========================================================

@app.route("/subjects")
def subjects():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            s.subject_name,
            t.topic_name

        FROM subject s

        LEFT JOIN topic t
        ON s.subject_id = t.subject_id

        ORDER BY
            s.subject_id,
            t.topic_id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    subjects_data = {}

    for subject_name, topic_name in rows:

        if subject_name not in subjects_data:

            subjects_data[subject_name] = []

        if topic_name:

            subjects_data[subject_name].append(
                topic_name
            )

    return render_template(
        "subjects.html",
        subjects=subjects_data
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html",
        name=session["student_name"]
    )


# =========================================================
# ASK AI
# =========================================================

@app.route("/ask", methods=["GET", "POST"])
def ask():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        question = request.form["question"]

        student_id = session["student_id"]

        # Generate AI Answer
        answer = get_syllabus_answer(
            question
        )

        conn = get_db_connection()
        cur = conn.cursor()

        # -------------------------
        # SAVE QUESTION
        # -------------------------

        cur.execute("""
            INSERT INTO query
            (
                student_id,
                question
            )

            VALUES (%s, %s)

            RETURNING query_id
        """, (
            student_id,
            question
        ))

        query_id = cur.fetchone()[0]

        # -------------------------
        # SAVE ANSWER
        # -------------------------

        cur.execute("""
            INSERT INTO answers
            (
                query_id,
                answer
            )

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


# =========================================================
# FEEDBACK
# =========================================================

@app.route("/feedback", methods=["POST"])
def feedback():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    rating = request.form["rating"]
    comment = request.form["comment"]
    answer_id = request.form["answer_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO feedback
        (
            answer_id,
            rating,
            comment
        )

        VALUES (%s, %s, %s)
    """, (
        answer_id,
        rating,
        comment
    ))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            q.question,
            a.answer,
            q.created_at

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


# =========================================================
# AI NOTES / SUMMARY
# =========================================================

@app.route("/notes", methods=["GET", "POST"])
def notes():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        topic = request.form["topic"]
        subject = request.form["subject"]

        notes_content = get_exam_notes(
            topic,
            subject
        )

        return render_template(
            "notes.html",
            topic=topic,
            subject=subject,
            notes=notes_content
        )

    return render_template("notes.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )