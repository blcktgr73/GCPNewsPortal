
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json

# Adjust path to include news_summarizer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'news_summarizer'))

from services.gemini_service import fetch_grounded_news

class TestGeminiService(unittest.TestCase):

    @patch('services.gemini_service.genai')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_fetch_grounded_news_success(self, mock_genai):
        # Mocking the model
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        # Phase 1 Response (Text)
        mock_response_p1 = MagicMock()
        mock_response_p1.text = """
        Report:
        1. Title: Gemini 1.5 Released
           Source: Google Blog
           Date: 2024-02-15
           Link: https://blog.google/gemini
           Summary: Google released Gemini 1.5 Pro.
        """
        
        # Phase 2 Response (JSON)
        mock_response_p2 = MagicMock()
        mock_response_p2.text = json.dumps([
            {
                "title": "Gemini 1.5 Released",
                "source_name": "Google Blog",
                "published_at": "2024-02-15",
                "url": "https://blog.google/gemini",
                "summary": "Google released Gemini 1.5 Pro."
            }
        ])
        
        # Configure side_effect for generate_content to return different responses for Phase 1 and Phase 2
        # First call is Phase 1, second call is Phase 2.
        # However, the code creates NEW model instances for each phase.
        # So GenerativeModel() is called twice.
        
        # We need to ensure that the mocked instances return the correct response.
        # Since GenerativeModel is called twice, side_effect on the constructor can return different mocks.
        
        mock_model_p1 = MagicMock()
        mock_model_p1.generate_content.return_value = mock_response_p1
        
        mock_model_p2 = MagicMock()
        mock_model_p2.generate_content.return_value = mock_response_p2
        
        mock_genai.GenerativeModel.side_effect = [mock_model_p1, mock_model_p2]

        # Execute
        results = fetch_grounded_news("Gemini", max_results=1)

        # Assertions
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Gemini 1.5 Released")
        self.assertEqual(results[0]['source_name'], "Google Blog")
        
        # Verify calls
        # Check that proper tools were passed in Phase 1
        call_args_p1 = mock_genai.GenerativeModel.call_args_list[0]
        _, kwargs_p1 = call_args_p1
        self.assertIn('tools', kwargs_p1)
        self.assertEqual(kwargs_p1['tools'], [{'google_search': {}}])
        
        # Check that response_mime_type was set in Phase 2
        call_args_p2 = mock_genai.GenerativeModel.call_args_list[1]
        _, kwargs_p2 = call_args_p2
        self.assertIn('generation_config', kwargs_p2)
        self.assertEqual(kwargs_p2['generation_config']['response_mime_type'], 'application/json')

    @patch('services.gemini_service.genai')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_fetch_grounded_news_phase1_failure(self, mock_genai):
        # Mocking the model to raise exception in Phase 1
        mock_genai.GenerativeModel.side_effect = Exception("Phase 1 Init Failed")
        
        # Execute
        results = fetch_grounded_news("Gemini")
        
        # Assertions
        self.assertEqual(results, [])

    @patch('services.gemini_service.genai')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_fetch_grounded_news_phase2_failure(self, mock_genai):
        mock_model_p1 = MagicMock()
        mock_model_p1.generate_content.return_value.text = "Some news text"
        
        mock_model_p2 = MagicMock()
        # Phase 2 raises exception during generation
        mock_model_p2.generate_content.side_effect = Exception("JSON Parsing Failed")
        
        mock_genai.GenerativeModel.side_effect = [mock_model_p1, mock_model_p2]
        
        results = fetch_grounded_news("Gemini")
        self.assertEqual(results, [])

    @patch('services.gemini_service.genai')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_fetch_grounded_news_phase2_invalid_json(self, mock_genai):
        mock_model_p1 = MagicMock()
        mock_model_p1.generate_content.return_value.text = "Some news text"
        
        mock_model_p2 = MagicMock()
        # Phase 2 returns broken JSON
        mock_model_p2.generate_content.return_value.text = "Not a JSON"
        
        mock_genai.GenerativeModel.side_effect = [mock_model_p1, mock_model_p2]
        
        results = fetch_grounded_news("Gemini")
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()
