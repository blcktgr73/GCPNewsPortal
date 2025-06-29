from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.firebase_init import *  # 초기화 먼저!
from services.summary_service import save_summary, fetch_summaries_by_user
from services.auth_service import verify_firebase_token
from models.summary_model import NewsSummary 
from models.keyword_model import KeywordCreate, KeywordItem
from services.keyword_service import add_keyword, get_keywords, delete_keyword
#from services.summary_service import summarize_and_store

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

@app.get("/summaries")
def get_summaries(user_id: str = Depends(verify_firebase_token)):
    try:
        results = fetch_summaries_by_user(user_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keywords")
def post_keyword(data: KeywordCreate, user_id: str = Depends(verify_firebase_token)):
    try:
        keyword_id = add_keyword(user_id, data.keyword)

        # 🔽 추가: 키워드로 뉴스 수집 및 요약 생성. 동작 안되서 미뤄둠
        #summary = summarize_and_store(user_id, data.keyword)

        return {"status": "keyword added and summary saved", "id": keyword_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/keywords", response_model=list[KeywordItem])
def list_keywords(user_id: str = Depends(verify_firebase_token)):
    try:
        return get_keywords(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/keywords/{keyword_id}")
def remove_keyword(keyword_id: str, user_id: str = Depends(verify_firebase_token)):
    try:
        delete_keyword(user_id, keyword_id)
        return {"status": "keyword deleted"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Keyword not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
