"""
Custom Actions for KLTN E-commerce Chatbot
Implements all business logic for chatbot interactions
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import logging
import time
import re

from .api_client import get_api_client
from .gemini_client import get_gemini_client
from .action_delivery_status import ActionGetDeliveryStatus

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_customer_id_from_tracker(tracker: Tracker) -> int:
    """
    Extract customer_id from tracker using multiple strategies:
    1. Check metadata.customer_id (preferred - sent by backend)
    2. Check slot customer_id
    3. Verify JWT token if available
    
    Args:
        tracker: Rasa tracker object
        
    Returns:
        customer_id (int) or None if not authenticated
    """
    # Strategy 1: Get from message metadata (sent by backend/frontend)
    metadata = tracker.latest_message.get("metadata", {})
    customer_id = metadata.get("customer_id")
    
    if customer_id:
        logger.info(f"✅ Got customer_id from metadata: {customer_id}")
        return int(customer_id)
    
    # Strategy 2: Get from slot (set in previous conversation)
    customer_id = tracker.get_slot("customer_id")
    if customer_id:
        logger.info(f"✅ Got customer_id from slot: {customer_id}")
        return int(customer_id)
    
    # Strategy 3: Verify JWT token if available
    jwt_token = metadata.get("user_jwt_token")
    if jwt_token:
        try:
            api_client = get_api_client()
            result = api_client.verify_token(jwt_token)
            
            if result.get("success") and result.get("data"):
                customer_id = result["data"].get("customer_id")
                logger.info(f"✅ Got customer_id from JWT verification: {customer_id}")
                return int(customer_id)
            else:
                logger.warning(f"⚠️ JWT verification failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"❌ JWT verification error: {e}")
    
    logger.warning("⚠️ No customer_id found - user not authenticated")
    return None


# ============================================================================
# GEMINI AI SAFETY - System Prompts & Validation
# ============================================================================

# CRITICAL: Gemini is ONLY for fashion knowledge, NOT business data
GEMINI_SYSTEM_PROMPT = """You are LeCas Virtual Shopping Assistant - representing a pioneering menswear brand founded in 2025.

BRAND IDENTITY:
- Brand: LeCas - Redefining casual male fashion
- Slogan: "Casually Elegant Every Moment"
- Focus: Premium menswear essentials for the modern man who believes in subtle power dressing
- Core Values: Quality First, Customer Focused, Authenticity, Sustainability
- Tone: Professional yet friendly, confident, sophisticated but approachable

YOUR ROLE: Fashion Knowledge Consultant

YOU CAN answer about:
- General fashion style advice (how to match clothes, color coordination)
- Material knowledge and care (cotton, polyester, denim, wool properties)
- Body type and fit guidance for menswear (slim fit vs regular, what suits different shapes)
- Fashion trends for modern men (seasonal trends, classic styles)
- Styling for different occasions (casual, formal, business, smart casual)
- General wardrobe building and clothing care tips

REDIRECT to our system for:
- Specific product prices or costs
- Stock availability
- Order status or tracking
- Shipping times or delivery information
- Store promotions, discounts, or coupon codes
- Specific product details from our inventory
- Product comparisons from our store catalog

RESPONSE STYLE:
- Be confident and reassuring (use phrases like Absolutely, Best of all)
- Sound sophisticated yet effortless (match Casually Elegant philosophy)
- Keep responses concise (2-3 sentences)
- Use structured format when listing (bullet points)
- Subtle emoji use (1-2 maximum, not excessive)
- Show expertise while being helpful and supportive

CRITICAL: If asked about forbidden topics, say: I do not have access to that specific information from our store system. Let me connect you with our product database to get accurate details.

Keep responses concise (2-3 sentences), friendly, and helpful within your allowed scope."""


def validate_gemini_response(response_text: str, user_message: str) -> tuple[bool, str]:
    """
    Validate that Gemini response doesn't violate safety policies.
    
    This function prevents Gemini from hallucinating business data like:
    - Product prices
    - Stock information
    - Order details
    - Shipping policies
    
    Args:
        response_text: The response from Gemini
        user_message: Original user message (for context)
        
    Returns:
        (is_valid, safe_response): 
            - is_valid: True if response is safe, False if violated
            - safe_response: Original text or filtered fallback message
    """
    # Keywords that indicate Gemini is answering forbidden topics
    # Use word boundaries to avoid false positives
    FORBIDDEN_PATTERNS = [
        # Price-related (with context)
        r'\$\d+', r'₫\d+', r'\d+\s*vnd', r'\d+\s*dollar', r'\d+\s*usd',
        r'\bprice\s+is\b', r'\bcosts?\s+\d+', r'\bfor\s+\$', 
        r'\bcheap\s+at\b', r'\bexpensive\s+at\b',
        
        # Stock-related (precise phrases)
        r'\bin\s+stock\b', r'\bout\s+of\s+stock\b', 
        r'\bsold\s+out\b', r'\binventory\s+(is|has)\b',
        
        # Order-related (with context)
        r'\border\s+status\b', r'\btracking\s+number\b', 
        r'\bshipped\s+on\b', r'\bdelivery\s+date\b',
        r'\bwill\s+arrive\b', r'\bprocessing\s+your\b',
        
        # Promotion-related (precise phrases)
        r'\d+%\s*off\b', r'\bdiscount\s+code\b', 
        r'\bpromotion\s+(ends|starts)\b', r'\bcoupon\s+code\b',
        r'\bspecial\s+offer\b', r'\bon\s+sale\b',
    ]
    
    response_lower = response_text.lower()
    
    # Check for forbidden patterns using regex
    violated_keywords = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, response_lower):
            violated_keywords.append(pattern)
    
    if violated_keywords:
        logger.warning(
            f"⚠️ GEMINI POLICY VIOLATION: Response mentioned forbidden topics: {violated_keywords}\n"
            f"User asked: '{user_message[:100]}'\n"
            f"Gemini tried to say: '{response_text[:100]}...'"
        )
        
        # Return safe fallback message
        safe_fallback = (
            "That's a great question! However, I need to check our store system "
            "to give you accurate information about that. Let me help you find the right details. "
            "What specifically would you like to know?"
        )
        
        return (False, safe_fallback)
    
    # Response is safe
    return (True, response_text)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_product_name(user_text: str) -> str:
    """
    Extract product name from user input by removing common phrases.
    
    Examples:
        "i want to find a tanktop" → "tanktop"
        "tôi cần tìm áo khoác" → "áo khoác"
        "show me blue shirts" → "blue shirts"
        "tanktop" → "tanktop" (already clean)
    
    Args:
        user_text: Raw user input text
    
    Returns:
        Cleaned product name/keyword
    """
    if not user_text:
        return ""
    
    # Convert to lowercase for pattern matching
    text = user_text.strip()
    
    # Remove common English prefixes (case-insensitive)
    en_patterns = [
        r'^i\s+want\s+to\s+(find|buy|see|search)\s+(for\s+)?(a\s+|an\s+|some\s+)?',
        r'^i\s*m\s+(finding|searching|looking\s+for)\s+(a\s+|an\s+)?',
        r'^find\s+(me\s+)?(a\s+|an\s+|some\s+)?',
        r'^show\s+(me\s+)?(a\s+|an\s+|some\s+)?',
        r'^search\s+(for\s+)?(a\s+|an\s+|some\s+)?',
        r'^looking\s+for\s+(a\s+|an\s+|some\s+)?',
        r'^(can|could)\s+you\s+(find|show)\s+(me\s+)?(a\s+|an\s+)?',
        r'^i\s+need\s+(a\s+|an\s+|some\s+)?',
        r'^finding\s+(a\s+|an\s+)?',
    ]
    
    # Remove common Vietnamese prefixes
    vi_patterns = [
        r'^tôi\s+cần\s+(tìm|mua)\s+',
        r'^tôi\s+muốn\s+(tìm|mua)\s+',
        r'^tìm\s+(cho\s+tôi\s+)?',
        r'^cho\s+tôi\s+(xem|tìm)\s+',
        r'^tìm\s+giúp\s+tôi\s+',
        r'^mua\s+cho\s+tôi\s+',
        r'^có\s+',
    ]
    
    # Apply all patterns
    for pattern in en_patterns + vi_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ============================================================================
# PRODUCT SEARCH & INQUIRY ACTIONS
# ============================================================================

class ActionSearchProducts(Action):
    """
    Search for products based on user query
    REFACTORED: Simplified and fixed backend response handling
    """
    
    def name(self) -> Text:
        return "action_search_products"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # 1. Get search query from entities or user message
        product_type = next(tracker.get_latest_entity_values("product_type"), None)
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        
        # Priority: entity > full text
        search_query = product_name or product_type
        
        if not search_query:
            # Fallback: extract from full user text
            user_text = tracker.latest_message.get('text', '')
            search_query = extract_product_name(user_text) if user_text else None
        
        logger.info(f"🔍 Searching for: {search_query}")
        
        if not search_query:
            dispatcher.utter_message(
                text="What are you looking for? Shirts, pants, jackets, or maybe some accessories? 😊",
                metadata={"source": "rasa_template"}
            )
            return []
        
        # Check if query is clearly out-of-scope (weather, news, etc.)
        user_text = tracker.latest_message.get('text', '').lower()
        out_of_scope_keywords = ["weather", "forecast", "temperature", "rain", "news", "movie", "song", "restaurant", "recipe", "flight", "hotel"]
        if any(keyword in user_text for keyword in out_of_scope_keywords):
            logger.info(f"🚫 Out-of-scope query detected in product search: {user_text[:50]}")
            dispatcher.utter_message(
                text="I'm a fashion shopping assistant focused on menswear! I can help you with:\n\n"
                     "• Product searches & recommendations 👕\n"
                     "• Styling advice & fit guidance 📏\n"
                     "• Order tracking & policies 📦\n\n"
                     "What can I help you find today?",
                metadata={"source": "rasa_template", "out_of_scope": True}
            )
            return [SlotSet("products_found", False)]
        
        # 2. Call Backend API
        try:
            api_client = get_api_client()
            result = api_client.search_products(search_query, limit=5)
            
            logger.info(f"📥 API Response: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            # Check for errors
            if isinstance(result, dict) and result.get("error"):
                logger.error(f"❌ API Error: {result.get('error')}")
                dispatcher.utter_message(
                    text="I'm having trouble connecting to the product catalog right now. 🙏",
                    metadata={"source": "backend", "error": True}
                )
                return [SlotSet("products_found", False)]
            
            # 3. Parse chatbot API response structure
            # Expected: {"success": true, "data": {"query": "...", "total": 5, "products": [...]}}
            products = []
            if isinstance(result, dict) and result.get("success") and result.get("data"):
                data = result.get("data", {})
                products = data.get("products", [])
                logger.info(f"✅ Parsed {len(products)} products from chatbot API response")
            elif isinstance(result, list):
                # Fallback: direct list
                products = result
            elif isinstance(result, dict):
                # Fallback: check for direct 'products' key
                products = result.get("products", [])
            
            # 4. Display results
            if not products:
                dispatcher.utter_message(
                    text=f"Sorry, I couldn't find any products matching '{search_query}' 😅\n\nCould you describe it differently?",
                    metadata={"source": "backend", "type": "no_results"}
                )
                return [SlotSet("products_found", False)]
            
            # Format products for frontend ProductCarousel
            # Chatbot API returns: product_id, name, category, price
            product_list = []
            for p in products:
                product_list.append({
                    "product_id": p.get("product_id") or p.get("id"),
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "price": float(p.get("price") or p.get("selling_price") or 0),
                    "thumbnail": p.get("thumbnail") or p.get("thumbnail_url"),
                    "rating": float(p.get("rating") or p.get("average_rating") or 0),
                    "reviews": p.get("reviews") or p.get("total_reviews") or 0,
                    "in_stock": p.get("in_stock", True)
                })
            
            # Send text + custom data for ProductCarousel
            dispatcher.utter_message(
                text=f"Found {len(products)} products for '{search_query}':",
                json_message={
                    "type": "product_list",
                    "products": product_list
                }
            )
            
            dispatcher.utter_message(
                text="💡 Click on any product to see details! 😊"
            )
            
            # Save to slots
            return [
                SlotSet("products_found", True),
                SlotSet("last_search_query", search_query),
                SlotSet("last_products", products[:10])
            ]
            
        except Exception as e:
            logger.error(f"❌ Exception in ActionSearchProducts: {e}")
            dispatcher.utter_message(
                text="Oops, something went wrong. Please try again later! 🙏",
                metadata={"source": "backend", "error": True, "exception": str(e)}
            )
            return [SlotSet("products_found", False)]


class ActionSearchByPrice(Action):
    """Search products by price range - handles intent: search_by_price"""
    
    def name(self) -> Text:
        return "action_search_by_price"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        max_price_str = next(tracker.get_latest_entity_values("max_price"), None)
        min_price_str = next(tracker.get_latest_entity_values("min_price"), None)
        product_type = next(tracker.get_latest_entity_values("product_type"), None)
        
        max_price = None
        min_price = None
        
        if max_price_str:
            try:
                max_price = float(str(max_price_str).replace("$", "").strip())
            except ValueError:
                pass
        
        if min_price_str:
            try:
                min_price = float(str(min_price_str).replace("$", "").strip())
            except ValueError:
                pass
        
        if not max_price and not min_price:
            dispatcher.utter_message(text="What's your budget? For example: 'under $20' or 'between $10 and $50'")
            return []
        
        logger.info(f"💰 Price search: min={min_price}, max={max_price}, type={product_type}")
        
        try:
            api_client = get_api_client()
            result = api_client.search_products(query=product_type, min_price=min_price, max_price=max_price, limit=10)
            
            products = []
            if isinstance(result, dict):
                products = result.get("products", [])
            
            if not products:
                price_range_msg = ""
                if min_price and max_price:
                    price_range_msg = f"between ${min_price} and ${max_price}"
                elif max_price:
                    price_range_msg = f"under ${max_price}"
                elif min_price:
                    price_range_msg = f"over ${min_price}"
                
                dispatcher.utter_message(text=f"I couldn't find products {price_range_msg} 😅\n\nWould you like to try a different price range?")
                return [SlotSet("products_found", False)]
            
            price_desc = ""
            if min_price and max_price:
                price_desc = f"between ${min_price} and ${max_price}"
            elif max_price:
                price_desc = f"under ${max_price}"
            elif min_price:
                price_desc = f"over ${min_price}"
            
            message = f"Found {len(products)} products {price_desc}:\n\n"
            
            for i, p in enumerate(products[:5], 1):
                name = p.get("name", "Unknown Product")
                price = p.get("selling_price") or p.get("price", 0)
                
                if isinstance(price, (int, float)):
                    price_str = f"${price:.2f}"
                else:
                    try:
                        price_str = f"${float(price):.2f}"
                    except:
                        price_str = "Contact for price"
                
                colors = p.get("available_colors", [])
                color_info = ""
                if colors and len(colors) > 0:
                    if len(colors) <= 3:
                        color_names = [c.get("name", c) if isinstance(c, dict) else c for c in colors]
                        color_info = f" - {', '.join(color_names)}"
                    else:
                        color_info = f" - {len(colors)} colors"
                
                stock_icon = "✅" if p.get("in_stock") else "😢"
                message += f"{i}. **{name}**{color_info} - {price_str} {stock_icon}\n"
            
            message += "\n💡 Which one interests you? 😊"
            
            dispatcher.utter_message(text=message)
            
            return [
                SlotSet("products_found", True),
                SlotSet("last_products", products[:10])
            ]
            
        except Exception as e:
            logger.error(f"❌ Exception in ActionSearchByPrice: {e}")
            dispatcher.utter_message(text="Oops, I had trouble searching by price. Please try again! 🙏")
            return [SlotSet("products_found", False)]


class ActionGetSizingAdvice(Action):
    """Get sizing advice based on height/weight/body type and fit preference."""

    def name(self) -> Text:
        return "action_get_sizing_advice"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        height = next(tracker.get_latest_entity_values("height"), None)
        weight = next(tracker.get_latest_entity_values("weight"), None)
        body_type = next(tracker.get_latest_entity_values("body_type"), "")
        fit_preference = next(tracker.get_latest_entity_values("fit_preference"), "")

        missing_parts = []
        if not product_name:
            missing_parts.append("product you want to buy")
        if not height:
            missing_parts.append("your height")
        if not weight:
            missing_parts.append("your weight")

        if missing_parts:
            dispatcher.utter_message(
                text=(
                    "To recommend the best size, please tell me: "
                    + ", ".join(missing_parts)
                    + ". For example: 'I'm 1m75, 70kg and want the classic polo'."
                )
            )
            return []

        api_client = get_api_client()
        
        # First, search for the product to get product_id
        search_result = api_client.search_products(product_name, limit=1)
        if search_result.get("error") or not search_result.get("products"):
            dispatcher.utter_message(text=f"I couldn't find '{product_name}'. Could you verify the product name?")
            return []
        
        product_id = search_result["products"][0].get("id")
        if not product_id:
            dispatcher.utter_message(text="I found the product but couldn't get its details. Please try again.")
            return []
        
        # Get sizing advice with product_id
        result = api_client.get_sizing_advice(
            product_id=product_id,
            height=str(height),
            weight=str(weight),
            body_type=str(body_type),
            fit_preference=str(fit_preference),
        )

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "I couldn't get a precise sizing recommendation right now. "
                    "As a general rule, if you are between sizes, it's usually safer to size up for a relaxed fit."
                )
            )
            return []

        advice = result.get("data", {}).get("advice") or result.get("advice")
        if advice:
            dispatcher.utter_message(text=advice)
        else:
            dispatcher.utter_message(
                text=(
                    "Based on your height, weight and preferences, I would recommend checking the size chart "
                    "for chest and waist measurements and choosing the closest match."
                )
            )

        return []


class ActionGetStylingAdvice(Action):
    """Get styling advice for a garment."""

    def name(self) -> Text:
        return "action_get_styling_advice"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)

        if not product_name:
            dispatcher.utter_message(text="Which product would you like styling advice for?")
            return []

        api_client = get_api_client()
        
        # Search for product to get product_id
        search_result = api_client.search_products(product_name, limit=1)
        if search_result.get("error") or not search_result.get("data"):
            dispatcher.utter_message(text=f"I couldn't find '{product_name}'. Please verify the product name.")
            return []
        
        product_id = search_result["data"][0].get("id")
        if not product_id:
            dispatcher.utter_message(text="I found the product but couldn't get styling details.")
            return []
        
        # Get styling advice using real API
        result = api_client.get_styling_advice(product_id=product_id)

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "Here are some generic styling tips: pair slim jeans with a clean sneaker, "
                    "and balance oversized tops with more fitted bottoms."
                )
            )
            return []

        # Extract styling rules from response
        styling_rules = result.get("data", {}).get("styling_rules") or result.get("styling_rules")
        if styling_rules:
            dispatcher.utter_message(text=styling_rules)
        else:
            dispatcher.utter_message(
                text=(
                    "You can combine this piece with neutral basics (black, white, navy) "
                    "and simple sneakers for a clean, casual look."
                )
            )

        return []


class ActionGetProductCare(Action):
    """Answer product care / washing questions using product details API."""

    def name(self) -> Text:
        return "action_get_product_care"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)

        if not product_name:
            dispatcher.utter_message(
                text="Which product would you like care instructions for?"
            )
            return []

        api_client = get_api_client()
        
        # Search for product to get product_id
        search_result = api_client.search_products(product_name, limit=1)
        if search_result.get("error") or not search_result.get("data"):
            dispatcher.utter_message(text=f"I couldn't find '{product_name}'. Please check the product name.")
            return []
        
        product_id = search_result["data"][0].get("id")
        if not product_id:
            dispatcher.utter_message(text="I found the product but couldn't get care details.")
            return []
        
        # Get care instructions from product details (real API call)
        result = api_client.get_product_care_info(product_id=product_id)

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "As a general rule, wash similar colors together, use gentle cycles, "
                    "and avoid high heat drying to maintain the shape and color."
                )
            )
            return []

        care_text = result.get("care")
        if care_text:
            dispatcher.utter_message(text=f"Care instructions: {care_text}")
        else:
            dispatcher.utter_message(
                text=(
                    "Please follow the care label on the garment. If you are unsure, "
                    "cold wash and air dry is usually the safest option."
                )
            )

        return []


class ActionReportOrderError(Action):
    """Handle reports about missing or extra items in an order."""

    def name(self) -> Text:
        return "action_report_order_error"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        order_number = next(tracker.get_latest_entity_values("order_number"), None)
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        error_type = next(tracker.get_latest_entity_values("error_type"), None)
        quantity = next(tracker.get_latest_entity_values("quantity"), "")

        # Use helper to extract customer_id from metadata or slots
        customer_id = get_customer_id_from_tracker(tracker)
        
        if not customer_id:
            dispatcher.utter_message(
                text=(
                    "To review issues with a specific order, please sign in first so I can verify your purchases."
                )
            )
            return []
        
        # Get JWT token for API calls
        metadata = tracker.latest_message.get("metadata", {})
        user_token = metadata.get("user_jwt_token") or tracker.get_slot("user_jwt_token")

        if not order_number or not product_name or not error_type:
            dispatcher.utter_message(
                text=(
                    "Please tell me the order number, which item is affected, and whether it is missing or extra."
                )
            )
            return []

        api_client = get_api_client()
        user_message = tracker.latest_message.get("text", "")
        
        # Report order error - creates support ticket internally
        result = api_client.report_order_error(
            order_number=order_number,
            error_type=str(error_type),
            product_name=product_name,
            quantity=str(quantity),
            user_message=user_message,
            auth_token=user_token,
        )

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "I've logged your order issue and created a ticket for our support team. "
                    "They will review your case and get back to you shortly."
                )
            )
        else:
            dispatcher.utter_message(
                text=(
                    "Thank you for letting us know. I have recorded the problem with your order "
                    "and our support team will follow up with you as soon as possible."
                )
            )

        return []


class ActionRequestReturnOrExchange(Action):
    """Handle requests to exchange or return a specific item from an order."""

    def name(self) -> Text:
        return "action_request_return_or_exchange"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        order_number = next(tracker.get_latest_entity_values("order_number"), None)
        product_to_return = next(tracker.get_latest_entity_values("product_to_return"), None)
        reason = next(tracker.get_latest_entity_values("reason"), None)
        product_to_get = next(tracker.get_latest_entity_values("product_to_get"), "")

        # Use helper to extract customer_id from metadata or slots
        customer_id = get_customer_id_from_tracker(tracker)
        
        if not customer_id:
            dispatcher.utter_message(
                text=(
                    "To request an exchange or return, please sign in so I can verify your order details."
                )
            )
            return []
        
        # Get JWT token for API calls
        metadata = tracker.latest_message.get("metadata", {})
        user_token = metadata.get("user_jwt_token") or tracker.get_slot("user_jwt_token")

        if not order_number or not product_to_return or not reason:
            dispatcher.utter_message(
                text=(
                    "Please provide the order number, which item you want to exchange, and the reason."
                )
            )
            return []

        api_client = get_api_client()
        user_message = tracker.latest_message.get("text", "")
        
        result = api_client.request_return_or_exchange(
            order_number=order_number,
            product_to_return=product_to_return,
            product_to_get=str(product_to_get),
            reason=str(reason),
            user_message=user_message,
            auth_token=user_token,
        )

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "I've recorded your request. Our support team will review whether the item is eligible "
                    "for return or exchange under our policy and will contact you soon."
                )
            )
        else:
            dispatcher.utter_message(
                text=(
                    "Your exchange/return request has been submitted. You will receive further instructions "
                    "by email if it is approved."
                )
            )

        return []


class ActionReportQualityIssue(Action):
    """Handle quality complaints about a product."""

    def name(self) -> Text:
        return "action_report_quality_issue"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        defect_description = next(tracker.get_latest_entity_values("defect_description"), None)

        # Use helper to extract customer_id from metadata or slots
        customer_id = get_customer_id_from_tracker(tracker)
        
        if not customer_id:
            dispatcher.utter_message(
                text=(
                    "To review a quality issue for a purchase, please sign in so I can check your order history."
                )
            )
            return []
        
        # Get JWT token for API calls
        metadata = tracker.latest_message.get("metadata", {})
        user_token = metadata.get("user_jwt_token") or tracker.get_slot("user_jwt_token")

        if not product_name or not defect_description:
            dispatcher.utter_message(
                text=(
                    "Please describe which product has the issue and what exactly is wrong with it."
                )
            )
            return []

        api_client = get_api_client()
        user_message = tracker.latest_message.get("text", "")
        
        result = api_client.report_quality_issue(
            product_name=product_name,
            defect_description=str(defect_description),
            user_message=user_message,
            auth_token=user_token,
        )

        dispatcher.utter_message(
            text=(
                "I'm sorry to hear about the quality issue. I have forwarded the details to our team. "
                "They will check whether this is covered under warranty or considered normal wear and tear."
            )
        )

        if result.get("error"):
            dispatcher.utter_message(
                text="If you can, please also attach photos when our support team contacts you."
            )

        return []


class ActionHandlePolicyException(Action):
    """Handle cases where user asks for an exception to normal policy."""

    def name(self) -> Text:
        return "action_handle_policy_exception"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        policy_type = next(tracker.get_latest_entity_values("policy_type"), None)
        reason = next(tracker.get_latest_entity_values("reason"), None)

        # Use helper to extract customer_id from metadata or slots
        customer_id = get_customer_id_from_tracker(tracker)
        
        if not customer_id:
            dispatcher.utter_message(
                text=(
                    "For special policy exceptions, please sign in first so we can verify your purchase."
                )
            )
            return []
        
        # Get JWT token for API calls
        metadata = tracker.latest_message.get("metadata", {})
        user_token = metadata.get("user_jwt_token") or tracker.get_slot("user_jwt_token")

        if not product_name or not policy_type or not reason:
            dispatcher.utter_message(
                text=(
                    "Please tell me which product, which policy applies (for example 'final sale'), "
                    "and why you are requesting an exception."
                )
            )
            return []

        api_client = get_api_client()
        user_message = tracker.latest_message.get("text", "")
        
        # Creates support ticket internally
        result = api_client.handle_policy_exception(
            product_name=product_name,
            policy_type=str(policy_type),
            reason=str(reason),
            user_message=user_message,
            auth_token=user_token,
        )

        dispatcher.utter_message(
            text=(
                "I understand your situation. Normally this policy is strict, but because there is a potential defect, "
                "I have escalated your case to our support team for a manual review."
            )
        )

        return []


class ActionSetStockNotification(Action):
    """Register a stock notification for out-of-stock products."""

    def name(self) -> Text:
        return "action_set_stock_notification"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        size = next(tracker.get_latest_entity_values("size"), None)

        # Use helper to extract customer_id from metadata or slots
        customer_id = get_customer_id_from_tracker(tracker)
        
        if not customer_id:
            dispatcher.utter_message(
                text=(
                    "To receive stock notifications, please sign in so we can link the alert to your account."
                )
            )
            return []
        
        # Get JWT token for API calls
        metadata = tracker.latest_message.get("metadata", {})
        user_token = metadata.get("user_jwt_token") or tracker.get_slot("user_jwt_token")

        if not product_name:
            dispatcher.utter_message(
                text="Please tell me which product you want to be notified about."
            )
            return []

        api_client = get_api_client()
        
        # Search for product to get product_id
        search_result = api_client.search_products(product_name, limit=1)
        if search_result.get("error") or not search_result.get("data"):
            dispatcher.utter_message(text=f"I couldn't find '{product_name}'. Please verify the product name.")
            return []
        
        product = search_result["data"][0]
        product_id = product.get("id")
        
        # For simplicity, use first variant or default variant_id
        # In production, match size to specific variant
        variant_id = product.get("default_variant_id", "default")
        
        result = api_client.set_stock_notification(
            product_id=product_id,
            variant_id=variant_id,
            auth_token=user_token,
        )

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "I couldn't register a stock notification right now, but you can also add this item "
                    "to your favourites and check back later."
                )
            )
        else:
            dispatcher.utter_message(
                text=f"Got it! I will notify you when '{product_name}' is back in stock."
            )

        return []


class ActionCheckDiscount(Action):
    """List top discounted products (no discount codes - direct pricing)."""

    def name(self) -> Text:
        return "action_check_discount"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        api_client = get_api_client()
        result = api_client.get_top_discounts(limit=10)

        if result.get("error"):
            dispatcher.utter_message(
                text="I couldn't fetch the current discounts right now. Please check our sale section on the website."
            )
            return []

        products = result.get("data", [])
        
        if not products:
            dispatcher.utter_message(
                text="There are no special discounts available at the moment, but we update our deals regularly!"
            )
            return []

        # Format the response with top discounted products
        response = "🎉 **Top Discounted Products:**\n\n"
        for i, product in enumerate(products[:5], 1):
            name = product.get("name", "Unknown")
            original_price = product.get("original_price", 0)
            discounted_price = product.get("price", 0)
            discount_percent = product.get("discount_percent", 0)
            
            response += f"{i}. **{name}**\n"
            if original_price and discounted_price:
                response += f"   💰 ~~${original_price}~~ **${discounted_price}** ({discount_percent}% off)\n\n"
            else:
                response += f"   💰 **${discounted_price}**\n\n"
        
        response += "Would you like to know more about any of these products?"
        
        dispatcher.utter_message(text=response)
        return [SlotSet("last_products", products)]


class ActionGetProductPrice(Action):
    """Get price information for a specific product"""
    
    def name(self) -> Text:
        return "action_get_product_price"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        
        if not product_name:
            # Try to use last search results
            last_products = tracker.get_slot("last_products")
            if last_products:
                response = "Here are the prices from your last search:\n\n"
                for product in last_products:
                    response += f"• {product.get('name')}: ${product.get('price')}\n"
                dispatcher.utter_message(text=response)
                return []
            else:
                dispatcher.utter_message(text="Which product would you like to know the price of? 😊")
                return []
        
        logger.info(f"Getting price for product: {product_name}")
        
        # Search for the product with timing
        api_client = get_api_client()
        start_time = time.time()
        result = api_client.search_products(product_name, limit=1)
        api_time = time.time() - start_time
        logger.info(f"⏱️ API search_products took {api_time:.3f}s")
        
        if result.get("error") or not result.get("products"):
            dispatcher.utter_message(
                text=f"Hmm, I couldn't find pricing for '{product_name}' 😅\n\nWould you like me to search for something similar?"
            )
            return []
        
        product = result["products"][0]
        name = product.get("name")
        price = product.get("selling_price", 0)
        
        if isinstance(price, (int, float)) and price > 0:
            price_str = f"{price:,.0f}₫"
            dispatcher.utter_message(
                text=f"The **{name}** is priced at **{price_str}**.\n\nWould you like to know more details about this product? I'm happy to help! 😊"
            )
        else:
            dispatcher.utter_message(
                text=f"The **{name}** is currently being updated with pricing. Please contact us directly for the most accurate quote! 📱"
            )
        
        return [SlotSet("last_product", product)]


class ActionCheckAvailability(Action):
    """Check if a product is available in stock"""
    
    def name(self) -> Text:
        return "action_check_availability"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        
        if not product_name:
            dispatcher.utter_message(text="Which product would you like me to check stock for? 😊")
            return []
        
        logger.info(f"Checking availability for: {product_name}")
        
        api_client = get_api_client()
        start_time = time.time()
        result = api_client.search_products(product_name, limit=1)
        api_time = time.time() - start_time
        logger.info(f"⏱️ API search_products took {api_time:.3f}s")
        
        if result.get("error") or not result.get("products"):
            dispatcher.utter_message(
                text=f"Hmm, I couldn't find '{product_name}' in our inventory 😅\n\nWould you like to try another product, or should I suggest some alternatives?"
            )
            return []
        
        product = result["products"][0]
        name = product.get("name")
        stock = product.get("total_stock", 0)
        
        if stock > 0:
            dispatcher.utter_message(
                text=f"Good news! **{name}** is in stock with {stock} units available 🎉\n\nWould you like to place an order, or need any advice first? 😊"
            )
        else:
            dispatcher.utter_message(
                text=f"Unfortunately, **{name}** is currently out of stock 😢\n\nWould you like me to notify you when it's back, or suggest similar items? 📱"
            )
        
        return [SlotSet("last_product", product)]


class ActionGetProductDetails(Action):
    """
    Get detailed information about a product
    REFACTORED: Support contextual queries (first one, number 2, etc.)
    """
    
    def name(self) -> Text:
        return "action_get_product_details"
    
    def _parse_product_index(self, text: str) -> int:
        """
        Parse product index from contextual references
        Returns 0-indexed position or -1 if not found
        """
        text_lower = text.lower()
        
        # English patterns
        if "first" in text_lower or "1st" in text_lower or "number 1" in text_lower:
            return 0
        if "second" in text_lower or "2nd" in text_lower or "number 2" in text_lower:
            return 1
        if "third" in text_lower or "3rd" in text_lower or "number 3" in text_lower:
            return 2
        if "fourth" in text_lower or "4th" in text_lower or "number 4" in text_lower:
            return 3
        if "fifth" in text_lower or "5th" in text_lower or "number 5" in text_lower:
            return 4
        
        # Vietnamese patterns
        if "đầu tiên" in text_lower or "đầu" in text_lower or "số 1" in text_lower:
            return 0
        if "thứ hai" in text_lower or "thứ 2" in text_lower or "số 2" in text_lower:
            return 1
        if "thứ ba" in text_lower or "thứ 3" in text_lower or "số 3" in text_lower:
            return 2
        if "thứ tư" in text_lower or "thứ 4" in text_lower or "số 4" in text_lower:
            return 3
        if "thứ năm" in text_lower or "thứ 5" in text_lower or "số 5" in text_lower:
            return 4
        
        return -1
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get("text", "")
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        product = None
        
        # Strategy 1: Check for contextual reference (first one, number 2, etc.)
        last_products = tracker.get_slot("last_products")
        if last_products and isinstance(last_products, list) and len(last_products) > 0:
            product_index = self._parse_product_index(user_message)
            
            if product_index >= 0 and product_index < len(last_products):
                product = last_products[product_index]
                logger.info(f"✅ Found product by context: index={product_index}, product={product.get('name')}")
        
        # Strategy 2: Check for explicit product name
        if not product and product_name:
            # First try to find in last_products by name match
            if last_products and isinstance(last_products, list):
                for p in last_products:
                    if product_name.lower() in p.get("name", "").lower():
                        product = p
                        logger.info(f"✅ Found product in cache: {product.get('name')}")
                        break
            
            # If not in cache, search via API
            if not product:
                api_client = get_api_client()
                start_time = time.time()
                result = api_client.search_products(product_name, limit=1)
                api_time = time.time() - start_time
                logger.info(f"⏱️ API search_products took {api_time:.3f}s")
                
                # Handle response
                products = []
                if isinstance(result, list):
                    products = result
                elif isinstance(result, dict):
                    products = result.get("products") or result.get("data") or []
                
                if products and len(products) > 0:
                    product = products[0]
                else:
                    dispatcher.utter_message(
                        text=f"Hmm, I couldn't find '{product_name}' 😅\n\nCould you try a different name?"
                    )
                    return []
        
        # Strategy 3: Check last_product slot (singular - from previous detail view)
        if not product:
            last_product = tracker.get_slot("last_product")
            if last_product:
                product = last_product
                logger.info("✅ Using last viewed product")
        
        # Strategy 4: No context - show popular products
        if not product:
            dispatcher.utter_message(
                text="Which product would you like to know about? 😊\n\nYou can say:\n• 'Show me the first one'\n• 'Tell me about the blue jacket'\n• 'Search for shirts'"
            )
            return []
        
        # Get full details via API if we have product_id
        product_id = product.get("id") or product.get("product_id")
        if product_id:
            api_client = get_api_client()
            try:
                detailed_result = api_client.get_product_by_id(str(product_id))
                if not detailed_result.get("error"):
                    # Merge detailed data
                    product.update(detailed_result.get("data", {}) or detailed_result)
                    logger.info(f"✅ Fetched detailed info for product_id={product_id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch detailed info: {e}")
        
        # Format product details
        name = product.get("name", "Product")
        price_raw = product.get("selling_price") or product.get("price")
        description = product.get("description", "High quality product")
        in_stock = product.get("in_stock", False)
        category = product.get("category_name") or product.get("category", "General")
        material = product.get("material", "")
        variants = product.get("variants", [])
        available_colors = product.get("available_colors", [])
        available_sizes = product.get("available_sizes", [])
        
        # Parse price (backend returns string or number)
        price_str = "Contact for pricing"
        if price_raw:
            try:
                price_val = float(price_raw)
                if price_val > 0:
                    price_str = f"${price_val:.2f}"
            except (ValueError, TypeError):
                pass
        
        # Contextual explanation if from search results
        context_msg = ""
        if product_index >= 0:
            context_msg = f"This is product #{product_index + 1} from your previous search.\n\n"
        
        response = context_msg
        response += f"📦 **{name}**\n\n"
        response += f"💰 Price: {price_str}\n"
        
        # Show category only if meaningful
        if category and category.lower() not in ["general", "unknown"]:
            response += f"📂 Category: {category}\n"
        
        if material:
            response += f"🧵 Material: {material}\n"
        
        # Show available colors
        if available_colors and isinstance(available_colors, list) and len(available_colors) > 0:
            color_names = [c.get("name", c) if isinstance(c, dict) else str(c) for c in available_colors]
            if len(color_names) <= 3:
                response += f"🎨 Available colors: {', '.join(color_names)}\n"
            else:
                response += f"🎨 Available colors: {', '.join(color_names[:3])} (+{len(color_names)-3} more)\n"
        
        # Show available sizes
        if available_sizes and isinstance(available_sizes, list) and len(available_sizes) > 0:
            size_names = [s.get("name", s) if isinstance(s, dict) else str(s) for s in available_sizes]
            response += f"📏 Available sizes: {', '.join(size_names)}\n"
        
        # Stock status - use in_stock field from backend
        if in_stock:
            response += f"✅ In stock\n\n"
        else:
            response += f"😢 Currently out of stock\n\n"
        
        response += f"📝 **Description:**\n{description}\n\n"
        
        # CTA based on stock status
        if in_stock:
            response += "Would you like to add this to your cart? 😊"
        else:
            response += "This item is out of stock. Would you like me to suggest similar products?"
        
        # NEW: Send product_actions metadata for button-based variant selection
        custom_data = None
        if in_stock and variants and len(variants) > 0:
            # Extract unique colors and sizes with IDs
            colors_map = {}
            sizes_map = {}
            
            for v in variants:
                # Extract color info
                color_obj = v.get("color", {})
                if isinstance(color_obj, dict):
                    color_id = color_obj.get("id") or v.get("color_id")
                    color_name = color_obj.get("name") or v.get("color_name")
                    color_hex = color_obj.get("hex") or v.get("color_hex")
                    
                    if color_id and color_name and color_id not in colors_map:
                        colors_map[color_id] = {
                            "id": int(color_id),
                            "name": str(color_name),
                            "hex": str(color_hex) if color_hex else None
                        }
                
                # Extract size info
                size_obj = v.get("size", {})
                if isinstance(size_obj, dict):
                    size_id = size_obj.get("id") or v.get("size_id")
                    size_name = size_obj.get("name") or v.get("size_name")
                    
                    if size_id and size_name and size_id not in sizes_map:
                        sizes_map[size_id] = {
                            "id": int(size_id),
                            "name": str(size_name)
                        }
            
            available_colors_with_ids = list(colors_map.values())
            available_sizes_with_ids = list(sizes_map.values())
            
            # Only send metadata if we have both colors and sizes
            if available_colors_with_ids and available_sizes_with_ids:
                custom_data = {
                    "type": "product_actions",
                    "product_id": int(product_id),
                    "product_name": name,
                    "product_price": float(price_raw) if price_raw else 0,
                    "product_thumbnail": product.get("thumbnail") or product.get("image_url") or "",
                    "available_colors": available_colors_with_ids,
                    "available_sizes": available_sizes_with_ids
                }
                logger.info(f"✅ Sending product_actions metadata: {len(available_colors_with_ids)} colors, {len(available_sizes_with_ids)} sizes")
        
        dispatcher.utter_message(
            text=response,
            json_message={"custom": custom_data} if custom_data else None
        )
        
        # Save current product and update slot
        return [
            SlotSet("last_product", product),
            SlotSet("current_product_id", product_id)
        ]


# ============================================================================
# ORDER TRACKING & MANAGEMENT ACTIONS
# ============================================================================

class ActionTrackOrder(Action):
    """Track order status - supports order number or product name search"""
    
    def name(self) -> Text:
        return "action_track_order"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        order_number = next(tracker.get_latest_entity_values("order_number"), None)
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        
        # Debug: Log all extracted entities
        all_entities = tracker.latest_message.get("entities", [])
        logger.info(f"📋 Extracted entities: {all_entities}")
        logger.info(f"🔢 Order number extracted: {order_number}")
        logger.info(f"📦 Product name extracted: {product_name}")
        
        # Check if user is logged in - use helper to extract from metadata or slots
        customer_id = get_customer_id_from_tracker(tracker)
        
        if not customer_id:
            dispatcher.utter_message(
                text="To track your order, please sign in to your account first."
            )
            return []
        
        logger.info(f"🔐 User authenticated - customer_id: {customer_id}")
        
        # Get JWT token for API calls (from metadata or slot)
        metadata = tracker.latest_message.get("metadata", {})
        user_token = metadata.get("user_jwt_token") or tracker.get_slot("user_jwt_token")
        
        api_client = get_api_client()
        
        # Better UX: Track by purchased product instead of order number
        if product_name and not order_number:
            logger.info(f"Tracking order by product: {product_name}")
            
            result = api_client.search_purchased_products(product_name, user_token)
            
            if result.get("error") or not result.get("data"):
                dispatcher.utter_message(
                    text=f"I couldn't find any orders with '{product_name}'. Please verify the product name or provide your order number."
                )
                return []
            
            orders = result["data"]
            if len(orders) == 1:
                # Single match - show order details
                order_number = orders[0].get("order_number")
                order_id = orders[0].get("order_id")
            else:
                # Multiple matches - list them
                response = f"I found {len(orders)} orders with '{product_name}':\n\n"
                for i, order in enumerate(orders[:3], 1):
                    response += f"{i}. Order #{order.get('order_number')} - {order.get('status')} ({order.get('date')})\n"
                response += "\nWhich order would you like to track?"
                dispatcher.utter_message(text=response)
                return []
        
        elif order_number:
            logger.info(f"Tracking order by number: {order_number}")
            order_id = order_number.replace("#", "")
        else:
            # No order number or product name provided - show recent orders list
            logger.info("No order number provided - showing order list")
            
            result = api_client.get_user_orders(user_token, limit=5)
            
            if result.get("error") or not result.get("data"):
                dispatcher.utter_message(
                    text="I couldn't retrieve your orders. Please try again or provide a specific order number."
                )
                return []
            
            orders = result.get("data", [])
            
            if len(orders) == 0:
                dispatcher.utter_message(
                    text="You don't have any orders yet. Start shopping to place your first order! 🛍️"
                )
                return []
            
            # Format order list
            response = f"📦 **Your Recent Orders** ({len(orders)} orders)\n\n"
            
            from datetime import datetime
            for i, order in enumerate(orders[:5], 1):
                order_num = order.get("order_number", "N/A")
                status = order.get("fulfillment_status") or order.get("status", "Unknown")
                total = order.get("total_amount") or order.get("total", 0)
                date_raw = order.get("created_at", "")
                
                try:
                    if date_raw:
                        dt = datetime.fromisoformat(date_raw.replace('Z', '+00:00'))
                        date_str = dt.strftime("%b %d, %Y")
                    else:
                        date_str = "N/A"
                except:
                    date_str = date_raw if date_raw else "N/A"
                
                total_str = f"{total:,.0f}₫" if total else "N/A"
                
                response += f"{i}. **#{order_num}** - {status.title()} - {total_str}\n"
                response += f"   📅 {date_str}\n\n"
            
            response += "💬 Reply with an order number to see details (e.g., '0000000001')"
            
            dispatcher.utter_message(text=response)
            return []
        
        # Get order details
        result = api_client.get_order_details(order_id, user_token)
        
        # Debug: Log the full response
        logger.info(f"🔍 Backend response structure: {list(result.keys())}")
        logger.info(f"🔍 Full response: {result}")
        
        if result.get("error"):
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find order {order_number}. Please verify and try again."
            )
            return []
        
        # Backend returns order data directly (not wrapped in "data" key)
        order = result
        logger.info(f"📦 Order data extracted: {order}")
        logger.info(f"📊 Order keys: {list(order.keys()) if order else 'EMPTY'}")
        
        # Handle backend field names (fulfillment_status/status, total_amount/total)
        status = order.get("fulfillment_status") or order.get("status", "Unknown")
        payment_status = order.get("payment_status", "")
        total_amount = order.get("total_amount") or order.get("total", 0)
        created_at_raw = order.get("created_at", "")
        
        # Debug: Log field extraction
        logger.info(f"🔍 fulfillment_status: {order.get('fulfillment_status')}")
        logger.info(f"🔍 status: {order.get('status')}")
        logger.info(f"🔍 total_amount: {order.get('total_amount')}")
        logger.info(f"🔍 total: {order.get('total')}")
        logger.info(f"🔍 created_at: {order.get('created_at')}")
        logger.info(f"📊 Final values - status={status}, total={total_amount}, date={created_at_raw}")
        
        # Format date for better display
        try:
            from datetime import datetime
            if created_at_raw:
                dt = datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
                created_at = dt.strftime("%B %d, %Y")
            else:
                created_at = "N/A"
        except:
            created_at = created_at_raw if created_at_raw else "N/A"
        
        # Format total with currency (convert string to float first)
        try:
            if total_amount and total_amount != 0:
                total_float = float(total_amount)
                total_display = f"${total_float:,.2f}"
            else:
                total_display = "N/A"
        except (ValueError, TypeError):
            total_display = str(total_amount) if total_amount else "N/A"
        
        response = f"📦 **Order #{order_number}**\n\n"
        response += f"📊 **Status:** {status.title() if status != 'Unknown' else status}"
        if payment_status:
            response += f" | Payment: {payment_status.title()}"
        response += "\n"
        response += f"📅 **Placed on:** {created_at}\n"
        response += f"💰 **Total:** {total_display}\n\n"
        
        # Add tracking info if available
        tracking_number = order.get("tracking_number")
        if tracking_number:
            response += f"🚚 **Tracking Number:** {tracking_number}\n\n"
        
        response += "Is there anything else you'd like to know about your order?"
        
        dispatcher.utter_message(text=response)
        
        return [SlotSet("last_order", order)]


class ActionCancelOrderRequest(Action):
    """Handle order cancellation request"""
    
    def name(self) -> Text:
        return "action_cancel_order_request"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        order_number = next(tracker.get_latest_entity_values("order_number"), None)
        
        if not order_number:
            dispatcher.utter_message(text="Which order would you like to cancel?")
            return []
        
        # For now, create a support ticket for cancellation
        dispatcher.utter_message(
            text=f"I understand you want to cancel order {order_number}. Let me connect you with our support team to process this request."
        )
        
        # Create support ticket
        api_client = get_api_client()
        user_message = tracker.latest_message.get("text", "")
        
        api_client.create_support_ticket(
            subject=f"Order Cancellation Request - {order_number}",
            message=f"Customer requested cancellation of order {order_number}",
            user_message=user_message
        )
        
        dispatcher.utter_message(
            text="A support ticket has been created. Our team will contact you within 24 hours to process your cancellation."
        )
        
        return []


# ============================================================================
# FAQ & POLICY ACTIONS
# ============================================================================

class ActionGetShippingPolicy(Action):
    """Get shipping policy information"""
    
    def name(self) -> Text:
        return "action_get_shipping_policy"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        logger.info("Fetching shipping policy")
        
        api_client = get_api_client()
        result = api_client.get_shipping_policy()
        
        if result.get("error"):
            dispatcher.utter_message(
                text="Shipping depends on your location within Vietnam:\n• Major Cities (Hanoi, HCMC, Da Nang): Typically 1-2 business days\n• Nationwide Delivery: Approximately 3-5 business days\n\nBest of all, we offer free shipping on all domestic orders!\n\nWe also ship to over 50 countries:\n• Asia (Thailand, Singapore, Malaysia, etc.): 5-7 business days for $8.99\n• Rest of the World: 10-14 business days for $15.99"
            )
            return []
        
        content = result.get("data", {}).get("content", "")
        
        if content:
            # Truncate long content instead of using Gemini (avoid hallucination risk)
            if len(content) > 500:
                dispatcher.utter_message(text=content[:500] + "...")
            else:
                dispatcher.utter_message(text=content)
        else:
            dispatcher.utter_message(response="utter_default_shipping_policy")
        
        return []


class ActionGetReturnPolicy(Action):
    """Get return policy information"""
    
    def name(self) -> Text:
        return "action_get_return_policy"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        logger.info("Fetching return policy")
        
        api_client = get_api_client()
        result = api_client.get_return_policy()
        
        if result.get("error"):
            dispatcher.utter_message(
                text="Our policy is simple: You have 30 days for a full refund if the item is unworn/unwashed and in original condition. Want to start a return? Just type 'Start Return' and include your Order Number! We'll handle it from there.\n\nOnce we receive your returned item, the refund will be processed within 5-7 business days. (Shipping costs are non-refundable.)"
            )
            return []
        
        content = result.get("data", {}).get("content", "")
        
        if content:
            dispatcher.utter_message(text=content[:500] if len(content) > 500 else content)
        else:
            dispatcher.utter_message(response="utter_default_return_policy")
        
        return []


class ActionGetPaymentMethods(Action):
    """Get available payment methods"""
    
    def name(self) -> Text:
        return "action_get_payment_methods"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="To make things convenient for you, LeCas accepts:\n• COD (Cash on Delivery) for domestic orders in Vietnam\n• VNPay for domestic orders in Vietnam\n• Major credit cards (Visa, Mastercard, Amex) for international purchases\n• PayPal for international purchases\n\nPayment options are indicated at checkout based on your location."
        )
        
        return []


class ActionGetWarrantyPolicy(Action):
    """Get warranty policy information"""
    
    def name(self) -> Text:
        return "action_get_warranty_policy"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="All our products come with a standard 1-year manufacturer warranty covering defects in materials and workmanship. Extended warranty options are available at checkout."
        )
        
        return []


# ============================================================================
# RECOMMENDATION & COMPARISON ACTIONS
# ============================================================================

class ActionRecommendProducts(Action):
    """Recommend products using AI"""
    
    def name(self) -> Text:
        return "action_recommend_products"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_query = tracker.latest_message.get("text", "")
        
        # Search for popular/trending products
        api_client = get_api_client()
        result = api_client.search_products("popular", limit=5)
        
        if result.get("error") or not result.get("data"):
            dispatcher.utter_message(
                text="I'd be happy to recommend products! Could you tell me what category you're interested in? (e.g., electronics, clothing, sports)"
            )
            return []
        
        products = result["data"]
        
        # Format products for frontend ProductCarousel
        product_list = []
        for p in products:
            product_list.append({
                "product_id": p.get("id"),
                "name": p.get("name"),
                "slug": p.get("slug"),
                "price": float(p.get("selling_price") or p.get("price") or 0),
                "thumbnail": p.get("thumbnail_url") or p.get("thumbnail"),
                "rating": float(p.get("average_rating") or p.get("rating") or 0),
                "reviews": p.get("total_reviews") or p.get("reviews") or 0,
                "in_stock": p.get("in_stock", False) or (p.get("stock_quantity", 0) > 0)
            })
        
        # Send text + custom data for ProductCarousel
        dispatcher.utter_message(
            text="Here are some recommendations for you:",
            json_message={
                "type": "product_list",
                "products": product_list
            }
        )
        
        dispatcher.utter_message(
            text="💡 Would you like to know more about any of these? 😊"
        )
        
        return [SlotSet("last_products", products)]


class ActionCompareProducts(Action):
    """Compare two or more products"""
    
    def name(self) -> Text:
        return "action_compare_products"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get product names from entities
        product_names = list(tracker.get_latest_entity_values("product_name"))
        
        if len(product_names) < 2:
            dispatcher.utter_message(
                text="Please specify which products you'd like to compare. For example: 'Compare iPhone 15 and Samsung S24'"
            )
            return []
        
        api_client = get_api_client()
        products = []
        
        # Fetch each product
        for name in product_names[:2]:  # Limit to 2 products
            result = api_client.search_products(name, limit=1)
            if not result.get("error") and result.get("data"):
                products.append(result["data"][0])
        
        if len(products) < 2:
            dispatcher.utter_message(
                text="Sorry, I couldn't find both products. Please verify the product names."
            )
            return []
        
        # Simple comparison without Gemini (avoid business data hallucination)
        p1, p2 = products[0], products[1]
        response = f"**Product Comparison:**\n\n"
        response += f"**1. {p1.get('name')}**\n"
        response += f"💰 Price: {p1.get('selling_price', 0):,.0f}₫\n"
        response += f"📦 Stock: {'✅ Available' if p1.get('total_stock', 0) > 0 else '😢 Out of Stock'}\n"
        if p1.get('category_name'):
            response += f"📂 Category: {p1.get('category_name')}\n"
        response += "\n"
        response += f"**2. {p2.get('name')}**\n"
        response += f"💰 Price: {p2.get('selling_price', 0):,.0f}₫\n"
        response += f"📦 Stock: {'✅ Available' if p2.get('total_stock', 0) > 0 else '😢 Out of Stock'}\n"
        if p2.get('category_name'):
            response += f"📂 Category: {p2.get('category_name')}\n"
        response += "\nWhich one would you like to know more about? 😊"
        
        dispatcher.utter_message(text=response)
        
        return []


# ============================================================================
# CART & PURCHASE ACTIONS - Phase 3 Implementation
# ============================================================================

class ActionAddToCart(Action):
    """
    Add product to cart with size, color, and quantity
    REFACTORED: Support contextual reference (add first one, add number 2)
    """
    
    def name(self) -> Text:
        return "action_add_to_cart"
    
    def _parse_product_index(self, text: str) -> int:
        """Parse product index from contextual references"""
        text_lower = text.lower()
        
        # English patterns
        if "first" in text_lower or "1st" in text_lower or "number 1" in text_lower:
            return 0
        if "second" in text_lower or "2nd" in text_lower or "number 2" in text_lower:
            return 1
        if "third" in text_lower or "3rd" in text_lower or "number 3" in text_lower:
            return 2
        
        # Vietnamese patterns
        if "đầu tiên" in text_lower or "đầu" in text_lower or "số 1" in text_lower or "cái 1" in text_lower:
            return 0
        if "thứ hai" in text_lower or "thứ 2" in text_lower or "số 2" in text_lower or "cái 2" in text_lower:
            return 1
        if "thứ ba" in text_lower or "thứ 3" in text_lower or "số 3" in text_lower or "cái 3" in text_lower:
            return 2
        
        return -1
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        logger.info("🛒 Add to cart requested - DISABLED (advisory mode only)")
        
        dispatcher.utter_message(
            text="I'm here to help you find and explore products! 😊\n\n"
                 "To add items to your cart, simply click on any product card I show you, "
                 "and it will take you to the product detail page where you can:\n"
                 "• View full product information\n"
                 "• Select size and color\n"
                 "• Add to cart\n"
                 "• Read reviews\n\n"
                 "Would you like me to help you find something specific?"
        )
        
        return [
            SlotSet("cart_size", None),
            SlotSet("cart_color", None),
            SlotSet("cart_quantity", 1)
        ]
    

class ActionViewCart(Action):
    """View current cart contents"""
    
    def name(self) -> Text:
        return "action_view_cart"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        logger.info("🛒 View cart requested - DISABLED (advisory mode only)")
        
        dispatcher.utter_message(
            text="I can help you find products, but I don't manage shopping carts! 😊\n\n"
                 "To view or manage your cart:\n"
                 "• Click the cart icon 🛒 in the top navigation\n"
                 "• Or visit the cart page directly on our website\n\n"
                 "Would you like me to help you find more products instead?"
        )
        
        return []


# ============================================================================
# GEMINI AI ACTIONS - Open-ended Query Handling
# ============================================================================

class ActionAskGemini(Action):
    """
    Handle open-ended queries using Gemini AI
    UPDATED: Uses strict system prompt and response validation for academic safety
    """
    
    def name(self) -> Text:
        return "action_ask_gemini"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        confidence = tracker.latest_message.get('intent', {}).get('confidence', 0.0)
        
        if not user_message:
            dispatcher.utter_message(
                text="Could you repeat that? 😊",
                metadata={"source": "rasa_template"}
            )
            return []
        
        logger.info(f"🤖 ActionAskGemini: intent={intent}, confidence={confidence:.2f}, message='{user_message[:50]}...'")
        
        # Get Gemini client (Singleton)
        gemini = get_gemini_client()
        
        if not gemini or not gemini.model:
            logger.warning("⚠️ Gemini not available")
            dispatcher.utter_message(
                text="I can help with product searches, sizing, and style advice! What would you like to know? 😊",
                metadata={"source": "rasa_template"}
            )
            return []
        
        # Create prompt with strict system instructions
        prompt = f"""{GEMINI_SYSTEM_PROMPT}

User question: "{user_message}"

Provide helpful, friendly advice within your allowed scope. Be concise (2-3 sentences)."""
        
        # Call Gemini with timing
        start_time = time.time()
        result = gemini.handle_open_ended_query(prompt)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if isinstance(result, dict) and result.get("success") and result.get("response"):
            # CRITICAL: Validate response before sending to user
            is_valid, safe_response = validate_gemini_response(
                result["response"], 
                user_message
            )
            
            if not is_valid:
                # Gemini violated policy - logged in validate function
                logger.error(f"❌ Gemini response blocked due to policy violation")
            
            logger.info(f"✅ Gemini responded in {response_time_ms}ms (valid={is_valid})")
            
            # LOGGING: Track Gemini usage for academic evaluation
            api_client = get_api_client()
            api_client.log_gemini_call(
                user_message=user_message,
                rasa_intent=intent,
                rasa_confidence=confidence,
                gemini_response=safe_response,
                response_time_ms=response_time_ms,
                is_validated=is_valid,
                metadata={
                    "action": "action_ask_gemini",
                    "with_history": False
                }
            )
            
            # Send safe response with metadata
            dispatcher.utter_message(
                text=safe_response,
                metadata={
                    "source": "gemini_ai",
                    "is_validated": is_valid,
                    "response_time_ms": response_time_ms,
                    "intent": intent,
                    "confidence": confidence
                }
            )
            dispatcher.utter_message(
                text="Can I help with anything else? 😊",
                metadata={"source": "rasa_template"}
            )
        else:
            logger.warning(f"⚠️ Gemini failed to respond")
            dispatcher.utter_message(
                text="I'm here to help with products, styling, and fashion advice! What would you like to know? 😊",
                metadata={"source": "rasa_template"}
            )
        
        return []


class ActionAskGeminiWithHistory(Action):
    """
    Handle open-ended queries with conversation history
    UPDATED: Uses strict system prompt and response validation
    """
    
    def name(self) -> Text:
        return "action_ask_gemini_with_history"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        confidence = tracker.latest_message.get('intent', {}).get('confidence', 0.0)
        
        if not user_message:
            dispatcher.utter_message(
                text="I didn't catch that. Could you please repeat? 😊",
                metadata={"source": "rasa_template"}
            )
            return []
        
        logger.info(f"🤖 ActionAskGeminiWithHistory: intent={intent}, confidence={confidence:.2f}")
        
        # Get Gemini client
        gemini_client = get_gemini_client()
        
        if not gemini_client or not gemini_client.model:
            logger.warning("⚠️ Gemini is disabled")
            dispatcher.utter_message(
                text="I can help you with various questions! What would you like to know? 😊",
                metadata={"source": "rasa_template"}
            )
            return []
        
        # Build conversation history
        conversation_history = []
        events = tracker.events
        
        for event in events[-10:]:  # Last 10 messages
            if event.get('event') == 'user':
                conversation_history.append({
                    'role': 'user',
                    'text': event.get('text', '')
                })
            elif event.get('event') == 'bot':
                conversation_history.append({
                    'role': 'assistant',
                    'text': event.get('text', '')
                })
        
        if not conversation_history:
            logger.warning("⚠️ No conversation history found")
            dispatcher.utter_message(
                text="Let's start fresh! What would you like to know? 😊",
                metadata={"source": "rasa_template"}
            )
            return []
        
        # Format conversation history for prompt
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['text'][:100]}" 
            for msg in conversation_history[-6:]  # Last 6 messages
        ])
        
        # Create prompt with history context
        prompt = f"""{GEMINI_SYSTEM_PROMPT}

Conversation history (for context):
{history_text}

Current user question: "{user_message}"

Provide helpful advice based on the conversation context. Be concise (2-3 sentences)."""
        
        # Call Gemini with timing
        start_time = time.time()
        result = gemini_client.handle_open_ended_query(prompt)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if result.get("success") and result.get("response"):
            # CRITICAL: Validate response
            is_valid, safe_response = validate_gemini_response(
                result["response"], 
                user_message
            )
            
            if not is_valid:
                logger.error(f"❌ Gemini with history violated policy")
            
            logger.info(f"✅ Gemini with history responded in {response_time_ms}ms (valid={is_valid})")
            
            # LOGGING: Track Gemini usage with history
            api_client = get_api_client()
            api_client.log_gemini_call(
                user_message=user_message,
                rasa_intent=intent,
                rasa_confidence=confidence,
                gemini_response=safe_response,
                response_time_ms=response_time_ms,
                is_validated=is_valid,
                metadata={
                    "action": "action_ask_gemini_with_history",
                    "with_history": True,
                    "history_length": len(conversation_history)
                }
            )
            
            dispatcher.utter_message(
                text=safe_response,
                metadata={
                    "source": "gemini_ai",
                    "is_validated": is_valid,
                    "response_time_ms": response_time_ms,
                    "with_history": True
                }
            )
        else:
            logger.error(f"❌ Gemini with history failed: {result.get('error')}")
            dispatcher.utter_message(
                text="I'm here to help! What would you like to know? 😊",
                metadata={"source": "rasa_template"}
            )
        
        return []


# ============================================================================
# FALLBACK & SUPPORT ACTIONS
# ============================================================================

class ActionFallback(Action):
    """
    Handle messages the bot doesn't understand
    UPDATED: Better domain detection and escalation logic
    """
    
    def name(self) -> Text:
        return "action_fallback"
    
    def _is_out_of_scope(self, message: str) -> bool:
        """
        Detect if query is clearly outside fashion/shopping domain
        Returns True if out-of-scope
        """
        message_lower = message.lower()
        
        # Keywords indicating out-of-scope queries
        out_of_scope_keywords = [
            # Weather & News
            "weather", "forecast", "temperature", "rain", "news", "politics",
            
            # Entertainment
            "movie", "film", "music", "song", "concert", "game", "sport",
            
            # Food & Restaurants
            "restaurant", "food", "recipe", "cooking", "eat", "dinner", "lunch",
            
            # Travel & Transportation
            "flight", "hotel", "travel", "vacation", "trip", "booking",
            
            # Technology (non-product)
            "software", "download", "install", "code", "program",
            
            # Health & Medical
            "doctor", "medicine", "health", "disease", "symptom",
            
            # General Knowledge
            "who is", "what is", "when was", "where is", "how to",
            "explain", "define", "meaning of"
        ]
        
        # Check if message contains out-of-scope keywords
        for keyword in out_of_scope_keywords:
            if keyword in message_lower:
                # Double-check it's not about fashion products
                fashion_context = any(w in message_lower for w in [
                    "shirt", "pants", "dress", "jacket", "shoe", "bag", 
                    "clothes", "wear", "fashion", "style", "fit", "size"
                ])
                if not fashion_context:
                    return True
        
        return False
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get("text", "")
        intent = tracker.latest_message.get("intent", {}).get("name", "unknown")
        confidence = tracker.latest_message.get("intent", {}).get("confidence", 0.0)
        
        # Track consecutive fallbacks
        fallback_count = tracker.get_slot("fallback_count") or 0
        fallback_count += 1
        
        logger.info(f"⚠️ Fallback triggered (#{fallback_count}): intent={intent}, confidence={confidence:.2f}, message='{user_message[:50]}...'")
        
        # Check if query is out-of-scope
        if self._is_out_of_scope(user_message):
            logger.info(f"🚫 Out-of-scope query detected: {user_message[:50]}...")
            dispatcher.utter_message(
                text="I'm a fashion shopping assistant, so I can only help with:\n\n"
                     "• Product searches & recommendations 👕\n"
                     "• Sizing, styling & fit advice 📏\n"
                     "• Order tracking & support 📦\n"
                     "• Shipping & return policies 🚚\n\n"
                     "For other topics, please consult the appropriate service! 😊",
                metadata={"source": "rasa_template", "is_fallback": True, "out_of_scope": True}
            )
            return [SlotSet("fallback_count", 0)]  # Reset counter
        
        # Escalate to human after 2 consecutive failures
        if fallback_count >= 2:
            logger.warning(f"⚠️ Multiple fallbacks ({fallback_count}) - offering human escalation")
            dispatcher.utter_message(
                text="I'm having trouble understanding your request. 😅\n\n"
                     "Would you like me to connect you with a human support agent who can help? "
                     "Just say 'I want to speak to support' or 'Contact customer service'. 🙋",
                metadata={"source": "rasa_template", "is_fallback": True, "escalation_offered": True}
            )
            return [SlotSet("fallback_count", fallback_count)]
        
        # Try to use Gemini for open-ended queries
        gemini_client = get_gemini_client()
        
        # Check if Gemini is available
        if gemini_client and gemini_client.model:
            # Use strict system prompt
            prompt = f"""{GEMINI_SYSTEM_PROMPT}

User question: "{user_message}"

Provide helpful advice within your allowed scope. Be concise (2-3 sentences)."""
            
            # Call Gemini with timing
            start_time = time.time()
            rag_result = gemini_client.handle_open_ended_query(prompt)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if rag_result.get("success") and rag_result.get("response"):
                # CRITICAL: Validate response
                is_valid, safe_response = validate_gemini_response(
                    rag_result["response"], 
                    user_message
                )
                
                if not is_valid:
                    logger.error(f"❌ Gemini fallback violated policy")
                
                logger.info(f"✅ Gemini handled fallback in {response_time_ms}ms (valid={is_valid})")
                
                # LOGGING: Track fallback Gemini calls
                api_client = get_api_client()
                api_client.log_gemini_call(
                    user_message=user_message,
                    rasa_intent=intent,
                    rasa_confidence=confidence,
                    gemini_response=safe_response,
                    response_time_ms=response_time_ms,
                    is_validated=is_valid,
                    metadata={
                        "action": "action_fallback",
                        "is_fallback": True,
                        "with_history": False
                    }
                )
                
                dispatcher.utter_message(
                    text=safe_response,
                    metadata={
                        "source": "gemini_ai",
                        "is_validated": is_valid,
                        "response_time_ms": response_time_ms,
                        "intent": intent,
                        "confidence": confidence,
                        "is_fallback": True
                    }
                )
                dispatcher.utter_message(
                    text="Can I help you with anything else? 😊",
                    metadata={"source": "rasa_template"}
                )
                return [SlotSet("fallback_count", 0)]  # Reset counter on success
        
        # Standard fallback if Gemini fails or disabled
        logger.warning(f"⚠️ Gemini not available for fallback: {user_message[:50]}...")
        dispatcher.utter_message(
            text="Sorry, I didn't quite understand that 😅\n\n"
                 "I can help you with:\n"
                 "• Product search & advice (shirts, pants, accessories)\n"
                 "• Size, material, and styling advice\n"
                 "• Order tracking\n"
                 "• Shipping and return policies\n"
                 "• Promotions & discounts\n\n"
                 "What can I help you with? 👕",
            metadata={"source": "rasa_template", "is_fallback": True}
        )
        
        return [SlotSet("fallback_count", fallback_count)]


class ActionCreateSupportTicket(Action):
    """Create a support ticket when chatbot cannot help"""
    
    def name(self) -> Text:
        return "action_create_support_ticket"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get("text", "")
        
        # Get conversation history for context
        events = tracker.events
        conversation_history = []
        for event in events[-10:]:  # Last 5 exchanges
            if event.get("event") in ["user", "bot"]:
                conversation_history.append({
                    "timestamp": event.get("timestamp"),
                    "type": event.get("event"),
                    "text": event.get("text", "")
                })
        
        logger.info("Creating support ticket")
        
        api_client = get_api_client()
        result = api_client.create_support_ticket(
            subject="Chatbot Assistance Request",
            message=f"User needs assistance. Original query: {user_message}",
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        if result.get("error"):
            dispatcher.utter_message(
                text="I apologize, but I'm having trouble creating a support ticket right now. Please contact us directly at support@yourstore.com"
            )
        else:
            ticket_id = result.get("data", {}).get("id", "N/A")
            dispatcher.utter_message(
                text=f"I've created a support ticket (#{ticket_id}) for you. Our team will reach out within 24 hours. Is there anything else I can help with in the meantime?"
            )
        
        return []


# ============================================================================
# UTILITY ACTIONS
# ============================================================================

class ActionDefaultAskAffirmation(Action):
    """Ask user to affirm something"""
    
    def name(self) -> Text:
        return "action_default_ask_affirmation"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="I want to make sure I understand correctly. Can you please confirm or rephrase your request?"
        )
        
        return []
