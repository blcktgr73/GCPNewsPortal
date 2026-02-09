
import google.generativeai as genai
import os
import json
from datetime import datetime
import re

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def fetch_grounded_news(keyword: str, max_results: int = 5):
    """
    Two-phase approach:
    1. Use Gemini 1.5 Flash with 'google_search' tool to get latest news in text format.
    2. Use Gemini (without Grounding) to parse that text into structured JSON.
    """
    if not api_key:
        print("GEMINI_API_KEY not found.")
        return []

    # gemini-1.5-flash is stable and supports google_search tool
    model_name = "gemini-1.5-flash"
    
    # --- Phase 1: Search and Retrieve (Grounding) ---
    print(f"[Phase 1] Searching news for: {keyword} (Model: {model_name})")
    
    # Updated Tool definition for 1.5 Flash / Latest API
    tools = [
        {"google_search": {}}
    ]

    try:
        model_p1 = genai.GenerativeModel(model_name=model_name, tools=tools)
    except Exception as e:
        print(f"[Phase 1 Init Error] {e}")
        return []

    today = datetime.now().strftime("%Y-%m-%d")
    prompt_p1 = f"""
    Find the latest news about "{keyword}". Today is {today}.
    Provide a detailed report on the top {max_results} most relevant news articles.
    For each article, clearly state:
    1. The exact Title
    2. The Source Name (e.g. CNN, BBC, Yonhap News)
    3. The Publication Date
    4. The exact original Link/URL
    5. A concise summary of the content in Korean.
    """

    try:
        # Grounding call
        response_p1 = model_p1.generate_content(prompt_p1)
        
        # Check if grounding actually happened (optional check)
        # if response_p1.candidates and response_p1.candidates[0].grounding_metadata:
        #    print("[Info] Grounding metadata present.")
        
        search_result_text = response_p1.text
        # print(f"[Phase 1 Output] {search_result_text[:200]}...") 
        
    except Exception as e:
        print(f"[Phase 1 Execution Error] {e}")
        return []

    # --- Phase 2: Format to JSON (No Grounding) ---
    print(f"[Phase 2] Formatting to JSON...")

    try:
        model_p2 = genai.GenerativeModel(
            model_name=model_name,
            # No tools here
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        )

        prompt_p2 = f"""
        You are a data extraction assistant.
        Below is a text report containing news articles.
        Extract the articles into a JSON list.
        
        The JSON structure must be:
        [
          {{
            "title": "...",
            "source_name": "...",
            "published_at": "...",
            "url": "...",
            "summary": "..."
          }}
        ]

        Start of Report:
        {search_result_text}
        End of Report
        """

        response_p2 = model_p2.generate_content(prompt_p2)
        json_text = response_p2.text
        
        # Clean up Markdown code blocks if present (though schema should prevent this)
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
            
        news_data = json.loads(json_text)
        
        # Robust structure validation
        if isinstance(news_data, dict):
            # Handle cases where model wraps result in {"articles": [...]}
            keys = list(news_data.keys())
            if len(keys) == 1 and isinstance(news_data[keys[0]], list):
                news_data = news_data[keys[0]]
                
        if not isinstance(news_data, list):
             print(f"[Phase 2 Error] Result is not a list: {type(news_data)}")
             return []

        print(f"[Phase 2] Successfully parsed {len(news_data)} articles.")
        return news_data

    except Exception as e:
        print(f"[Phase 2 Error] JSON parsing failed: {e}")
        return []
