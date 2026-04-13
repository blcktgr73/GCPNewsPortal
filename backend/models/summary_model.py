from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

class NewsSummary(BaseModel):
    title: str
    url: str
    summary: str
    keywords: str
    createdAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    summaryTokens: int