
import requests
import google.generativeai as genai
import os
import xml.etree.ElementTree as ET
import time
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv("./tools/.env")

# Gemini API 설정
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 1. Google News RSS로 최신 기사 가져오기
def get_rss_links(keyword: str, max_results: int = 10):
    print(f"\n[Step 1] Fetching {max_results} links for: {keyword}")
    links = []
    
    # 여러 페이지를 가져오거나 한 번에 많이 가져오기 (RSS는 100개까지 가능)
    processed_keyword = keyword.replace(" ", "+")
    rss_url = f"https://news.google.com/rss/search?q={processed_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        response = requests.get(rss_url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('./channel/item')[:max_results]:
                title = item.find('title').text
                link = item.find('link').text
                links.append({"title": title, "google_url": link})
            return links
        else:
            print(f"Failed to fetch RSS: {response.status_code}")
            return []
    except Exception as e:
        print(f"RSS Error: {e}")
        return []

# 2. Python requests로 실제 Redirect URL 찾기 (Ground Truth)
def resolve_url_programmatically(google_url):
    try:
        # User-Agent 없으면 구글이 봇으로 인식하여 차단할 수 있음
        headers = {'User-Agent': 'Mozilla/5.0'}
        # allow_redirects=True (기본값)
        response = requests.head(google_url, headers=headers, allow_redirects=True, timeout=5)
        return response.url
    except Exception:
        return None

# 3. Gemini에게 URL 해석 요청하기 (Batch)
def resolve_urls_with_gemini(articles_batch):
    print(f"\n[Step 2] Asking Gemini to resolve {len(articles_batch)} URLs...")
    
    model = genai.GenerativeModel("gemini-flash-latest")
    
    # 배치로 질문
    prompt = "Here is a list of Google News Redirect URLs. Please find the ORIGINAL Source URL for each one:\n\n"
    for idx, art in enumerate(articles_batch):
        prompt += f"{idx+1}. Title: {art['title']}\n   Google Link: {art['google_url']}\n\n"
        
    prompt += """
    Output Format:
    1. [Original URL here]
    2. [Original URL here]
    ...
    
    Just provide the numbered list of URLs. Nothing else.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Parse numbered list
        gemini_urls = []
        for line in text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() and '. ' in line[:5]):
                # Extract URL part (remove "1. ")
                url_part = line.split('. ', 1)[1].strip()
                gemini_urls.append(url_part)
        return gemini_urls
    except Exception as e:
        print(f"Gemini Error: {e}")
        return []

# 실행 및 검증
if __name__ == "__main__":
    keyword = "AI Technology"
    test_count = 10  # 테스트 개수 (너무 많으면 시간 오래 걸림)
    
    articles = get_rss_links(keyword, max_results=test_count)
    if not articles:
        exit()
        
    print(f"\n[Step 3] Comparing Results (Batch of {len(articles)})...")
    
    # 1. Ground Truth (Programmatic)
    print("Resolving programmatically (Ground Truth)...")
    truth_urls = []
    for art in articles:
        resolved = resolve_url_programmatically(art['google_url'])
        truth_urls.append(resolved)
        # print(f"  - {resolved}")
        time.sleep(0.5) # 부하 방지

    # 2. Gemini Prediction
    print("Resolving with Gemini...")
    gemini_urls = resolve_urls_with_gemini(articles)
    
    # 3. Validation
    correct_count = 0
    print("\n--- Validation Report ---")
    
    # Gemini가 누락하거나 더 많이 뱉었을 수 있으므로 min length 사용
    limit = min(len(truth_urls), len(gemini_urls))
    
    for i in range(limit):
        truth = truth_urls[i]
        prediction = gemini_urls[i]
        
        # 간단한 도메인 매칭 또는 전체 일치 확인
        # URL 파라미터(utm_source 등) 차이가 있을 수 있으므로 도메인/경로 중요
        is_match = False
        if truth and prediction and (truth in prediction or prediction in truth):
            is_match = True
        
        status = "✅ MATCH" if is_match else "❌ MISMATCH"
        if is_match: correct_count += 1
        
        print(f"[{i+1}] {status}")
        print(f"  Truth: {truth}")
        print(f"  Gemini: {prediction}")
        print("-" * 30)
        
    print(f"\nAccuracy: {correct_count}/{limit} ({correct_count/limit*100:.1f}%)")
