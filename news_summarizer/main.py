import os
import functions_framework
from flask import Request, jsonify
#from dotenv import load_dotenv
from services.summary_service import summarize_and_store

#load_dotenv()

@functions_framework.http
def summarize_news(request: Request):
    request_json = request.get_json(silent=True)
    user_id = request_json.get("user_id")
    keyword = request_json.get("keyword")

    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    try:
        summarize_and_store(keyword, user_id)
        return jsonify({"message": f"Summarization for '{keyword}' complete."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
