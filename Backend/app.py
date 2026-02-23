from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
import uvicorn
from PyPDF2 import PdfReader
from groq import Groq

# 🔐 PUT YOUR GROQ API KEY
GROQ_API_KEY = "REMOVED_GROQ_KEY"

TEXT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=GROQ_API_KEY)

class Question(BaseModel):
    question: str

# 🔹 TEXT QUESTION
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
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": str(e)}

# 🔹 IMAGE QUESTION
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
                        {"type": "text", "text": "இந்த படத்தில் உள்ள கேள்விக்கு தமிழில் முழு பதில் அளிக்கவும்."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": str(e)}

# 🔹 PDF QUESTION
@app.post("/pdf-question")
async def pdf_question(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        pdf = PdfReader(io.BytesIO(contents))

        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "PDF உள்ளடக்கத்தை தமிழில் விளக்கவும்."},
                {"role": "user", "content": text[:12000]},
            ],
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)