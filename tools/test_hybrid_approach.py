
import requests
import google.generativeai as genai
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv("./tools/.env")

# Gemini API 설정
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 1. Google News RSS로 최신 기사 가져오기
def get_google_news_rss(keyword: str, max_results: int = 3):
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

# 2. Gemini를 사용하여 URL 내용 요약하기 (Grounding 없이)
def summarize_article(article):
    print(f"\n[Step 2] Summarizing article: {article['title']}")
    
    # 모델: gemini-flash-latest (안정적 최신)
    model = genai.GenerativeModel("gemini-flash-latest")
    
    prompt = f"""
    You are a helpful news assistant.
    Please summarize the following news article in Korean.
    
    Title: {article['title']}
    Source: {article['source']}
    Date: {article['pub_date']}
    Link: {article['link']}
    
    Using the information above (and your knowledge if available), provide a concise summary in Korean (3-4 sentences).
    Focus on the "Who, What, When, Where, Why" if possible.
    """
    
    try:
        response = model.generate_content(prompt)
        print(f"✅ Summary Generated.")
        
        with open("tools/test_result.txt", "w", encoding="utf-8") as f:
            f.write(f"Article: {article['title']}\n")
            f.write(f"Summary: {response.text}\n")
            
        return response.text
    except Exception as e:
        print(f"❌ Summarization Error: {e}")
        return None

# 실행
if __name__ == "__main__":
    keyword = "Gemini AI"
    articles = get_google_news_rss(keyword, max_results=1)
    
    if articles:
        for article in articles:
            summary = summarize_article(article)
