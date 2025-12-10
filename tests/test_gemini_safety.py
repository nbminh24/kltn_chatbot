"""
Test Suite for Gemini AI Safety Mechanisms
Tests to validate academic-grade safety implementation
"""

import pytest
from actions.actions import validate_gemini_response, GEMINI_SYSTEM_PROMPT


class TestGeminiValidation:
    """Test response validation filter"""
    
    def test_safe_fashion_advice(self):
        """Test that valid fashion advice passes validation"""
        response = "Cotton is breathable and great for summer. It's comfortable and easy to care for."
        user_msg = "What's cotton fabric like?"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        assert is_valid == True
        assert safe_response == response
    
    def test_blocks_price_mention(self):
        """Test that price mentions are blocked"""
        response = "This shirt costs around $25-30 and is very affordable."
        user_msg = "How much is this shirt?"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        assert is_valid == False
        assert "check our store system" in safe_response
    
    def test_blocks_stock_mention(self):
        """Test that stock mentions are blocked"""
        response = "Yes, this item is in stock and available for purchase."
        user_msg = "Is this available?"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        assert is_valid == False
    
    def test_blocks_order_status(self):
        """Test that order status mentions are blocked"""
        response = "Your order is being processed and will ship tomorrow."
        user_msg = "Where is my order?"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        assert is_valid == False
    
    def test_blocks_promotion(self):
        """Test that promotion mentions are blocked"""
        response = "There's a 20% discount on all items this week!"
        user_msg = "Any sales?"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        assert is_valid == False


class TestSystemPrompt:
    """Test system prompt structure"""
    
    def test_prompt_has_restrictions(self):
        """Verify system prompt contains forbidden topics"""
        assert "CANNOT answer" in GEMINI_SYSTEM_PROMPT
        assert "price" in GEMINI_SYSTEM_PROMPT
        assert "stock" in GEMINI_SYSTEM_PROMPT
        assert "order" in GEMINI_SYSTEM_PROMPT
    
    def test_prompt_defines_allowed_scope(self):
        """Verify system prompt defines allowed topics"""
        assert "fashion" in GEMINI_SYSTEM_PROMPT.lower()
        assert "style advice" in GEMINI_SYSTEM_PROMPT.lower()
        assert "material knowledge" in GEMINI_SYSTEM_PROMPT.lower()


class TestForbiddenKeywords:
    """Test all forbidden keyword categories"""
    
    @pytest.mark.parametrize("keyword,user_question", [
        # Price-related
        ("price", "What's the price?"),
        ("cost", "How much does it cost?"),
        ("$25", "It's $25"),
        ("cheap", "This is cheap"),
        
        # Stock-related
        ("in stock", "Is it in stock?"),
        ("sold out", "It's sold out"),
        ("available", "This is available now"),
        
        # Order-related
        ("tracking", "Order tracking number"),
        ("shipped", "It has shipped"),
        ("delivery", "Delivery time is 2 days"),
        
        # Promotion-related
        ("discount", "20% discount"),
        ("sale", "On sale now"),
        ("promotion", "Special promotion"),
    ])
    def test_blocks_forbidden_keyword(self, keyword, user_question):
        """Test that each forbidden keyword is caught"""
        response = f"Sure! The item has {keyword} information."
        
        is_valid, safe_response = validate_gemini_response(response, user_question)
        
        assert is_valid == False, f"Should block keyword: {keyword}"


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_empty_response(self):
        """Test handling of empty response"""
        response = ""
        user_msg = "Hello?"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        assert is_valid == True  # Empty is technically safe
    
    def test_very_long_response(self):
        """Test handling of very long response"""
        response = "Cotton fabric " * 1000  # Very long but safe
        user_msg = "Tell me about cotton"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        assert is_valid == True
    
    def test_mixed_safe_and_unsafe(self):
        """Test response with both safe and unsafe content"""
        response = "Cotton is great for summer. Prices start from $20."
        user_msg = "What about cotton?"
        
        is_valid, safe_response = validate_gemini_response(response, user_msg)
        
        # Should still block due to price mention
        assert is_valid == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
