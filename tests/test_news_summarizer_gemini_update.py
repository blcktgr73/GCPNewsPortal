
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json

# Adjust path to include news_summarizer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'news_summarizer'))

from services.gemini_service import fetch_grounded_news, _get_google_news_rss, _analyze_article_with_gemini

class TestGeminiServiceHybrid(unittest.TestCase):

    @patch('services.gemini_service.genai')
    @patch('services.gemini_service.requests.get')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_fetch_grounded_news_success(self, mock_requests_get, mock_genai):
        # 1. Mock RSS Response (Phase 1)
        mock_rss_response = MagicMock()
        mock_rss_response.status_code = 200
        # Simple RSS XML for testing
        mock_rss_response.content = b"""
        <rss version="2.0">
            <channel>
                <item>
                    <title>Gemini 1.5 Released</title>
                    <link>https://blog.google/gemini</link>
                    <pubDate>Mon, 09 Feb 2026 06:17:00 GMT</pubDate>
                    <source>Google Blog</source>
                </item>
            </channel>
        </rss>
        """
        mock_requests_get.return_value = mock_rss_response

        # 2. Mock Gemini Response (Phase 2)
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        expected_json = {
            "title": "Gemini 1.5 Released",
            "source_name": "Google Blog",
            "published_at": "2026-02-09 15:17", # KST Converted manually for test expectation
            "url": "https://blog.google/gemini",
            "summary": "Google released Gemini 1.5 Pro."
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(expected_json)
        mock_model.generate_content.return_value = mock_response

        # Execute
        results = fetch_grounded_news("Gemini", max_results=1)

        # Assertions
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Gemini 1.5 Released")
        self.assertEqual(results[0]['published_at'], "2026-02-09 15:17")
        
        # Verify calls
        mock_requests_get.assert_called_once() # RSS Fetch
        mock_model.generate_content.assert_called_once() # Gemini Analysis

    @patch('services.gemini_service.requests.get')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_rss_failure(self, mock_requests_get):
        # Mock RSS Failure
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests_get.return_value = mock_response
        
        # Execute
        results = fetch_grounded_news("Gemini")
        
        # Assertions
        self.assertEqual(results, [])

    @patch('services.gemini_service.genai')
    @patch('services.gemini_service.requests.get')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_gemini_analysis_failure(self, mock_requests_get, mock_genai):
        # 1. Mock RSS Success
        mock_rss_response = MagicMock()
        mock_rss_response.status_code = 200
        mock_rss_response.content = b"""
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Article</title>
                    <link>http://example.com</link>
                    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
                    <source>Test Source</source>
                </item>
            </channel>
        </rss>
        """
        mock_requests_get.return_value = mock_rss_response
        
        # 2. Mock Gemini Failure (Exception)
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Simulate an exception during generation or parsing
        mock_model.generate_content.side_effect = Exception("API Error")
        
        # Execute
        results = fetch_grounded_news("Gemini")
        
        # Should return empty list because the only article failed to process
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()
