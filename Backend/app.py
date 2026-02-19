from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import PyPDF2
import io
import os
from dotenv import load_dotenv


load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    MODEL_NAME: str = os.getenv("MODEL_NAME")

settings = Settings()
print("Loaded GROQ API KEY:", settings.GROQ_API_KEY)


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stored_questions = []
stored_pdf_text = ""

# ---------------- HOME ----------------
@app.get("/")
def home():
    return {"status": "Backend Running"}

# ---------------- PDF UPLOAD ----------------
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    global stored_questions, stored_pdf_text

    contents = await file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))

    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    if not text.strip():
        return {"error": "PDF text extract ஆகவில்லை"}

    stored_pdf_text = text

    # AI question detect
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
கீழே உள்ள உரையில் உள்ள அனைத்து கேள்விகளையும் மட்டும் எண் இடி பட்டியலிடவும்.
தமிழில் மட்டும்.
"""
            },
            {
                "role": "user",
                "content": text[:2000]
            }
        ],
        temperature=0.3
    )

    questions_text = response.choices[0].message.content

    stored_questions = [
        line.strip()
        for line in questions_text.split("\n")
        if line.strip()
    ]

    return {
        "message": "PDF uploaded successfully",
        "total_questions": len(stored_questions)
    }

# ---------------- ASK ----------------
class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(data: QuestionRequest):
    global stored_questions, stored_pdf_text

    user_input = data.question.strip()

    if not stored_pdf_text:
        return {"error": "முதலில் PDF upload செய்யவும்"}

    # If number given
    if user_input.isdigit():
        q_num = int(user_input)

        if q_num <= 0 or q_num > len(stored_questions):
            return {"error": "Invalid question number"}

        question_text = stored_questions[q_num - 1]
    else:
        question_text = user_input

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """
நீங்கள் தமிழ் ஆசிரியர்.
குறுகிய தெளிவான பதில் மட்டும் அளிக்கவும்.
"""
                },
                {
                    "role": "user",
                    "content": question_text
                }
            ],
            temperature=0.5
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        return {"error": str(e)}
