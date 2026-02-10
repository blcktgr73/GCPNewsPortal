
import google.generativeai as genai
import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def fetch_grounded_news(keyword: str, max_results: int = 5):
    """
    Hybrid approach:
    1. Fetch news links via Google News RSS.
    2. Use Gemini 1.5 Flash (or gemini-flash-latest) to analyze each link and format as JSON.
    """
    if not api_key:
        print("GEMINI_API_KEY not found.")
        return []

    print(f"[Phase 1] Fetching RSS for: {keyword}")
    articles = _get_google_news_rss(keyword, max_results)
    
    if not articles:
        print("[Phase 1] No articles found.")
        return []

    print(f"[Phase 2] Analyzing {len(articles)} articles with Gemini...")
    final_news = []
    
    for article in articles:
        try:
            # Individual analysis for better quality
            json_result = _analyze_article_with_gemini(article)
            if json_result:
                final_news.append(json_result)
        except Exception as e:
            print(f"[Phase 2 Error] Failed to process article: {e}")
            continue
            
    return final_news

def _get_google_news_rss(keyword: str, max_results: int):
    # RSS URL construction
    processed_keyword = keyword.replace(" ", "+")
    rss_url = f"https://news.google.com/rss/search?q={processed_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = []
            for item in root.findall('./channel/item')[:max_results]:
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text
                source = item.find('source').text if item.find('source') is not None else "Unknown"
                
                items.append({
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "source": source
                })
            return items
        else:
            print(f"[RSS Error] Status Code: {response.status_code}")
            return []
    except Exception as e:
        print(f"[RSS Error] Exception: {e}")
        return []

def _analyze_article_with_gemini(article):
    # Model: gemini-flash-latest (Stable & Fast)
    model = genai.GenerativeModel(
        "gemini-flash-latest",
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = f"""
    You are a professional news analyst.
    Please analyze the following news article found at this link: {article['link']}
    
    Base Information from RSS:
    - Title: {article['title']}
    - RSS PubDate: {article['pub_date']}
    - Source: {article['source']}
    
    Task:
    1. Visit the link or use your knowledge to understand the content.
    2. Extract the exact publication date.
       - IMPORTANT: Convert the date to **KST (Korea Standard Time, UTC+9)**.
       - Format must be 'YYYY-MM-DD HH:MM'.
       - If only RSS date is available, convert '{article['pub_date']}' to KST.
    3. Generate a concise summary in Korean.
    4. Return the result in the following JSON format:
    
    {{
        "title": "{article['title']}",
        "source_name": "{article['source']}",
        "published_at": "YYYY-MM-DD HH:MM", 
        "url": "{article['link']}",
        "summary": "Korean summary here..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"[Gemini Error] {e}")
        return None
