from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import base64
from PyPDF2 import PdfReader
from io import BytesIO
import os
from dotenv import load_dotenv

print("🔥 Tamil AI Backend Running 🔥")

##GROQ_API_KEY = "REMOVED_GROQ_KEY"
##client = Groq(api_key=GROQ_API_KEY)

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

# -----------------------------
# MODELS
TEXT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
# -----------------------------

class QuestionRequest(BaseModel):
    question: str

class ImagePrompt(BaseModel):
    prompt: str


@app.get("/")
def home():
    return {"status": "Backend Running 🚀"}


# 🔹 TEXT
@app.post("/ask")
def ask_question(data: QuestionRequest):
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """
                    நீங்கள் தமிழ் இலக்கிய பேராசிரியர்.
                    விரிவாகவும் துணைத் தலைப்புகளுடன் பதில் அளிக்கவும்.
                    """
                },
                {"role": "user", "content": data.question}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        return {"answer": f"Server Error: {str(e)}"}


# 🔹 IMAGE UNDERSTANDING
@app.post("/image-question")
async def image_question(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": "இந்த படத்தில் உள்ளதை விவரமாக தமிழில் விளக்கவும்."},
                        {"type": "image_url",
                         "image_url": {
                             "url": f"data:image/jpeg;base64,{base64_image}"
                         }}
                    ]
                }
            ],
            max_tokens=1500
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        return {"answer": f"Image Server Error: {str(e)}"}


# 🔹 PDF
@app.post("/pdf-question")
async def pdf_question(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        reader = PdfReader(BytesIO(pdf_bytes))

        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system",
                 "content": "PDF உள்ளடக்கத்தை அடிப்படையாக கொண்டு தமிழில் விளக்கவும்."},
                {"role": "user", "content": text[:12000]}
            ],
            max_tokens=1500
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        return {"answer": f"PDF Error: {str(e)}"}


# 🔹 IMAGE GENERATION (Prompt → Creative Description)
@app.post("/generate-image")
def generate_image(data: ImagePrompt):
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """
                    பயனர் கொடுத்த prompt அடிப்படையில்
                    ஒரு மிக அழகான காட்சியை விரிவாக விவரிக்கவும்.
                    (Image generation style description)
                    """
                },
                {"role": "user", "content": data.prompt}
            ],
            max_tokens=1000
        )

        description = response.choices[0].message.content

        return {"image_description": description}

    except Exception as e:
        return {"error": str(e)}