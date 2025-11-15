"""
Google Gemini API Client for RAG (Retrieval-Augmented Generation)
Handles intelligent responses for out-of-scope queries
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Try to import Gemini, but don't fail if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not installed. RAG features will be disabled.")

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiRAGClient:
    """Client for Google Gemini API with RAG capabilities"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.enabled = os.getenv("ENABLE_RAG", "true").lower() == "true"
        
        if not GEMINI_AVAILABLE:
            logger.warning("google-generativeai package not available. RAG features disabled.")
            self.enabled = False
            return
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. RAG features will be disabled.")
            self.enabled = False
            return
        
        try:
            # Configure Gemini API
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"GeminiRAGClient initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            self.enabled = False
    
    def _build_context_from_products(self, products: List[Dict]) -> str:
        """
        Build context string from product data
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Formatted context string
        """
        if not products:
            return "No product information available."
        
        context_parts = ["Available products:\n"]
        
        for i, product in enumerate(products[:5], 1):  # Limit to 5 products
            context_parts.append(f"{i}. {product.get('name', 'Unknown')}")
            context_parts.append(f"   Price: ${product.get('price', 'N/A')}")
            context_parts.append(f"   Description: {product.get('description', 'N/A')[:100]}...")
            context_parts.append(f"   In Stock: {product.get('stock', 0) > 0}\n")
        
        return "\n".join(context_parts)
    
    def _create_prompt(
        self, 
        user_query: str, 
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Create prompt for Gemini with context
        
        Args:
            user_query: User's question
            context: Retrieved context (products, policies, etc.)
            conversation_history: Recent conversation for continuity
            
        Returns:
            Formatted prompt
        """
        prompt_parts = [
            "You are a helpful e-commerce shopping assistant. Use the provided context to answer the customer's question.",
            "Be friendly, concise, and accurate. If the context doesn't contain relevant information, politely say so.",
            "",
            "Context:",
            context,
            ""
        ]
        
        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("Recent conversation:")
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                text = msg.get("text", "")
                prompt_parts.append(f"{role}: {text}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            f"Customer question: {user_query}",
            "",
            "Your response:"
        ])
        
        return "\n".join(prompt_parts)
    
    def generate_response_with_products(
        self, 
        user_query: str, 
        products: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent response using product context
        
        Args:
            user_query: User's question
            products: Product data for context
            conversation_history: Recent conversation
            
        Returns:
            Generated response with metadata
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "RAG is disabled",
                "response": None
            }
        
        try:
            # Build context from products
            context = self._build_context_from_products(products)
            
            # Create prompt
            prompt = self._create_prompt(user_query, context, conversation_history)
            
            logger.info(f"Generating RAG response for query: {user_query[:50]}...")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "response": response.text,
                "context_used": len(products),
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def generate_response_with_context(
        self, 
        user_query: str, 
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate response with custom context (policies, FAQ, etc.)
        
        Args:
            user_query: User's question
            context: Custom context string
            conversation_history: Recent conversation
            
        Returns:
            Generated response
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "RAG is disabled",
                "response": None
            }
        
        try:
            prompt = self._create_prompt(user_query, context, conversation_history)
            
            logger.info(f"Generating RAG response with custom context")
            
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "response": response.text,
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def handle_open_ended_query(
        self, 
        user_query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Handle open-ended queries without specific context
        Used for general shopping advice, style tips, etc.
        
        Args:
            user_query: User's question
            conversation_history: Recent conversation
            
        Returns:
            Generated response
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "RAG is disabled",
                "response": None
            }
        
        try:
            # Create a prompt for general e-commerce assistance
            prompt_parts = [
                "You are a knowledgeable e-commerce shopping assistant with expertise in fashion, electronics, and general retail.",
                "Provide helpful, friendly advice based on the customer's question.",
                "Keep responses concise (2-3 sentences) and actionable.",
                ""
            ]
            
            if conversation_history:
                prompt_parts.append("Recent conversation:")
                for msg in conversation_history[-3:]:
                    role = msg.get("role", "user")
                    text = msg.get("text", "")
                    prompt_parts.append(f"{role}: {text}")
                prompt_parts.append("")
            
            prompt_parts.extend([
                f"Customer question: {user_query}",
                "",
                "Your helpful response:"
            ])
            
            prompt = "\n".join(prompt_parts)
            
            logger.info(f"Handling open-ended query: {user_query[:50]}...")
            
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "response": response.text,
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error handling open-ended query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }


# Singleton instance
_gemini_client = None

def get_gemini_client() -> GeminiRAGClient:
    """Get singleton instance of Gemini client"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiRAGClient()
    return _gemini_client
