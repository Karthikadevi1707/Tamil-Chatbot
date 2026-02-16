from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uuid
from groq import Groq

# ------------------------
# CONFIG
# ------------------------

GROQ_API_KEY = "GROQ_API_KEY"

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# DATABASE
# ------------------------

conn = sqlite3.connect("memory.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    chat_id TEXT,
    role TEXT,
    message TEXT
)
""")
conn.commit()

# ------------------------
# MODELS
# ------------------------

class ChatRequest(BaseModel):
    chat_id: str
    message: str

# ------------------------
# CREATE NEW CHAT
# ------------------------

@app.get("/new_chat")
def new_chat():
    chat_id = str(uuid.uuid4())
    return {"chat_id": chat_id}

# ------------------------
# GET CHAT HISTORY LIST
# ------------------------

@app.get("/chat_list")
def chat_list():

    cursor.execute("""
    SELECT chat_id, message 
    FROM chats 
    WHERE role='user'
    GROUP BY chat_id
    ORDER BY rowid DESC
    """)

    chats = cursor.fetchall()

    result = []

    for chat in chats:
        chat_id = chat[0]
        first_msg = chat[1][:30]

        result.append({
            "chat_id": chat_id,
            "title": first_msg
        })

    return result


# ------------------------
# GET CHAT MESSAGES
# ------------------------

@app.get("/chat/{chat_id}")
def get_chat(chat_id: str):

    cursor.execute("""
    SELECT role, message FROM chats WHERE chat_id=?
    """, (chat_id,))

    messages = cursor.fetchall()

    return messages


# ------------------------
# CHAT ENDPOINT
# ------------------------

@app.post("/chat")
def chat(req: ChatRequest):

    # Save user message
    cursor.execute(
        "INSERT INTO chats VALUES (?, ?, ?)",
        (req.chat_id, "user", req.message)
    )
    conn.commit()

    # Get history
    cursor.execute(
        "SELECT role, message FROM chats WHERE chat_id=?",
        (req.chat_id,)
    )

    history = cursor.fetchall()

    messages = []

    for role, msg in history:
        messages.append({
            "role": role,
            "content": msg
        })

    # Call Groq
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages
    )

    answer = response.choices[0].message.content

    # Save bot response
    cursor.execute(
        "INSERT INTO chats VALUES (?, ?, ?)",
        (req.chat_id, "assistant", answer)
    )
    conn.commit()

    return {"answer": answer}
