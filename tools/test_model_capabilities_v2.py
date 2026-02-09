
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load from backend .env
backend_env_path = os.path.join(os.getcwd(), 'backend', '.env')
load_dotenv(backend_env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("API Key not found.")
    exit(1)

genai.configure(api_key=api_key)

# Test with gemini-2.0-flash-exp (known to support search grounding)
# Also trying gemini-1.5-flash as fallback/alternative
model_names = ["gemini-2.0-flash-exp", "gemini-1.5-flash"]

for model_name in model_names:
    print(f"\n--------------------------------------------------")
    print(f"Testing Model: {model_name}")
    print(f"--------------------------------------------------")

    # --- Test 1: Grounding (Google Search) ---
    print("\n[Test 1] Grounding (Google Search)...")
    try:
        # Use the 'google_search_retrieval' tool configuration
        tools = [
            {"google_search_retrieval": {
                "dynamic_retrieval_config": {
                    "mode": "dynamic",
                    "dynamic_threshold": 0.3,
                }
            }}
        ]
        
        model = genai.GenerativeModel(model_name=model_name, tools=tools)
        response = model.generate_content("What is the latest news about Google Gemini?")
        
        # Check if grounding metadata exists in the response
        if response.candidates and response.candidates[0].grounding_metadata:
             print("[SUCCESS] Grounding supported.")
             print(f"Response Snippet: {response.text[:100]}...")
             if response.candidates[0].grounding_metadata.search_entry_point:
                 print(f"Search Entry Point: {response.candidates[0].grounding_metadata.search_entry_point}")
        else:
             print("[WARN] Grounding metadata not found (might assume no search needed).")

    except Exception as e:
        print(f"[FAIL] Grounding Test Failed: {e}")


    # --- Test 2: JSON Mode ---
    print("\n[Test 2] JSON Mode...")
    try:
        model_json = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = """
        List 3 distinct colors in JSON format.
        Example: [{"color": "red"}, ...]
        """
        
        response_json = model_json.generate_content(prompt)
        
        try:
            data = json.loads(response_json.text)
            if isinstance(data, list) or isinstance(data, dict):
                print("[SUCCESS] JSON Mode supported.")
                # print(f"Output: {json.dumps(data, indent=2)}")
            else:
                print(f"[WARN] JSON parsed but unexpected structure: {type(data)}")
        except json.JSONDecodeError:
             print(f"[FAIL] JSON Mode Failed: Output is not valid JSON.\n{response_json.text}")

    except Exception as e:
        print(f"[FAIL] JSON Mode Test Failed: {e}")
