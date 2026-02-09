
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Try loading from various locations
locations = [
    os.path.join(os.getcwd(), 'utils', '.env'), # Just in case
    os.path.join(os.getcwd(), 'tools', '.env'),
    os.path.join(os.getcwd(), 'backend', '.env'),
    os.path.join(os.getcwd(), 'news_summarizer', '.env'),
    os.path.join(os.getcwd(), '.env')
]

successful_key = None

print("Checking .env files for a valid API Key...")

for env_path in locations:
    if os.path.exists(env_path):
        # Create a fresh environment for each check to avoid pollution
        # Actually load_dotenv doesn't override existing if override=False (default)
        # So we should clear or specifically load.
        # Simplest is to read the file manually or use clean env.
        
        # Let's just use load_dotenv with override=True
        load_dotenv(env_path, override=True)
        key = os.getenv("GEMINI_API_KEY")
        
        if key:
            print(f"Found key in: {env_path} (Starts with: {key[:4]}...)")
            genai.configure(api_key=key)
            try:
                # Try a lightweight call
                list(genai.list_models(page_size=1))
                print(f"[SUCCESS] Valid key found in {env_path}")
                successful_key = key
                break
            except Exception as e:
                # Simplify error message to avoid clutter
                err_msg = str(e).split('\n')[0]
                print(f"[FAIL] Key in {env_path} failed: {err_msg}")
        else:
            print(f"[INFO] No GEMINI_API_KEY in {env_path}")

if successful_key:
    genai.configure(api_key=successful_key)
    print("\n--- Support Model List ---")
    try:
        found_any = False
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                found_any = True
                print(f"Model Name: {model.name}")
                print(f"Display Name: {model.display_name}")
                print(f"Description: {model.description}\n")
        
        if not found_any:
            print("No models found with 'generateContent' capability.")
            
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("\n[WARN] No valid API Key found in any .env file.")
