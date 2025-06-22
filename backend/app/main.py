from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.firebase_init import *  # 초기화 먼저!
from services.summary_service import save_summary, get_summaries, fetch_summaries_by_user
from models.summary_model import NewsSummary 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/summaries")
def get_summaries(user_id: str = Query(...)):
    try:
        results = fetch_summaries_by_user(user_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
