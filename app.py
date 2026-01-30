from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

client = Groq(api_key="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")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Backend running OK"}

class AskData(BaseModel):
    question: str
    mode: str

@app.post("/ask")
def ask(data: AskData):

    mode_map = {
        "short": "2–3 வரிகளில் மட்டும் பதில் கொடு.",
        "medium": "நடுத்தர அளவில் தெளிவாக விளக்கி சொல்.",
        "explain": "முழு விரிவான விளக்கம் கொடு."
    }

    prompt = f"""
நீ ஒரு தமிழ் இலக்கிய நிபுணர்.

IMPORTANT RULES:
- ஒரே விஷயத்தை மீண்டும் மீண்டும் சொல்லக்கூடாது
- Sentence repetition தவிர்க்கவும்
- Clear, structured, fresh sentences மட்டும்
- Intro + points + conclusion மாதிரி அமை

{mode_map.get(data.mode, mode_map["medium"])}

கேள்வி:
{data.question}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2   # 👈 repetition குறைக்க
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        return {"error": str(e)}
