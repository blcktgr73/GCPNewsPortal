# Transformation: T-20260209-001 - Gemini Grounding Integration

**Date**: 2026-02-09
**Status**: Proposed

## Intent
**Problem**:
- The current news fetching relies on scraping `news.google.com` which is brittle and returns redirect URLs (`news.google.com/rss/...`) instead of original source links.
- The current summarization uses a non-existent or typo model `gemini-2.5-flash` via raw REST API.
- It fails to capture metadata like "Publication Date" or "Source Name".
- The summarization is "blind" (only title+URL provided to model) without actual article content.

**Solution**:
- Replace scraping with **Gemini 1.5 Flash** using **Google Search Grounding**.
- Use the official `google-generativeai` SDK.
- Prompt Gemini to find news, and return a structured JSON response containing Title, Original URL, Summary, and Date.

## Impact Analysis
- **Themes Affected**: News Consumption
- **Structural Changes**:
    - `news_summarizer/requirements.txt`: Add `google-generativeai`.
    - `news_summarizer/services/google_news.py`: Deprecate/Remove scraping logic.
    - `news_summarizer/services/gemini_service.py`: Create new service for Grounding.
    - `news_summarizer/services/summary_service.py`: Update to use `gemini_service`.

## Design Options
### Option A: Grounding for Discovery & Summary (Recommended)
- **Mechanism**: Ask Gemini: "Search for latest news about {keyword}. Return JSON list with title, original_url, summary, date."
- **Pros**:
    - Solves "Real URL" issue (Grounding returns source).
    - Solves "Date" issue.
    - "Summary" is based on actual search content (RAG-like).
    - Simplifies code (No BeautifulSoup).
- **Cons**:
    - Relies on Gemini's search capabilities/ranking.

### Option B: Scraping + Grounding for Verification
- **Mechanism**: Scrape Google News URLs -> Ask Gemini to visit/verify.
- **Pros**: More control over initial list.
- **Cons**: Still have to deal with Google redirects and scraping fragility.

## Verification Plan
- [ ] Verify `google-generativeai` integration locally (if possible) or via deployment.
- [ ] Check if `gemini-1.5-flash` returns valid JSON with Grounding.
- [ ] Validate that URLs are direct links (not `news.google.com` redirects).
