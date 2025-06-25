from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsSummary(BaseModel):
    title: str
    url: str
    summary: str
    keywords: str
    createdAt: Optional[datetime] = Field(default_factory=datetime.utcnow)
    summaryTokens: int