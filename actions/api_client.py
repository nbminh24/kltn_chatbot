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
        self.timeout = 5  # seconds - reduced for faster response
        
        # Create session with connection pooling for better performance
        self.session = requests.Session()
        
        # Default headers for all requests
        # Backend has TWO different guards:
        # 1. ApiKeyGuard (for /internal/* endpoints) - expects x-api-key
        # 2. InternalApiKeyGuard (for /api/chatbot/* endpoints) - expects X-Internal-Api-Key
        # Send BOTH headers to satisfy both guards
        self.headers = {
            "x-api-key": self.api_key,              # For /internal/* endpoints
            "X-Internal-Api-Key": self.api_key,     # For /api/chatbot/* endpoints
            "Content-Type": "application/json"
        }
        
        # Log API key status (first 10 chars only for security)
        if self.api_key:
            logger.info(f"✅ BackendAPIClient initialized with base_url: {self.base_url}, API key: {self.api_key[:10]}...")
        else:
            logger.error(f"❌ INTERNAL_API_KEY is EMPTY! Backend will return 401. Set INTERNAL_API_KEY in .env file.")
    
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
            logger.info(f"🔐 Sending request with JWT token (first 20 chars): {auth_token[:20]}...")
        else:
            logger.warning("⚠️ No auth_token provided for this request")
        
        # Debug: Log request details
        logger.info(f"📤 {method} {url}")
        logger.info(f"📋 Query params: {params}")
        logger.info(f"🔑 Headers: {list(headers.keys())}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"📥 Response status: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP Error: {e.response.status_code}")
            logger.error(f"❌ Response body: {e.response.text}")
            logger.error(f"❌ Request URL: {url}")
            logger.error(f"❌ Request headers sent: {list(headers.keys())}")
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
    
    def search_products(
        self, 
        query: str = None, 
        limit: int = 10, 
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        colors: List[str] = None,
        sizes: List[str] = None,
        in_stock: bool = None
    ) -> Dict[str, Any]:
        """
        Search for products using chatbot API endpoint
        Uses GET /api/chatbot/products/search with query parameters
        
        Args:
            query: Search query
            limit: Maximum number of results
            category: Category slug filter (not used in current implementation)
            min_price: Minimum price (not used in current implementation)
            max_price: Maximum price (not used in current implementation)
            colors: List of color names (not used in current implementation)
            sizes: List of size names (not used in current implementation)
            in_stock: Only in-stock products (not used in current implementation)
            
        Returns:
            Dict with 'data' containing products list and metadata
        """
        logger.info(f"Searching products with query: {query}, limit: {limit}")
        
        # Build query parameters for chatbot search endpoint
        params = {}
        
        if query:
            params["query"] = query
        if limit:
            params["limit"] = limit
        
        # Use chatbot search endpoint that returns correct results
        return self._make_request("GET", "/api/chatbot/products/search", params=params)
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific product - Public API"""
        logger.info(f"Fetching product details for ID: {product_id}")
        return self._make_request("GET", f"/products/id/{product_id}")
    
    def check_product_availability(self, product_name: str = None, size: str = None, color: str = None) -> Dict[str, Any]:
        """
        Check product availability with filters - Public API
        Endpoint: GET /products/availability?name={}&size={}&color={}
        """
        logger.info(f"Checking availability: name={product_name}, size={size}, color={color}")
        
        params = {}
        if product_name:
            params["name"] = product_name
        if size:
            params["size"] = size
        if color:
            params["color"] = color
        
        return self._make_request("GET", "/products/availability", params=params)
    
    # ========================================================================
    # FAQ & POLICY ENDPOINTS
    # ========================================================================
    
    def get_page_content(self, slug: str) -> Dict[str, Any]:
        """
        Get content from CMS pages (FAQ, policies, etc.) - Public API
        
        Args:
            slug: Page slug (e.g., 'shipping-policy', 'return-policy')
            
        Returns:
            Page content
        """
        logger.info(f"Fetching page content for slug: {slug}")
        return self._make_request("GET", f"/pages/{slug}")
    
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
    
    def get_order_details(self, order_id: str, auth_token: str = None) -> Dict[str, Any]:
        """
        Get order details for a specific order - Public track endpoint
        Can use order tracking: GET /orders/track?order_id={}
        
        Args:
            order_id: Order ID or order number
            auth_token: Optional user's JWT token
            
        Returns:
            Order details
        """
        logger.info(f"Fetching order details for order: {order_id}")
        params = {"order_id": order_id}
        return self._make_request(
            "GET", 
            "/orders/track", 
            params=params,
            auth_token=auth_token
        )
    
    def get_user_orders(self, auth_token: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get all orders for authenticated user.
        Backend endpoint: GET /orders (with JWT)
        
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
            "/orders", 
            params=params,
            auth_token=auth_token
        )
    
    def get_delivery_estimation(self, order_id: str, auth_token: str = None) -> Dict[str, Any]:
        """
        Get delivery estimation for an order.
        Backend endpoint: GET /orders/track/delivery-estimation?order_id={}
        
        Args:
            order_id: Order number (e.g., "0000000032")
            auth_token: User's JWT token
            
        Returns:
            Dictionary containing delivery estimation data including:
            - status, shipping_method, destination
            - estimated_delivery: {from, to, date, formatted}
            - tracking_url
        """
        logger.info(f"Fetching delivery estimation for order: {order_id}")
        params = {"order_id": order_id}
        return self._make_request(
            "GET",
            "/orders/track/delivery-estimation",
            params=params,
            auth_token=auth_token
        )
    
    def cancel_order(self, order_id: str, cancel_reason: str, auth_token: str = None) -> Dict[str, Any]:
        """
        Cancel an order with a specified reason.
        Backend endpoint: POST /orders/{order_id}/cancel
        
        Only allowed when order status is 'pending'.
        Backend will validate and return appropriate error for other statuses.
        
        Args:
            order_id: Order ID (numeric, e.g., "32")
            cancel_reason: Reason for cancellation (enum value)
            auth_token: User's JWT token
            
        Valid cancel_reason values:
            - changed_mind
            - ordered_wrong_item
            - wrong_size_color
            - found_better_price
            - delivery_too_slow
            - payment_issue
            - duplicate_order
            - other
            
        Returns:
            Success: { "success": true, "order": {...} }
            Error: { "success": false, "error": "...", "suggestion": "..." }
        """
        logger.info(f"Cancelling order {order_id} with reason: {cancel_reason}")
        
        payload = {"cancel_reason": cancel_reason}
        
        return self._make_request(
            "POST",
            f"/orders/{order_id}/cancel",
            json_data=payload,
            auth_token=auth_token
        )
    
    def search_purchased_products(self, product_name: str, auth_token: str) -> Dict[str, Any]:
        """
        Search products from user's purchase history.
        Better UX: users ask about products they bought, not order IDs.
        Real endpoint: GET /internal/orders (filter by product in results)
        
        Args:
            product_name: Product name to search for
            auth_token: User's JWT token
            
        Returns:
            Orders containing the product
        """
        logger.info(f"Searching purchased products: {product_name}")
        
        # Get user orders
        result = self.get_user_orders(auth_token, limit=50)
        
        if result.get("error"):
            return result
        
        orders = result.get("data", [])
        matching_orders = []
        
        # Filter orders containing the product
        for order in orders:
            items = order.get("items", [])
            for item in items:
                item_name = item.get("product_name", "").lower()
                if product_name.lower() in item_name:
                    matching_orders.append({
                        "order_id": order.get("id"),
                        "order_number": order.get("order_number"),
                        "product": item.get("product_name"),
                        "status": order.get("status"),
                        "date": order.get("created_at")
                    })
                    break
        
        return {
            "data": matching_orders,
            "count": len(matching_orders)
        }
    
    # ========================================================================
    # SUPPORT TICKET ENDPOINTS  
    # ========================================================================
    
    def create_support_ticket(
        self, 
        subject: str, 
        message: str, 
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        auth_token: Optional[str] = None,
        customer_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a support ticket when chatbot cannot help.
        Backend handles this through admin module.
        Note: Endpoint might need to be confirmed with backend team.
        
        Args:
            subject: Ticket subject
            message: Ticket message/description
            user_message: Original user message that triggered fallback
            conversation_history: Recent conversation context
            auth_token: Optional JWT token if user is authenticated
            customer_email: Optional email if guest user
            
        Returns:
            Ticket creation response
        """
        logger.info(f"Creating support ticket with subject: {subject}")
        
        data = {
            "subject": subject,
            "message": message,
            "source": "chatbot",
            "priority": "normal"
        }
        
        if customer_email:
            data["customer_email"] = customer_email
        
        # Note: Using generic /support-tickets endpoint
        # Backend team should confirm the exact endpoint
        return self._make_request("POST", "/support-tickets", data=data, auth_token=auth_token)
    
    def log_fallback(self, user_message: str, intent: str, confidence: float) -> Dict[str, Any]:
        """
        Log messages that chatbot couldn't understand
        Helps improve training data
        Note: This endpoint may not exist yet - optional feature
        
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
            "source": "chatbot_fallback"
        }
        
        # This endpoint might need to be created by backend team
        return self._make_request("POST", "/api/chatbot/log-fallback", data=data)

    # ========================================================================
    # CHATBOT-SPECIFIC ENDPOINTS (Internal APIs - Require X-Internal-Api-Key)
    # ========================================================================
    
    def add_to_cart(self, customer_id: int, variant_id: int, quantity: int = 1) -> Dict[str, Any]:
        """
        Add item to cart using internal chatbot API
        Endpoint: POST /api/chatbot/cart/add
        Requires: X-Internal-Api-Key header
        
        Args:
            customer_id: Customer ID
            variant_id: Product variant ID
            quantity: Quantity to add
            
        Returns:
            Cart update response
        """
        logger.info(f"Adding to cart: customer={customer_id}, variant={variant_id}, qty={quantity}")
        
        data = {
            "customer_id": customer_id,
            "variant_id": variant_id,
            "quantity": quantity
        }
        
        return self._make_request("POST", "/api/chatbot/cart/add", data=data)
    
    def get_cart(self, customer_id: int) -> Dict[str, Any]:
        """
        Get cart by customer ID using internal chatbot API
        Endpoint: GET /api/chatbot/cart/:customer_id
        Requires: X-Internal-Api-Key header
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Cart data with items, subtotal, and total
            {
                "success": true,
                "data": {
                    "customer_id": 123,
                    "items": [...],
                    "total_items": 2,
                    "subtotal": 300000,
                    "total": 300000
                }
            }
        """
        logger.info(f"Getting cart for customer: {customer_id}")
        return self._make_request("GET", f"/api/chatbot/cart/{customer_id}")
    
    def verify_token(self, jwt_token: str) -> Dict[str, Any]:
        """
        Verify JWT token and get customer information
        Endpoint: POST /api/chatbot/auth/verify
        Requires: X-Internal-Api-Key header
        
        Args:
            jwt_token: JWT token from frontend
            
        Returns:
            Customer information
            {
                "success": true,
                "data": {
                    "customer_id": 123,
                    "email": "user@example.com",
                    "name": "John Doe"
                }
            }
        """
        logger.info(f"Verifying JWT token: {jwt_token[:20]}...")
        
        data = {
            "jwt_token": jwt_token
        }
        
        return self._make_request("POST", "/api/chatbot/auth/verify", data=data)
    
    def add_to_wishlist(self, customer_id: int, variant_id: int) -> Dict[str, Any]:
        """
        Add item to wishlist using internal chatbot API
        Endpoint: POST /api/chatbot/wishlist/add
        Requires: X-Internal-Api-Key header
        
        Args:
            customer_id: Customer ID
            variant_id: Product variant ID
            
        Returns:
            Wishlist update response
        """
        logger.info(f"Adding to wishlist: customer={customer_id}, variant={variant_id}")
        
        data = {
            "customer_id": customer_id,
            "variant_id": variant_id
        }
        
        return self._make_request("POST", "/api/chatbot/wishlist/add", data=data)
    
    def cancel_order(self, order_id: int, customer_id: int, cancel_reason: str = "other") -> Dict[str, Any]:
        """
        Cancel order using internal chatbot API
        Endpoint: POST /api/chatbot/orders/:id/cancel
        Requires: X-Internal-Api-Key header
        
        Args:
            order_id: Order ID to cancel
            customer_id: Customer ID (for verification)
            cancel_reason: Reason for cancellation (enum: changed_mind, ordered_wrong_item, 
                          wrong_size_color, found_better_price, delivery_too_slow, 
                          payment_issue, duplicate_order, other)
            
        Returns:
            Order cancellation response with status-based suggestions
        """
        logger.info(f"Cancelling order: order_id={order_id}, customer_id={customer_id}, reason={cancel_reason}")
        
        data = {
            "customer_id": customer_id,
            "cancel_reason": cancel_reason
        }
        
        return self._make_request("POST", f"/api/chatbot/orders/{order_id}/cancel", data=data)
    
    def request_handoff(self, session_id: int) -> Dict[str, Any]:
        """
        Request human handoff for a chat session
        Endpoint: POST /api/v1/chat/handoff
        Requires: X-Internal-Api-Key header
        
        Args:
            session_id: Chat session ID
            
        Returns:
            Handoff request result
        """
        logger.info(f"Requesting human handoff for session: {session_id}")
        
        data = {
            "session_id": session_id,
            "reason": "customer_request"
        }
        
        return self._make_request("POST", "/api/v1/chat/handoff", data=data)
    
    def get_size_chart(self, category: str) -> Dict[str, Any]:
        """
        Get size chart for product category
        Endpoint: GET /api/chatbot/size-chart/:category
        Categories: shirt, pants, shoes
        Requires: X-Internal-Api-Key header
        
        Args:
            category: Product category (shirt, pants, shoes)
            
        Returns:
            Size chart image URL and description
        """
        logger.info(f"Getting size chart for category: {category}")
        
        return self._make_request("GET", f"/api/chatbot/size-chart/{category}")
    
    def get_sizing_advice(
        self,
        height: int,
        weight: int,
        category: str = "shirt"
    ) -> Dict[str, Any]:
        """
        Get personalized size recommendation
        Endpoint: POST /api/chatbot/size-advice
        Requires: X-Internal-Api-Key header
        
        Args:
            height: Height in cm
            weight: Weight in kg
            category: Product category (shirt, pants, shoes)
            
        Returns:
            Size recommendation with confidence and reasoning
        """
        logger.info(f"Getting size advice: height={height}cm, weight={weight}kg, category={category}")

        data = {
            "height": height,
            "weight": weight,
            "category": category
        }

        return self._make_request("POST", "/api/chatbot/size-advice", data=data)
    
    def get_product_recommendations(
        self,
        context: str = None,
        category: str = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get product recommendations based on context/occasion
        Endpoint: GET /api/chatbot/products/recommend
        Contexts: wedding, beach, work, party, casual, sport
        Requires: X-Internal-Api-Key header
        
        Args:
            context: Occasion/context (wedding, beach, work, party, casual, sport)
            category: Product category filter (optional)
            limit: Max number of recommendations (default 5, max 20)
            
        Returns:
            Product recommendations
        """
        logger.info(f"Getting recommendations: context={context}, category={category}, limit={limit}")
        
        params = {"limit": limit}
        if context:
            params["context"] = context
        if category:
            params["category"] = category
        
        return self._make_request("GET", "/api/chatbot/products/recommend", params=params)
    
    def ask_gemini(self, question: str) -> Dict[str, Any]:
        """
        Ask Google Gemini AI for general fashion questions
        Endpoint: POST /api/chatbot/gemini/ask
        Requires: X-Internal-Api-Key header
        
        Args:
            question: User's question
            
        Returns:
            AI-generated answer
        """
        logger.info(f"Asking Gemini AI: {question}")
        
        data = {
            "question": question
        }
        
        return self._make_request("POST", "/api/chatbot/gemini/ask", data=data)

    # ========================================================================
    # ADVANCED BUSINESS LOGIC ENDPOINTS (LEGACY - May need update)
    # ========================================================================

    def get_styling_advice(
        self,
        product_id: str,
    ) -> Dict[str, Any]:
        """
        Get styling rules/advice for a product.
        Real endpoint: GET /internal/products/{id}/styling-rules
        """
        logger.info(f"Requesting styling advice for product_id='{product_id}'")
        return self._make_request("GET", f"/internal/products/{product_id}/styling-rules")

    def get_product_care_info(
        self,
        product_id: str,
    ) -> Dict[str, Any]:
        """
        Get care/washing instructions for a product.
        Uses the product details endpoint which includes care instructions.
        Real endpoint: GET /internal/products/{id}
        """
        logger.info(f"Requesting product care info for product_id='{product_id}'")
        result = self.get_product_by_id(product_id)
        
        # Extract care instructions from product details
        if not result.get("error"):
            care_instructions = result.get("care_instructions") or result.get("data", {}).get("care_instructions")
            if care_instructions:
                return {"care": care_instructions}
        
        return result

    def report_order_error(
        self,
        order_number: str,
        error_type: str,
        product_name: str,
        quantity: str,
        user_message: str = "",
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Report order issues (missing / extra items).
        Real endpoint: POST /internal/support/create-ticket
        """
        logger.info(
            f"Reporting order error order='{order_number}', error_type='{error_type}', "
            f"product='{product_name}', quantity='{quantity}'"
        )

        subject = f"Order Error: {error_type} - Order #{order_number}"
        message = (
            f"Order error reported:\n"
            f"- Order Number: {order_number}\n"
            f"- Error Type: {error_type}\n"
            f"- Product: {product_name}\n"
            f"- Quantity: {quantity}\n\n"
            f"Original message: {user_message}"
        )

        return self.create_support_ticket(
            subject=subject,
            message=message,
            user_message=user_message,
            auth_token=auth_token
        )

    def request_return_or_exchange(
        self,
        order_number: str,
        product_to_return: str,
        reason: str,
        product_to_get: str = "",
        user_message: str = "",
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a return/exchange request for a specific item in an order.
        Real endpoint: POST /internal/support/create-ticket
        """
        logger.info(
            f"Requesting exchange for order='{order_number}', return='{product_to_return}', "
            f"get='{product_to_get}', reason='{reason}'"
        )

        subject = f"Return/Exchange Request - Order #{order_number}"
        message = (
            f"Return/Exchange request:\n"
            f"- Order Number: {order_number}\n"
            f"- Product to Return: {product_to_return}\n"
            f"- Product to Get: {product_to_get or 'N/A (Return only)'}\n"
            f"- Reason: {reason}\n\n"
            f"Original message: {user_message}"
        )

        return self.create_support_ticket(
            subject=subject,
            message=message,
            user_message=user_message,
            auth_token=auth_token
        )

    def report_quality_issue(
        self,
        product_name: str,
        defect_description: str,
        user_message: str = "",
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Report quality issues for a product (e.g., defects).
        Real endpoint: POST /internal/support/create-ticket
        """
        logger.info(
            f"Reporting quality issue for '{product_name}', defect='{defect_description}'"
        )

        subject = f"Quality Issue: {product_name}"
        message = (
            f"Quality issue reported:\n"
            f"- Product: {product_name}\n"
            f"- Defect Description: {defect_description}\n\n"
            f"Original message: {user_message}"
        )

        return self.create_support_ticket(
            subject=subject,
            message=message,
            user_message=user_message,
            auth_token=auth_token
        )

    def handle_policy_exception(
        self,
        product_name: str,
        policy_type: str,
        reason: str,
        user_message: str = "",
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ask backend to handle a potential policy exception case.
        Real endpoint: POST /internal/support/create-ticket
        """
        logger.info(
            f"Handling policy exception for product='{product_name}', policy='{policy_type}', reason='{reason}'"
        )

        subject = f"Policy Exception Request: {policy_type}"
        message = (
            f"Policy exception request:\n"
            f"- Product: {product_name}\n"
            f"- Policy Type: {policy_type}\n"
            f"- Reason: {reason}\n\n"
            f"Original message: {user_message}"
        )

        return self.create_support_ticket(
            subject=subject,
            message=message,
            user_message=user_message,
            auth_token=auth_token
        )

    def set_stock_notification(
        self,
        product_id: str,
        variant_id: str,
        auth_token: str,
    ) -> Dict[str, Any]:
        """
        Subscribe user to stock notifications.
        Real endpoint: POST /internal/notifications/subscribe
        Requires JWT authentication - user_id derived from token
        """
        logger.info(
            f"Setting stock notification for product_id='{product_id}', variant_id='{variant_id}'"
        )

        data = {
            "product_id": product_id,
            "variant_id": variant_id,
            "notification_type": "stock_alert"
        }

        return self._make_request("POST", "/internal/notifications/subscribe", data=data, auth_token=auth_token)

    def get_top_discounts(
        self,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get top discounted products (no discount codes used).
        Real endpoint: GET /internal/promotions/top-discounts
        """
        logger.info(f"Fetching top {limit} discounted products")
        params = {"limit": limit}
        return self._make_request("GET", "/internal/promotions/top-discounts", params=params)
    
    # ========================================================================
    # GEMINI AI LOGGING (For Academic Evaluation)
    # ========================================================================
    
    def log_gemini_call(
        self,
        user_message: str,
        rasa_intent: str,
        rasa_confidence: float,
        gemini_response: str,
        response_time_ms: int,
        is_validated: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log Gemini AI calls for academic evaluation and auditing.
        
        This logging is CRITICAL for the thesis defense to show:
        - How often Gemini is called (should be low %)
        - What types of queries trigger Gemini
        - That Gemini never handles business data
        
        Args:
            user_message: Original user question
            rasa_intent: Intent detected by Rasa
            rasa_confidence: Confidence score from Rasa
            gemini_response: Response from Gemini (validated)
            response_time_ms: Response time in milliseconds
            is_validated: Whether response passed safety validation
            metadata: Additional metadata (with_history, fallback, etc.)
            
        Returns:
            Backend response (success/error)
        """
        logger.info(f"📊 Logging Gemini call: intent={rasa_intent}, confidence={rasa_confidence:.2f}")
        
        data = {
            "user_message": user_message[:500],  # Truncate long messages
            "rasa_intent": rasa_intent,
            "rasa_confidence": rasa_confidence,
            "gemini_response": gemini_response[:1000],  # Truncate long responses
            "response_time_ms": response_time_ms,
            "is_validated": is_validated,
            "metadata": metadata or {}
        }
        
        # Try to log to backend (non-critical, don't fail if backend offline)
        try:
            return self._make_request(
                "POST",
                "/api/chatbot/gemini/log",
                data=data
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to log Gemini call to backend (non-critical): {e}")
            return {"success": False, "error": "Backend logging unavailable"}


# Singleton instance
_api_client = None

def get_api_client() -> BackendAPIClient:
    """Get singleton instance of API client"""
    global _api_client
    if _api_client is None:
        _api_client = BackendAPIClient()
    return _api_client
