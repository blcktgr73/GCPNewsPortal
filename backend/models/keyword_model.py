from pydantic import BaseModel

class KeywordCreate(BaseModel):
    keyword: str

class KeywordItem(BaseModel):
    id: str
    keyword: str
    created_at: str