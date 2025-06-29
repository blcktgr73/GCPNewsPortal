# news_summary.py

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime
import os
import json
#from dotenv import load_dotenv

# 전역 디버그 설정
DEBUG_MODE = False

headers = {'User-Agent': 'Mozilla/5.0'}

# .env 경로 설정
#load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def get_naver_news(query, max_results=3):
    url = f"https://search.naver.com/search.naver?where=news&query={query}"
    res = requests.get(url, headers=headers)

    soup = BeautifulSoup(res.text, 'html.parser')
    items = soup.select('a[href^="https://n.news.naver.com/"]')[:max_results]
    
    # 디버깅 뉴스 갯수 출력
    if DEBUG_MODE:
        print(f"[NAVER] 뉴스 개수: {len(items)}")
    return [(a.text.strip(), a['href']) for a in items]

def get_google_news(query, max_results=3):
    url = f"https://news.google.com/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers)

    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select("a.JtKRv")[:max_results]
    news_list = []
    for a in items:
        title = a.text.strip()
        href = a.get("href", "")
        # 상대경로를 절대경로로 변경
        if href.startswith("./"):
            href = "https://news.google.com" + href[1:]
        news_list.append((title, href))
    if DEBUG_MODE:
        print(f"[Google] 뉴스 개수: {len(news_list)}")
    return news_list

def fetch_article_content(url):
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.select('article p')
        text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
        return text[:1000]
    except Exception as e:
        return f"(본문 수집 실패: {e})"

def fetch_naver_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://www.naver.com'
        }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        article = soup.select_one('article')
        if article:
            paragraphs = article.find_all(['p', 'div'])
            text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return text[:2000]
        else:
            return "(기사 본문을 찾을 수 없음)"
    except Exception as e:
        return f"(본문 수집 실패: {e})"

def summarize_with_gpt(title, url):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "YOUR KEY")
    if "n.news.naver.com" in url:
        content = fetch_naver_article_content(url)
        prompt = f"다음은 뉴스 기사입니다. 기사의 제목을 첫 줄에 포함해주세요. 그리고, 핵심 내용을 3줄 이내로 요약해 주세요.\n\n제목: {title}\n본문:\n{content}"
    else:
        content = fetch_article_content(url)
        prompt = f"다음은 뉴스 기사입니다. 핵심 내용을 3줄 이내로 요약해 주세요:\n\n제목: {title}\n내용: {content}"
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(요약 실패: {e})"
    

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"

headers = {
    "Content-Type": "application/json"
}

def summarize_with_gemini(title: str, url: str) -> str:
    """뉴스 제목과 URL을 받아 Gemini를 사용해 요약을 생성합니다."""
    prompt = f"""
    다음은 뉴스 제목과 URL입니다. 해당 뉴스의 내용을 짧고 핵심적으로 요약해 주세요.
    
    제목: {title}
    기사 링크: {url}

    요약은 한국어로 작성해 주세요.
    """

    data = {
        "contents": [{
            "parts": [{
                "text": prompt.strip()
            }]
        }]
    }

    params = {
        "key": API_KEY
    }

    try:
        response = requests.post(API_URL, headers=headers, params=params, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()
        summary_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return summary_text.strip()
    except Exception as e:
        print(f"Gemini 요약 요청 중 오류 발생: {e}")
        return "요약 생성에 실패했습니다."


def run_news_summary(query):
    #result = {"네이버": [], "구글": []}
    #for portal, func in [("네이버", get_naver_news), ("구글", get_google_news)]:
    result = {"구글": []}
    for portal, func in [("구글", get_google_news)]:

        try:
            for title, url in func(query):
                #summary = summarize_with_gpt(title, url)
                summary = summarize_with_gemini(title, url)
                result[portal].append((title, url, summary))
        except Exception as e:
            result[portal].append(("수집 실패", "#", str(e)))
    return result

def save_all_queries_to_markdown(all_results, all_queries, output_dir="/volume2/backups/Obsidian/Newbie/0. Inbox"):
    today = datetime.now().strftime('%Y-%m-%d')
    filename = os.path.join(output_dir, f"multi_news_ALL_{today}.md")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 📰 {today} - 전체 키워드 뉴스 요약\n\n")
        for query in all_queries:
            f.write(f"\n---\n\n## 🔍 키워드: {query}\n\n")
            result = all_results[query]
            for portal, items in result.items():
                f.write(f"### 🔎 {portal} 뉴스\n")
                for title, url, summary in items:
                    f.write(f"- [{title}]({url})\n  > {summary}\n\n")
    return filename

if __name__ == "__main__":

    queries = ["AI 기술"]

    all_results = {}
    for q in queries:
        print(f"▶️ 수집 시작: {q}")
        result = run_news_summary(q)
        all_results[q] = result

    #final_path = save_all_queries_to_markdown(all_results, queries)
    #print(f"✅ 전체 결과 저장 완료: {final_path}")
    print(all_results)
