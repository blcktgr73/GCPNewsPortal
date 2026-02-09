
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

model_name = "models/gemini-flash-latest"

print(f"Testing capabilities for: {model_name}")

# --- Test 1: Grounding (Google Search) ---
print("\n[Test 1] Grounding (Google Search)...")
try:
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
        print("✅ Grounding supported.")
        # print(response.text[:100] + "...")
    else:
        print("❓ Grounding metadata not found (might rely on threshold).")
        # Force search query to check
        response_force = model.generate_content("What is the stock price of Google right now?")
        if response_force.candidates and response_force.candidates[0].grounding_metadata:
             print("✅ Grounding supported (confirmed with forced query).")
        else:
             print("❌ Grounding might not be configured or supported.")

except Exception as e:
    print(f"❌ Grounding Test Failed: {e}")


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
            print("✅ JSON Mode supported.")
            print(f"Output: {json.dumps(data, indent=2)}")
        else:
            print(f"❓ JSON parsed but unexpected structure: {type(data)}")
    except json.JSONDecodeError:
         print(f"❌ JSON Mode Failed: Output is not valid JSON.\n{response_json.text}")

except Exception as e:
    print(f"❌ JSON Mode Test Failed: {e}")
