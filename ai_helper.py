import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.5-flash:generateContent"
)


def get_syllabus_answer(question, topic_name=None, subject_name=None):

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
            GEMINI_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()

            return (
                data["candidates"][0]["content"]["parts"][0]["text"]
                .strip()
            )

        return f"⚠️ Gemini AI Error: {response.status_code}"

    except Exception as e:
        return f"⚠️ AI service unavailable: {str(e)}"


def get_exam_notes(topic_name, subject_name):

    prompt = f"""
Create exam-oriented notes for:

Topic: {topic_name}
Subject: {subject_name}

Format:

DEFINITION:
Give a clear definition.

KEY POINTS:
• Point 1
• Point 2
• Point 3

IMPORTANT FOR EXAMS:
• Important question 1
• Important question 2

SIMPLE EXAMPLE:
Give one simple example.

Keep the notes simple, short and exam-focused.
"""

    try:
        response = requests.post(
            GEMINI_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()

            return (
                data["candidates"][0]["content"]["parts"][0]["text"]
                .strip()
            )

        return "⚠️ Notes generation failed."

    except Exception as e:
        return f"⚠️ AI service unavailable: {str(e)}"