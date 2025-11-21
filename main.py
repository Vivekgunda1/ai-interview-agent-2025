# main.py - AI Interview Agent with Resume Parsing (Groq + FastAPI + React)
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pdfplumber
from dotenv import load_dotenv

load_dotenv()  # Loads GROQ_API_KEY from .env file

app = FastAPI(title="AI Interview Agent")

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure way: reads from .env (never hardcode keys!)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Simple in-memory session store
sessions = {}

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        text = f"Error reading PDF: {str(e)}"
    return text

@app.post("/start-interview")
async def start_interview(
    job_role: str = Form(...),
    candidate_name: str = Form("Candidate"),
    resume: UploadFile = File(...)
):
    # Save resume temporarily
    os.makedirs("resumes", exist_ok=True)
    resume_path = f"resumes/{resume.filename}"
    with open(resume_path, "wb") as f:
        content = await resume.read()
        f.write(content)

    resume_text = extract_text_from_pdf(resume_path)

    system_prompt = f"""
You are an expert interviewer for the role: {job_role}.
Candidate: {candidate_name}
Resume:
{resume_text[:10000]}

Instructions:
- Greet the candidate by name
- Ask ONE thoughtful question at a time based on their experience
- Be professional, encouraging, and adaptive
- After 8–10 questions, give a final summary and score (1–10) with clear reasoning
"""

    session_id = f"{candidate_name}_{job_role}_{len(sessions)}"
    sessions[session_id] = [{"role": "system", "content": system_prompt}]

    # First AI message
    chain = ChatPromptTemplate.from_messages(sessions[session_id]) | llm | StrOutputParser()
    first_reply = chain.invoke({}).strip()
    sessions[session_id].append({"role": "assistant", "content": first_reply})

    return {"message": first_reply, "session_id": session_id}

@app.post("/answer")
async def answer_question(
    session_id: str = Form(...),
    user_answer: str = Form(...)
):
    if session_id not in sessions:
        return {"error": "Session expired. Please start a new interview."}

    sessions[session_id].append({"role": "user", "content": user_answer})

    chain = ChatPromptTemplate.from_messages(sessions[session_id]) | llm | StrOutputParser()
    reply = chain.invoke({}).strip()

    sessions[session_id].append({"role": "assistant", "content": reply})

    return {"reply": reply}