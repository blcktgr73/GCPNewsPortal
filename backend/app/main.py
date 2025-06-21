from fastapi import FastAPI
from app.firebase_init import *  # 초기화 먼저!
from services.summary_service import save_summary, get_summaries
from models.summary_model import NewsSummary

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/summary/{user_id}")
def post_summary(user_id: str, summary: NewsSummary):
    save_summary(user_id, summary)
    return {"status": "summary saved"}

@app.get("/summary/{user_id}")
def list_summaries(user_id: str):
    return get_summaries(user_id)
