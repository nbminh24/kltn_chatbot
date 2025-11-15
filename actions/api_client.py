"""
API Client for communicating with Nest.js Backend
Handles all API requests to the e-commerce backend
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Client for interacting with Nest.js Backend API"""
    
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:3001")
        self.api_key = os.getenv("INTERNAL_API_KEY", "")
        self.timeout = 10  # seconds
        
        # Default headers for all requests
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        logger.info(f"BackendAPIClient initialized with base_url: {self.base_url}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to backend API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/internal/products')
            data: Request body data
            params: Query parameters
            auth_token: JWT token for user-specific requests
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        # Add JWT token if provided (for user-specific endpoints)
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return {
                "error": True,
                "message": f"API request failed: {e.response.status_code}",
                "details": e.response.text
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {str(e)}")
            return {
                "error": True,
                "message": f"Connection error: {str(e)}"
            }
    
    # ========================================================================
    # PRODUCT ENDPOINTS
    # ========================================================================
    
    def search_products(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for products by name or description
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of products matching the query
        """
        logger.info(f"Searching products with query: {query}")
        
        params = {
            "search": query,
            "limit": limit
        }
        
        return self._make_request("GET", "/internal/products", params=params)
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific product"""
        logger.info(f"Fetching product details for ID: {product_id}")
        return self._make_request("GET", f"/internal/products/{product_id}")
    
    def check_product_availability(self, product_id: str) -> Dict[str, Any]:
        """Check if a product is in stock"""
        logger.info(f"Checking availability for product ID: {product_id}")
        result = self._make_request("GET", f"/internal/products/{product_id}")
        
        if not result.get("error"):
            return {
                "product_id": product_id,
                "available": result.get("stock", 0) > 0,
                "stock": result.get("stock", 0)
            }
        return result
    
    # ========================================================================
    # FAQ & POLICY ENDPOINTS
    # ========================================================================
    
    def get_page_content(self, slug: str) -> Dict[str, Any]:
        """
        Get content from CMS pages (FAQ, policies, etc.)
        
        Args:
            slug: Page slug (e.g., 'shipping-policy', 'return-policy')
            
        Returns:
            Page content
        """
        logger.info(f"Fetching page content for slug: {slug}")
        return self._make_request("GET", f"/internal/pages/{slug}")
    
    def get_shipping_policy(self) -> Dict[str, Any]:
        """Get shipping policy content"""
        return self.get_page_content("shipping-policy")
    
    def get_return_policy(self) -> Dict[str, Any]:
        """Get return policy content"""
        return self.get_page_content("return-policy")
    
    def get_warranty_policy(self) -> Dict[str, Any]:
        """Get warranty policy content"""
        return self.get_page_content("warranty-policy")
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Get available payment methods"""
        return self.get_page_content("payment-methods")
    
    # ========================================================================
    # ORDER ENDPOINTS (Requires JWT)
    # ========================================================================
    
    def get_order_details(self, order_id: str, auth_token: str) -> Dict[str, Any]:
        """
        Get order details for a specific order
        Requires user authentication
        
        Args:
            order_id: Order ID or order number
            auth_token: User's JWT token
            
        Returns:
            Order details
        """
        logger.info(f"Fetching order details for order: {order_id}")
        return self._make_request(
            "GET", 
            f"/internal/orders/{order_id}", 
            auth_token=auth_token
        )
    
    def get_user_orders(self, auth_token: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get all orders for authenticated user
        
        Args:
            auth_token: User's JWT token
            limit: Maximum number of orders to return
            
        Returns:
            List of user orders
        """
        logger.info("Fetching user orders")
        params = {"limit": limit}
        return self._make_request(
            "GET", 
            "/internal/orders", 
            params=params,
            auth_token=auth_token
        )
    
    # ========================================================================
    # SUPPORT TICKET ENDPOINTS
    # ========================================================================
    
    def create_support_ticket(
        self, 
        subject: str, 
        message: str, 
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Create a support ticket when chatbot cannot help
        This is the fallback mechanism
        
        Args:
            subject: Ticket subject
            message: Ticket message
            user_message: Original user message that triggered fallback
            conversation_history: Recent conversation context
            
        Returns:
            Ticket creation response
        """
        logger.info(f"Creating support ticket with subject: {subject}")
        
        data = {
            "subject": subject,
            "message": message,
            "original_query": user_message,
            "conversation_history": conversation_history or [],
            "source": "chatbot_fallback"
        }
        
        return self._make_request("POST", "/support/tickets", data=data)
    
    def log_fallback(self, user_message: str, intent: str, confidence: float) -> Dict[str, Any]:
        """
        Log messages that chatbot couldn't understand
        Helps improve training data
        
        Args:
            user_message: The message user sent
            intent: Detected intent (if any)
            confidence: Confidence score
            
        Returns:
            Log response
        """
        logger.info(f"Logging fallback for message: {user_message}")
        
        data = {
            "message": user_message,
            "intent": intent,
            "confidence": confidence,
            "timestamp": None  # Backend will add timestamp
        }
        
        return self._make_request("POST", "/internal/chatbot/log-fallback", data=data)

    # ========================================================================
    # ADVANCED BUSINESS LOGIC ENDPOINTS (MOCKED)
    # ========================================================================

    def get_sizing_advice(
        self,
        product_name: str,
        height: str,
        weight: str,
        body_type: str = "",
        fit_preference: str = "",
    ) -> Dict[str, Any]:
        """Get sizing advice from backend based on body metrics and preferences."""
        logger.info(
            f"Requesting sizing advice for product='{product_name}', height='{height}', weight='{weight}', "
            f"body_type='{body_type}', fit_preference='{fit_preference}'"
        )

        data = {
            "product_name": product_name,
            "height": height,
            "weight": weight,
            "body_type": body_type,
            "fit_preference": fit_preference,
        }

        # Mock endpoint – you will implement it in backend later
        return self._make_request("POST", "/internal/chatbot/sizing-advice", data=data)

    def get_styling_advice(
        self,
        garment_to_pair: str,
        occasion: str = "",
    ) -> Dict[str, Any]:
        """Get styling advice (what to pair with a given garment, by occasion)."""
        logger.info(
            f"Requesting styling advice for garment='{garment_to_pair}', occasion='{occasion}'"
        )

        data = {
            "garment_to_pair": garment_to_pair,
            "occasion": occasion,
        }

        return self._make_request("POST", "/internal/chatbot/styling-advice", data=data)

    def get_product_care_info(
        self,
        product_name: str,
        care_property: str = "",
    ) -> Dict[str, Any]:
        """Get care/washing instructions for a product."""
        logger.info(
            f"Requesting product care info for '{product_name}', care_property='{care_property}'"
        )

        data = {
            "product_name": product_name,
            "care_property": care_property,
        }

        return self._make_request("POST", "/internal/chatbot/product-care", data=data)

    def report_order_error(
        self,
        order_number: str,
        error_type: str,
        product_name: str,
        quantity: str,
    ) -> Dict[str, Any]:
        """Report order issues (missing / extra items)."""
        logger.info(
            f"Reporting order error order='{order_number}', error_type='{error_type}', "
            f"product='{product_name}', quantity='{quantity}'"
        )

        data = {
            "order_number": order_number,
            "error_type": error_type,
            "product_name": product_name,
            "quantity": quantity,
        }

        return self._make_request("POST", "/internal/chatbot/order-error", data=data)

    def request_return_or_exchange(
        self,
        order_number: str,
        product_to_return: str,
        reason: str,
        product_to_get: str = "",
    ) -> Dict[str, Any]:
        """Create a return/exchange request for a specific item in an order."""
        logger.info(
            f"Requesting exchange for order='{order_number}', return='{product_to_return}', "
            f"get='{product_to_get}', reason='{reason}'"
        )

        data = {
            "order_number": order_number,
            "product_to_return": product_to_return,
            "product_to_get": product_to_get,
            "reason": reason,
        }

        return self._make_request("POST", "/internal/chatbot/return-or-exchange", data=data)

    def report_quality_issue(
        self,
        product_name: str,
        defect_description: str,
    ) -> Dict[str, Any]:
        """Report quality issues for a product (e.g., defects)."""
        logger.info(
            f"Reporting quality issue for '{product_name}', defect='{defect_description}'"
        )

        data = {
            "product_name": product_name,
            "defect_description": defect_description,
        }

        return self._make_request("POST", "/internal/chatbot/quality-issue", data=data)

    def handle_policy_exception(
        self,
        product_name: str,
        policy_type: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Ask backend to handle a potential policy exception case."""
        logger.info(
            f"Handling policy exception for product='{product_name}', policy='{policy_type}', reason='{reason}'"
        )

        data = {
            "product_name": product_name,
            "policy_type": policy_type,
            "reason": reason,
        }

        return self._make_request("POST", "/internal/chatbot/policy-exception", data=data)

    def set_stock_notification(
        self,
        product_name: str,
        size: str,
        price_condition: str,
        user_id: str = "",
    ) -> Dict[str, Any]:
        """Subscribe user to stock notifications with optional price condition."""
        logger.info(
            f"Setting stock notification for product='{product_name}', size='{size}', "
            f"price_condition='{price_condition}', user_id='{user_id}'"
        )

        data = {
            "product_name": product_name,
            "size": size,
            "price_condition": price_condition,
            "user_id": user_id,
        }

        return self._make_request("POST", "/internal/chatbot/stock-notification", data=data)

    def check_discount(
        self,
        discount_codes: List[str],
        product_name: str = "",
    ) -> Dict[str, Any]:
        """Validate discount codes against cart / product context."""
        logger.info(
            f"Checking discount logic for codes={discount_codes}, product='{product_name}'"
        )

        data = {
            "discount_codes": discount_codes,
            "product_name": product_name,
        }

        return self._make_request("POST", "/internal/chatbot/check-discount", data=data)


# Singleton instance
_api_client = None

def get_api_client() -> BackendAPIClient:
    """Get singleton instance of API client"""
    global _api_client
    if _api_client is None:
        _api_client = BackendAPIClient()
    return _api_client
