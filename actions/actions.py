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

logger = logging.getLogger(__name__)


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
        r'^i\s+want\s+to\s+(find|buy|see|search)\s+(a\s+|an\s+|some\s+)?',
        r'^find\s+(me\s+)?(a\s+|an\s+|some\s+)?',
        r'^show\s+(me\s+)?(a\s+|an\s+|some\s+)?',
        r'^search\s+(for\s+)?(a\s+|an\s+|some\s+)?',
        r'^looking\s+for\s+(a\s+|an\s+|some\s+)?',
        r'^(can|could)\s+you\s+(find|show)\s+(me\s+)?(a\s+|an\s+)?',
        r'^i\s+need\s+(a\s+|an\s+|some\s+)?',
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
                text="What are you looking for? Shirts, pants, jackets, or maybe some accessories? 😊"
            )
            return []
        
        # 2. Call Backend API
        try:
            api_client = get_api_client()
            result = api_client.search_products(search_query, limit=5)
            
            logger.info(f"� API Response: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            # 3. Handle different JSON structures (CRITICAL FIX)
            # Backend might return: {"products": [...]} or {"data": [...]} or [...]
            products = []
            if isinstance(result, list):
                products = result
            elif isinstance(result, dict):
                # Try both 'products' and 'data' keys
                products = result.get("products") or result.get("data") or []
            
            # Check for errors
            if isinstance(result, dict) and result.get("error"):
                logger.error(f"❌ API Error: {result.get('error')}")
                dispatcher.utter_message(
                    text="I'm having trouble connecting to the product catalog right now. 🙏"
                )
                return [SlotSet("products_found", False)]
            
            # 4. Display results
            if not products:
                dispatcher.utter_message(
                    text=f"Sorry, I couldn't find any products matching '{search_query}' 😅\n\nCould you describe it differently?"
                )
                return [SlotSet("products_found", False)]
            
            # Format message
            message = f"Found {len(products)} products for '{search_query}':\n\n"
            for i, p in enumerate(products[:5], 1):  # Show top 5
                name = p.get("name", "Unknown Product")
                price = p.get("selling_price") or p.get("price", 0)
                stock = p.get("total_stock") or p.get("stock", 0)
                
                # Format price
                if isinstance(price, (int, float)) and price > 0:
                    price_str = f"{price:,.0f}₫"
                else:
                    price_str = "Contact for price"
                
                stock_icon = "✅" if stock > 0 else "😢"
                message += f"{i}. **{name}** - {price_str} {stock_icon}\n"
            
            if len(products) > 5:
                message += f"\n_(+{len(products) - 5} more products)_\n"
            
            message += "\n💡 Which one interests you? I can provide more details! 😊"
            
            dispatcher.utter_message(text=message)
            
            # Save to slots
            return [
                SlotSet("products_found", True),
                SlotSet("last_search_query", search_query),
                SlotSet("last_products", products[:10])
            ]
            
        except Exception as e:
            logger.error(f"❌ Exception in ActionSearchProducts: {e}")
            dispatcher.utter_message(
                text="Oops, something went wrong. Please try again later! 🙏"
            )
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

        user_token = tracker.get_slot("user_jwt_token")
        if not user_token:
            dispatcher.utter_message(
                text=(
                    "To review issues with a specific order, please sign in first so I can verify your purchases."
                )
            )
            return []

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

        user_token = tracker.get_slot("user_jwt_token")
        if not user_token:
            dispatcher.utter_message(
                text=(
                    "To request an exchange or return, please sign in so I can verify your order details."
                )
            )
            return []

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

        user_token = tracker.get_slot("user_jwt_token")
        if not user_token:
            dispatcher.utter_message(
                text=(
                    "To review a quality issue for a purchase, please sign in so I can check your order history."
                )
            )
            return []

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

        user_token = tracker.get_slot("user_jwt_token")
        if not user_token:
            dispatcher.utter_message(
                text=(
                    "For special policy exceptions, please sign in first so we can verify your purchase."
                )
            )
            return []

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

        user_token = tracker.get_slot("user_jwt_token")
        if not user_token:
            dispatcher.utter_message(
                text=(
                    "To receive stock notifications, please sign in so we can link the alert to your account."
                )
            )
            return []

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
    """Get detailed information about a product"""
    
    def name(self) -> Text:
        return "action_get_product_details"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        
        if not product_name:
            # Check if there's a last product in context
            last_product = tracker.get_slot("last_product")
            if last_product:
                product = last_product
            else:
                # No specific product - show popular/recommended products
                api_client = get_api_client()
                start_time = time.time()
                result = api_client.search_products("popular", limit=5)
                api_time = time.time() - start_time
                logger.info(f"⏱️ API search_products (popular) took {api_time:.3f}s")
                
                if result.get("error") or not result.get("products"):
                    dispatcher.utter_message(
                        text="We have everything from shirts, pants, jackets to accessories! What are you interested in? 😊"
                    )
                    return []
                
                products = result["products"]
                response = "Let me show you our hottest items right now:\n\n"
                for i, prod in enumerate(products[:3], 1):
                    name = prod.get('name', 'Unknown')
                    price = prod.get('selling_price', 0)
                    stock = prod.get('total_stock', 0)
                    
                    if isinstance(price, (int, float)) and price > 0:
                        price_str = f"{price:,.0f}₫"
                    else:
                        price_str = "Contact us"
                    
                    status = "in stock" if stock > 0 else "out of stock"
                    response += f"{i}. **{name}** - {price_str} ({status})\n"
                
                response += "\n💬 You can ask me:\n"
                response += "• 'I want to find a jacket/pants/shoes'\n"
                response += "• 'Show me details about [product name]'\n"
                response += "• 'What size would fit me?'"
                dispatcher.utter_message(text=response)
                return [SlotSet("last_products", products)]
        else:
            api_client = get_api_client()
            start_time = time.time()
            result = api_client.search_products(product_name, limit=1)
            api_time = time.time() - start_time
            logger.info(f"⏱️ API search_products took {api_time:.3f}s")
            
            if result.get("error") or not result.get("products"):
                dispatcher.utter_message(
                    text=f"Hmm, I couldn't find '{product_name}' 😅\n\nCould you try a different name, or would you like me to suggest alternatives?"
                )
                return []
            
            product = result["products"][0]
        
        # Format product details
        name = product.get("name", "Product")
        price = product.get("selling_price", 0)
        description = product.get("description", "High quality product")
        stock = product.get("total_stock", 0)
        category = product.get("category_name", "General")
        
        if isinstance(price, (int, float)) and price > 0:
            price_str = f"{price:,.0f}₫"
        else:
            price_str = "Contact for pricing"
        
        response = f"📦 **{name}**\n\n"
        response += f"💰 Price: {price_str}\n"
        response += f"📂 Category: {category}\n"
        
        if stock > 0:
            response += f"✅ In stock - {stock} units available!\n\n"
        else:
            response += f"😢 Currently out of stock\n\n"
        
        response += f"📝 **Description:**\n{description}\n\n"
        response += "Would you like sizing advice, styling tips, or ready to order? 😊"
        
        dispatcher.utter_message(text=response)
        return [SlotSet("last_product", product)]


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
        
        # Get user JWT token from slot (set by frontend)
        user_token = tracker.get_slot("user_jwt_token")
        
        if not user_token:
            dispatcher.utter_message(
                text="To track your order, please sign in to your account first."
            )
            return []
        
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
            dispatcher.utter_message(
                text="Please provide your order number or tell me which product you ordered."
            )
            return []
        
        # Get order details
        result = api_client.get_order_details(order_id, user_token)
        
        if result.get("error"):
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find order {order_number}. Please verify and try again."
            )
            return []
        
        order = result.get("data", {})
        status = order.get("status", "Unknown")
        created_at = order.get("created_at", "N/A")
        total = order.get("total", "N/A")
        
        response = f"📦 **Order #{order_number}**\n\n"
        response += f"📊 **Status:** {status}\n"
        response += f"📅 **Placed on:** {created_at}\n"
        response += f"💰 **Total:** ${total}\n\n"
        
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
                text="Here's our standard shipping policy: We offer free standard shipping on orders over $50. Standard delivery takes 5-7 business days. Express shipping is available for $15 and takes 2-3 business days."
            )
            return []
        
        content = result.get("data", {}).get("content", "")
        
        if content:
            # If content is too long, summarize with Gemini
            if len(content) > 500:
                gemini_client = get_gemini_client()
                rag_result = gemini_client.generate_response_with_context(
                    "Summarize the shipping policy in 2-3 sentences",
                    content
                )
                
                if rag_result.get("success"):
                    dispatcher.utter_message(text=rag_result["response"])
                else:
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
                text="We accept returns within 30 days of purchase. Items must be unused and in original packaging. Refunds are processed within 5-7 business days."
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
            text="We accept the following payment methods:\n• Credit/Debit Cards (Visa, Mastercard, Amex)\n• PayPal\n• Apple Pay\n• Google Pay\n• Bank Transfer"
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
        
        # Simple product list (Gemini integration optional)
        response = "Here are some popular products:\n\n"
        for i, product in enumerate(products[:3], 1):
            name = product.get('name', 'Unknown')
            price = product.get('selling_price', 0)
            price_str = f"{price:,.0f}₫" if price > 0 else "Contact for price"
            response += f"{i}. {name} - {price_str}\n"
        
        response += "\nWould you like to know more about any of these? 😊"
        dispatcher.utter_message(text=response)
        
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
        
        # Use Gemini for intelligent comparison
        gemini_client = get_gemini_client()
        user_query = tracker.latest_message.get("text", "")

        # Try to extract contextual information if available (e.g. "for someone who is short")
        context_text = ""
        latest_entities = tracker.latest_message.get("entities", [])
        for ent in latest_entities:
            if ent.get("entity") == "context":
                context_text = ent.get("value", "")
                break

        if context_text:
            prompt = (
                "Compare these products and give advice based on this context: "
                f"'{context_text}'. Original user query: {user_query}"
            )
        else:
            prompt = f"Compare these products: {user_query}"

        rag_result = gemini_client.generate_response_with_products(
            prompt,
            products
        )
        
        if rag_result.get("success"):
            dispatcher.utter_message(text=rag_result["response"])
        else:
            # Fallback comparison
            p1, p2 = products[0], products[1]
            response = f"**Comparison:**\n\n"
            response += f"**{p1.get('name')}**\n"
            response += f"Price: ${p1.get('price')}\n"
            response += f"Stock: {'Available' if p1.get('stock', 0) > 0 else 'Out of Stock'}\n\n"
            response += f"**{p2.get('name')}**\n"
            response += f"Price: ${p2.get('price')}\n"
            response += f"Stock: {'Available' if p2.get('stock', 0) > 0 else 'Out of Stock'}\n"
            
            dispatcher.utter_message(text=response)
        
        return []


# ============================================================================
# CART & PURCHASE ACTIONS - Phase 3 Implementation
# ============================================================================

class ActionAddToCart(Action):
    """
    Add product to cart with size, color, and quantity
    Uses Rasa Forms for slot filling
    """
    
    def name(self) -> Text:
        return "action_add_to_cart"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get filled slots from form
        product_id = tracker.get_slot("current_product_id")
        size = tracker.get_slot("cart_size")
        color = tracker.get_slot("cart_color")
        quantity = tracker.get_slot("cart_quantity") or 1
        
        logger.info(f"🛒 Adding to cart: product_id={product_id}, size={size}, color={color}, qty={quantity}")
        
        # Validate required fields
        if not product_id:
            dispatcher.utter_message(
                text="I need to know which product you want to add. Could you search for a product first? 😊"
            )
            return []
        
        if not size:
            dispatcher.utter_message(
                text="What size would you like? (S, M, L, XL, etc.)"
            )
            return []
        
        if not color:
            dispatcher.utter_message(
                text="What color would you prefer?"
            )
            return []
        
        # Call Backend API to add to cart
        try:
            api_client = get_api_client()
            
            # Prepare cart data
            cart_data = {
                "product_id": int(product_id),
                "size": size,
                "color": color,
                "quantity": int(quantity)
            }
            
            logger.info(f"📤 Calling backend add_to_cart API with: {cart_data}")
            
            # Call API (assuming you have this method in api_client)
            result = api_client.add_to_cart(cart_data)
            
            # Handle response
            if isinstance(result, dict):
                if result.get("success") or result.get("data"):
                    # Success
                    product_name = result.get("product_name", "Product")
                    dispatcher.utter_message(
                        text=f"✅ Added {product_name} ({size}, {color}) to your cart!\n\n"
                             f"Quantity: {quantity}\n\n"
                             f"Would you like to continue shopping or check out? 🛍️"
                    )
                    
                    # Reset cart slots for next add
                    return [
                        SlotSet("cart_size", None),
                        SlotSet("cart_color", None),
                        SlotSet("cart_quantity", 1)
                    ]
                elif result.get("error"):
                    # API error
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"❌ Backend error: {error_msg}")
                    dispatcher.utter_message(
                        text=f"Sorry, I couldn't add that to your cart. {error_msg} 😅"
                    )
            else:
                # Unexpected response
                logger.error(f"❌ Unexpected API response: {result}")
                dispatcher.utter_message(
                    text="Something went wrong while adding to cart. Please try again! 🙏"
                )
        
        except AttributeError:
            # API client doesn't have add_to_cart method yet
            logger.warning("⚠️ api_client.add_to_cart() not implemented yet")
            dispatcher.utter_message(
                text=f"✅ (Mock) Added to cart: Size {size}, Color {color}, Qty {quantity}\n\n"
                     f"💡 Note: Backend API integration pending."
            )
            return [
                SlotSet("cart_size", None),
                SlotSet("cart_color", None),
                SlotSet("cart_quantity", 1)
            ]
        
        except Exception as e:
            logger.error(f"❌ Exception in add_to_cart: {e}")
            dispatcher.utter_message(
                text="Oops, something went wrong. Please try again later! 🙏"
            )
        
        return []


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
        
        logger.info("🛒 Viewing cart")
        
        try:
            api_client = get_api_client()
            result = api_client.get_cart()
            
            if isinstance(result, dict) and result.get("items"):
                items = result.get("items", [])
                total = result.get("total", 0)
                
                message = "🛍️ Your Cart:\n\n"
                for i, item in enumerate(items, 1):
                    name = item.get("product_name", "Product")
                    size = item.get("size", "")
                    color = item.get("color", "")
                    qty = item.get("quantity", 1)
                    price = item.get("price", 0)
                    
                    message += f"{i}. {name} ({size}, {color}) x{qty} - {price:,.0f}₫\n"
                
                message += f"\n**Total: {total:,.0f}₫**\n\n"
                message += "Ready to check out? 😊"
                
                dispatcher.utter_message(text=message)
            else:
                dispatcher.utter_message(
                    text="Your cart is empty! 🛒\n\nWould you like to search for products? 😊"
                )
        
        except AttributeError:
            logger.warning("⚠️ api_client.get_cart() not implemented yet")
            dispatcher.utter_message(
                text="🛒 (Mock) Your cart:\n\n"
                     "1. Sample Product (M, Blue) x1 - 150,000₫\n\n"
                     "💡 Note: Backend API integration pending."
            )
        except Exception as e:
            logger.error(f"❌ Exception in view_cart: {e}")
            dispatcher.utter_message(
                text="I couldn't retrieve your cart right now. Please try again! 🙏"
            )
        
        return []


# ============================================================================
# GEMINI AI ACTIONS - Open-ended Query Handling
# ============================================================================

class ActionAskGemini(Action):
    """
    Handle open-ended queries using Gemini AI
    REFACTORED: Simplified prompt structure
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
        
        if not user_message:
            dispatcher.utter_message(text="Could you repeat that? 😊")
            return []
        
        logger.info(f"🤖 ActionAskGemini: {user_message[:50]}...")
        
        # Get Gemini client (Singleton)
        gemini = get_gemini_client()
        
        if not gemini or not gemini.model:
            logger.warning("⚠️ Gemini not available")
            dispatcher.utter_message(
                text="I can help with product searches, sizing, and style advice! What would you like to know? 😊"
            )
            return []
        
        # Create simple prompt with context
        prompt = f"""You are a helpful fashion sales assistant.
User said: "{user_message}"

Please answer in English, be concise (2-3 sentences) and helpful. 
If it's chitchat, be friendly. If it's about fashion advice, give practical suggestions."""
        
        # Call Gemini
        result = gemini.handle_open_ended_query(prompt)
        
        if isinstance(result, dict) and result.get("success") and result.get("response"):
            dispatcher.utter_message(text=result["response"])
            dispatcher.utter_message(text="Can I help with anything else? 😊")
        else:
            dispatcher.utter_message(
                text="I'm here to help with products, styling, and fashion advice! What would you like to know? 😊"
            )
        
        return []


class ActionAskGeminiWithHistory(Action):
    """
    Handle open-ended queries with conversation history
    Provides contextual responses based on previous messages
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
        
        if not user_message:
            dispatcher.utter_message(
                text="I didn't catch that. Could you please repeat? 😊"
            )
            return []
        
        logger.info(f"🤖 ActionAskGeminiWithHistory: Processing query with history")
        
        # Get Gemini client
        gemini_client = get_gemini_client()
        
        if not gemini_client.enabled:
            logger.warning("⚠️ Gemini is disabled")
            dispatcher.utter_message(
                text="I can help you with various questions! What would you like to know? 😊"
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
            dispatcher.utter_message(text="Let's start fresh! What would you like to know? 😊")
            return []
        
        # Add e-commerce context
        context = """You are a knowledgeable fashion e-commerce assistant.
        Use the conversation history to provide contextual, helpful responses.
        Reference previous topics when relevant."""
        
        # Generate with history
        result = gemini_client.generate_response_with_context(
            user_query=user_message,
            context=context,
            conversation_history=conversation_history
        )
        
        if result.get("success") and result.get("response"):
            logger.info(f"✅ Gemini with history responded successfully")
            dispatcher.utter_message(text=result["response"])
        else:
            logger.error(f"❌ Gemini with history failed: {result.get('error')}")
            # Fallback to simple response
            dispatcher.utter_message(
                text="I'm here to help! What would you like to know? 😊"
            )
        
        return []


# ============================================================================
# FALLBACK & SUPPORT ACTIONS
# ============================================================================

class ActionFallback(Action):
    """Handle messages the bot doesn't understand"""
    
    def name(self) -> Text:
        return "action_fallback"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get("text", "")
        intent = tracker.latest_message.get("intent", {}).get("name", "unknown")
        confidence = tracker.latest_message.get("intent", {}).get("confidence", 0.0)
        
        logger.info(f"Fallback triggered for message: {user_message} (intent: {intent}, confidence: {confidence})")
        
        # Removed: Backend logging (causes 401 error when backend offline)
        # api_client = get_api_client()
        # api_client.log_fallback(user_message, intent, confidence)
        
        # Try to use Gemini for open-ended queries
        gemini_client = get_gemini_client()
        
        # Check if Gemini is available
        if gemini_client and gemini_client.model:
            # Create simple prompt
            prompt = f"""You are a helpful fashion e-commerce assistant.
User said: "{user_message}"

Please answer in English, be concise (2-3 sentences) and helpful."""
            
            rag_result = gemini_client.handle_open_ended_query(prompt)
            
            if rag_result.get("success") and rag_result.get("response"):
                logger.info(f"✅ Gemini handled fallback: {user_message[:50]}...")
                dispatcher.utter_message(text=rag_result["response"])
                dispatcher.utter_message(text="Can I help you with anything else? 😊")
                return []
        
        # Standard fallback if RAG fails or disabled
        logger.warning(f"RAG failed or disabled for: {user_message}")
        dispatcher.utter_message(
            text="Sorry, I didn't quite understand that 😅\n\n"
                 "I can help you with:\n"
                 "• Product search & advice (shirts, pants, accessories)\n"
                 "• Size, material, and styling advice\n"
                 "• Order tracking\n"
                 "• Shipping and return policies\n"
                 "• Promotions & discounts\n\n"
                 "What can I help you with? 👕"
        )
        
        return []


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
