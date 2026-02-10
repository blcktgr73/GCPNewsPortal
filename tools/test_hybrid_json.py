
import requests
import google.generativeai as genai
import os
import xml.etree.ElementTree as ET
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv("./tools/.env")

# Gemini API 설정
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 1. Google News RSS로 최신 기사 가져오기
def get_google_news_rss(keyword: str, max_results: int = 1):
    print(f"\n[Step 1] Fetching Google News RSS for: {keyword}")
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
            print(f"✅ Found {len(items)} articles.")
            return items
        else:
            print(f"❌ Failed to fetch RSS: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ RSS Error: {e}")
        return []

# 2. Gemini를 사용하여 URL 내용 요약 및 메타데이터 추출 (JSON Output)
def analyze_article_with_gemini(article):
    print(f"\n[Step 2] Analyzing article: {article['title']}")
    
    # 모델: gemini-flash-latest (안정적 최신)
    # JSON 모드 활성화
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
    2. Extract the exact publication date if available in the content (otherwise use RSS date).
    3. Generate a concise summary in Korean.
    4. Return the result in the following JSON format:
    
    {{
        "title": "Exact Title of the article",
        "source_name": "Name of the news source",
        "published_at": "YYYY-MM-DD HH:MM format if possible, or standard date string",
        "url": "{article['link']}",
        "summary": "Korean summary here..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        print(f"✅ Analysis Completed.")
        return response.text
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        return None

# 실행
if __name__ == "__main__":
    keyword = "Gemini AI"
    articles = get_google_news_rss(keyword, max_results=1)
    
    if articles:
        for article in articles:
            json_result = analyze_article_with_gemini(article)
            if json_result:
                print(f"\n[Result JSON]\n{json_result}")
                
                # 파일로 저장하여 확인
                with open("tools/test_json_result.txt", "w", encoding="utf-8") as f:
                    f.write(json_result)
