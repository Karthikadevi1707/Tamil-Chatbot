from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import base64

print("🔥 Tamil Literature AI Backend Running 🔥")

GROQ_API_KEY = "REMOVED_GROQ_KEY"

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {"status": "Backend Running 🚀"}


# 🔹 TEXT + VOICE
@app.post("/ask")
def ask_question(data: QuestionRequest):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """
                    நீங்கள் தமிழ் இலக்கிய பேராசிரியர்.
                    விரிவான பதில் அளிக்கவும்.
                    கட்டுரை என்றால் துணைத் தலைப்புகள் பயன்படுத்தவும்.
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


# 🔹 IMAGE (Latest Working Vision Model)
@app.post("/image-question")
async def image_question(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                            இந்த படத்தில் உள்ள கேள்வியை கண்டறிந்து
                            விரிவாக தமிழில் பதில் அளிக்கவும்.
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        return {"answer": f"Image Server Error: {str(e)}"}
