from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsSummary(BaseModel):
    url: str
    title: str
    summary: str
    createdAt: Optional[datetime] = Field(default_factory=datetime.utcnow)
    source: str = "Google"
    category: str
    keywords: List[str]
    summaryTokens: int