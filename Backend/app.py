from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
import uvicorn
from PyPDF2 import PdfReader
from groq import Groq
import os
from dotenv import load_dotenv

# ✅ Load .env file
load_dotenv()

# ✅ Get API key safely
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

TEXT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Initialize Groq client
client = Groq(api_key=groq_api_key)

# ✅ Request model
class Question(BaseModel):
    question: str


# =============================
# TEXT QUESTION ENDPOINT
# =============================
@app.post("/ask")
def ask_question(data: Question):
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "தமிழில் விரிவாக விளக்கவும்."},
                {"role": "user", "content": data.question}
            ],
        )

        return {
            "status": "success",
            "answer": response.choices[0].message.content
        }

    except Exception as e:
        return {
            "status": "error",
            "answer": str(e)
        }


# =============================
# IMAGE QUESTION ENDPOINT
# =============================
@app.post("/image-question")
async def image_question(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        image_base64 = base64.b64encode(contents).decode("utf-8")

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "இந்த படத்தில் உள்ள கேள்விக்கு தமிழில் முழு பதில் அளிக்கவும்."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ],
                }
            ],
        )

        return {
            "status": "success",
            "answer": response.choices[0].message.content
        }

    except Exception as e:
        return {
            "status": "error",
            "answer": str(e)
        }


# =============================
# PDF QUESTION ENDPOINT
# =============================
@app.post("/pdf-question")
async def pdf_question(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        pdf = PdfReader(io.BytesIO(contents))

        text = ""

        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

        # limit text to avoid token overflow
        text = text[:12000]

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "PDF உள்ளடக்கத்தை தமிழில் விளக்கவும்."},
                {"role": "user", "content": text},
            ],
        )

        return {
            "status": "success",
            "answer": response.choices[0].message.content
        }

    except Exception as e:
        return {
            "status": "error",
            "answer": str(e)
        }


# =============================
# HEALTH CHECK
# =============================
@app.get("/")
def root():
    return {"message": "Backend running successfully"}


# =============================
# RUN SERVER
# =============================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)