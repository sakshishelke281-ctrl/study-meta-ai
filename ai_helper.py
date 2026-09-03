import requests

# Ollama API
OLLAMA_URL = "http://localhost:11434/api/generate"

# AI Model
MODEL_NAME = "phi"


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
            return result.get("response", "").strip()

        return f"⚠️ AI Error: {response.status_code}"

    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama is not running. Please start Ollama first."

    except Exception as e:
        return f"⚠️ AI service unavailable: {str(e)}"


def get_exam_notes(topic_name, subject_name):
    """
    Generate exam-oriented notes for a topic.
    """

    prompt = f"""
Create exam-oriented notes for:

Topic: {topic_name}
Subject: {subject_name}

Format:

📌 DEFINITION:
Give a clear definition.

📌 KEY POINTS:
• Point 1
• Point 2
• Point 3

📌 IMPORTANT FOR EXAMS:
• Important question 1
• Important question 2

📌 SIMPLE EXAMPLE:
Give one simple example.

Keep the notes simple, short and exam-focused.
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
            return response.json().get("response", "").strip()

        return "⚠️ Notes generation failed."

    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama is not running."

    except Exception as e:
        return f"⚠️ AI service unavailable: {str(e)}"