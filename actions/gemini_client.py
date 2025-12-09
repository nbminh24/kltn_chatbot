"""
Google Gemini API Client - Simplified Version
Handles intelligent responses for open-ended queries
REFACTORED: Removed complex RAG logic, kept core functionality
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Try to import Gemini, but don't fail if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("⚠️ google-generativeai not installed. Gemini features disabled.")

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiRAGClient:
    """
    Simplified Gemini Client
    No complex RAG logic - just direct API calls
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.model = None
        
        # Check if package is available
        if not GEMINI_AVAILABLE:
            logger.error("❌ google-generativeai package not available")
            return
        
        # Check if API key exists
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY not found in environment")
            return
        
        # Initialize Gemini
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"✅ Gemini {self.model_name} initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            self.model = None
    
    def handle_open_ended_query(self, message: str) -> Dict[str, Any]:
        """
        Simplified method to handle any open-ended query
        Just pass the message to Gemini and return response
        
        Args:
            message: The prompt/message to send to Gemini
            
        Returns:
            Dict with success status and response
        """
        if not self.model:
            return {
                "success": False,
                "response": "AI Module not active."
            }
        
        try:
            # Direct call to Gemini - no complex processing
            response = self.model.generate_content(message)
            
            if response and response.text:
                logger.info(f"✅ Gemini responded: {response.text[:50]}...")
                return {
                    "success": True,
                    "response": response.text
                }
        except Exception as e:
            logger.error(f"❌ Gemini Generation Error: {e}")
        
        return {
            "success": False,
            "response": "Sorry, I lost my train of thought."
        }


# Singleton instance
_gemini_client = None

def get_gemini_client() -> GeminiRAGClient:
    """Get singleton instance of Gemini client"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiRAGClient()
    return _gemini_client
