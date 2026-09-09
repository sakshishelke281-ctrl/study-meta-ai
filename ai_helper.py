import requests
import os


# =========================================================
# OLLAMA CONFIGURATION
# =========================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

MODEL_NAME = "phi"


# =========================================================
# GENERATE SYLLABUS ANSWER
# =========================================================

def get_syllabus_answer(question, topic_name=None, subject_name=None):
    """
    Generate simple, exam-focused answer for students.
    """

    context = ""

    if topic_name and subject_name:
        context = f" for the topic '{topic_name}' in {subject_name}"

    prompt = f"""
You are StudyMeta AI, an exam-oriented academic assistant for students.

QUESTION:
{question}{context}

INSTRUCTIONS:
1. Give the answer in SIMPLE language.
2. Make it EXAM-FOCUSED.
3. Keep it CONCISE.
4. If it is a definition, give a clear definition.
5. If it is an explanation, include important key points.
6. Use bullet points wherever useful.
7. Give one simple example if required.
8. Do not give unnecessary information.

ANSWER:
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500
                }
            },
            timeout=120
        )

        if response.status_code == 200:

            result = response.json()

            answer = result.get("response", "").strip()

            if answer:
                return answer

            return "⚠️ AI did not generate an answer."

        return f"⚠️ AI Error: {response.status_code}"

    except requests.exceptions.ConnectionError:

        return (
            "⚠️ Ollama is not reachable. "
            "Please make sure Ollama is running."
        )

    except requests.exceptions.Timeout:

        return "⚠️ AI request timed out. Please try again."

    except Exception as e:

        return f"⚠️ AI service unavailable: {str(e)}"


# =========================================================
# GENERATE EXAM NOTES
# =========================================================

def get_exam_notes(topic_name, subject_name):
    """
    Generate exam-oriented notes for a topic.
    """

    prompt = f"""
You are StudyMeta AI, an exam-oriented academic assistant.

Create simple and exam-focused notes for:

Subject: {subject_name}
Topic: {topic_name}

Use this format:

📌 DEFINITION:
Give a clear and simple definition.

📌 KEY POINTS:
• Point 1
• Point 2
• Point 3
• Point 4

📌 IMPORTANT FOR EXAMS:
• Important question 1
• Important question 2

📌 SIMPLE EXAMPLE:
Give one simple example.

Keep the notes:
- Simple
- Short
- Easy to understand
- Exam-focused
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500
                }
            },
            timeout=120
        )

        if response.status_code == 200:

            result = response.json()

            notes = result.get("response", "").strip()

            if notes:
                return notes

            return "⚠️ Notes could not be generated."

        return f"⚠️ Notes generation failed: {response.status_code}"

    except requests.exceptions.ConnectionError:

        return "⚠️ Ollama is not reachable. Please make sure Ollama is running."

    except requests.exceptions.Timeout:

        return "⚠️ Notes generation timed out. Please try again."

    except Exception as e:

        return f"⚠️ AI service unavailable: {str(e)}"