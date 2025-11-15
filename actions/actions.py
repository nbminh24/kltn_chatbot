"""
Custom Actions for KLTN E-commerce Chatbot
Implements all business logic for chatbot interactions
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import logging

from .api_client import get_api_client
from .gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


# ============================================================================
# PRODUCT SEARCH & INQUIRY ACTIONS
# ============================================================================

class ActionSearchProducts(Action):
    """Search for products based on user query"""
    
    def name(self) -> Text:
        return "action_search_products"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get search query from entities or user message
        product_type = next(tracker.get_latest_entity_values("product_type"), None)
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        
        query = product_type or product_name or tracker.latest_message.get("text", "")
        
        if not query:
            dispatcher.utter_message(text="What product are you looking for?")
            return []


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
        result = api_client.get_sizing_advice(
            product_name=product_name,
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
    """Get styling advice for a garment and occasion."""

    def name(self) -> Text:
        return "action_get_styling_advice"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # For now we use product_name as garment_to_pair
        garment_to_pair = next(tracker.get_latest_entity_values("product_name"), None)
        occasion = next(tracker.get_latest_entity_values("occasion"), "")

        if not garment_to_pair:
            user_text = tracker.latest_message.get("text", "")
            garment_to_pair = user_text

        api_client = get_api_client()
        result = api_client.get_styling_advice(
            garment_to_pair=garment_to_pair,
            occasion=str(occasion),
        )

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "Here are some generic styling tips: pair slim jeans with a clean sneaker, "
                    "and balance oversized tops with more fitted bottoms."
                )
            )
            return []

        advice = result.get("data", {}).get("advice") or result.get("advice")
        if advice:
            dispatcher.utter_message(text=advice)
        else:
            dispatcher.utter_message(
                text=(
                    "You can combine this piece with neutral basics (black, white, navy) "
                    "and simple sneakers for a clean, casual look."
                )
            )

        return []


class ActionGetProductCare(Action):
    """Answer product care / washing questions using backend info."""

    def name(self) -> Text:
        return "action_get_product_care"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        care_property = next(tracker.get_latest_entity_values("care_property"), "")

        if not product_name:
            dispatcher.utter_message(
                text="Which product would you like care instructions for?"
            )
            return []

        api_client = get_api_client()
        result = api_client.get_product_care_info(
            product_name=product_name,
            care_property=str(care_property),
        )

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "As a general rule, wash similar colors together, use gentle cycles, "
                    "and avoid high heat drying to maintain the shape and color."
                )
            )
            return []

        care_text = result.get("data", {}).get("care") or result.get("care")
        if care_text:
            dispatcher.utter_message(text=care_text)
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
        # Note: backend can infer user from JWT; we just log the issue here.
        result = api_client.report_order_error(
            order_number=order_number,
            error_type=str(error_type),
            product_name=product_name,
            quantity=str(quantity),
        )

        # Always create a support ticket as well
        user_message = tracker.latest_message.get("text", "")
        api_client.create_support_ticket(
            subject=f"Order issue reported for {order_number}",
            message=(
                f"Customer reported an order issue. Type: {error_type}, "
                f"product: {product_name}, quantity: {quantity}."
            ),
            user_message=user_message,
            conversation_history=None,
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
        result = api_client.request_return_or_exchange(
            order_number=order_number,
            product_to_return=product_to_return,
            product_to_get=str(product_to_get),
            reason=str(reason),
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
        result = api_client.report_quality_issue(
            product_name=product_name,
            defect_description=str(defect_description),
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
        result = api_client.handle_policy_exception(
            product_name=product_name,
            policy_type=str(policy_type),
            reason=str(reason),
        )

        # Always escalate to human support
        user_message = tracker.latest_message.get("text", "")
        api_client.create_support_ticket(
            subject="Policy exception request",
            message=(
                f"Customer requested a policy exception for product '{product_name}', "
                f"policy '{policy_type}', reason: {reason}."
            ),
            user_message=user_message,
            conversation_history=None,
        )

        dispatcher.utter_message(
            text=(
                "I understand your situation. Normally this policy is strict, but because there is a potential defect, "
                "I have escalated your case to our support team for a manual review."
            )
        )

        return []


class ActionSetStockNotification(Action):
    """Register a stock notification with optional price condition."""

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
        price_condition = next(tracker.get_latest_entity_values("price_condition"), "")

        user_token = tracker.get_slot("user_jwt_token")
        if not user_token:
            dispatcher.utter_message(
                text=(
                    "To receive stock notifications, please sign in so we can link the alert to your account."
                )
            )
            return []

        if not product_name or not size:
            dispatcher.utter_message(
                text=(
                    "Please tell me which product and which size you want to be notified about."
                )
            )
            return []

        api_client = get_api_client()
        result = api_client.set_stock_notification(
            product_name=product_name,
            size=str(size),
            price_condition=str(price_condition),
            user_id="",  # backend can derive user from JWT or session
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
                text=(
                    "Got it! I will notify you when this size is back in stock"
                    + (f" and meets your price condition ({price_condition})." if price_condition else ".")
                )
            )

        return []


class ActionCheckDiscount(Action):
    """Explain why discount codes work or not for the current context."""

    def name(self) -> Text:
        return "action_check_discount"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # Collect all discount_code entities in the message
        discount_codes: List[str] = []
        for ent in tracker.latest_message.get("entities", []):
            if ent.get("entity") == "discount_code" and ent.get("value"):
                discount_codes.append(str(ent.get("value")))

        product_name = next(tracker.get_latest_entity_values("product_name"), "")

        if not discount_codes:
            dispatcher.utter_message(
                text="Please tell me which discount codes you are trying to use."
            )
            return []

        api_client = get_api_client()
        result = api_client.check_discount(
            discount_codes=discount_codes,
            product_name=str(product_name),
        )

        if result.get("error"):
            dispatcher.utter_message(
                text=(
                    "The discount rules can be a bit strict. Some codes cannot be combined or do not apply "
                    "to certain products or sale items. Please check the terms of each code."
                )
            )
            return []

        explanation = result.get("data", {}).get("explanation") or result.get("explanation")
        if explanation:
            dispatcher.utter_message(text=explanation)
        else:
            dispatcher.utter_message(
                text=(
                    "Typically, you can only use one promo code per order and some codes exclude specific "
                    "categories like sale items or leather goods."
                )
            )

        return []
        
        logger.info(f"Searching products with query: {query}")
        
        # Call backend API
        api_client = get_api_client()
        result = api_client.search_products(query, limit=5)
        
        if result.get("error"):
            dispatcher.utter_message(
                text=f"Sorry, I encountered an error while searching: {result.get('message')}"
            )
            return [SlotSet("products_found", False)]
        
        products = result.get("data", [])
        
        if not products:
            dispatcher.utter_message(
                text=f"I couldn't find any products matching '{query}'. Would you like to try a different search or speak with our support team?"
            )
            return [SlotSet("products_found", False)]
        
        # Format and display results
        response = f"I found {len(products)} product(s) for you:\n\n"
        
        for i, product in enumerate(products, 1):
            name = product.get("name", "Unknown")
            price = product.get("price", "N/A")
            stock = product.get("stock", 0)
            status = "✅ In Stock" if stock > 0 else "❌ Out of Stock"
            
            response += f"{i}. **{name}**\n"
            response += f"   💰 Price: ${price}\n"
            response += f"   📦 Status: {status}\n\n"
        
        response += "Would you like more details about any of these products?"
        
        dispatcher.utter_message(text=response)
        
        return [
            SlotSet("products_found", True),
            SlotSet("last_search_query", query),
            SlotSet("last_products", products)
        ]


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
                dispatcher.utter_message(text="Which product would you like to know the price of?")
                return []
        
        logger.info(f"Getting price for product: {product_name}")
        
        # Search for the product
        api_client = get_api_client()
        result = api_client.search_products(product_name, limit=1)
        
        if result.get("error") or not result.get("data"):
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find pricing information for '{product_name}'. Would you like me to search for similar products?"
            )
            return []
        
        product = result["data"][0]
        name = product.get("name")
        price = product.get("price")
        
        dispatcher.utter_message(
            text=f"The **{name}** is priced at **${price}**. Would you like to know more about this product?"
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
            dispatcher.utter_message(text="Which product would you like to check availability for?")
            return []
        
        logger.info(f"Checking availability for: {product_name}")
        
        api_client = get_api_client()
        result = api_client.search_products(product_name, limit=1)
        
        if result.get("error") or not result.get("data"):
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find '{product_name}' in our inventory."
            )
            return []
        
        product = result["data"][0]
        name = product.get("name")
        stock = product.get("stock", 0)
        
        if stock > 0:
            dispatcher.utter_message(
                text=f"Great news! **{name}** is currently in stock with {stock} unit(s) available. Would you like to place an order?"
            )
        else:
            dispatcher.utter_message(
                text=f"Unfortunately, **{name}** is currently out of stock. Would you like me to notify you when it's back in stock or suggest similar alternatives?"
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
                dispatcher.utter_message(text="Which product would you like to know more about?")
                return []
        else:
            api_client = get_api_client()
            result = api_client.search_products(product_name, limit=1)
            
            if result.get("error") or not result.get("data"):
                dispatcher.utter_message(
                    text=f"Sorry, I couldn't find details for '{product_name}'."
                )
                return []
            
            product = result["data"][0]
        
        # Format product details
        name = product.get("name", "Unknown")
        price = product.get("price", "N/A")
        description = product.get("description", "No description available")
        stock = product.get("stock", 0)
        category = product.get("category", "General")
        
        response = f"📦 **{name}**\n\n"
        response += f"💰 **Price:** ${price}\n"
        response += f"📂 **Category:** {category}\n"
        response += f"📋 **Description:**\n{description}\n\n"
        response += f"📦 **Availability:** {'✅ In Stock' if stock > 0 else '❌ Out of Stock'}\n\n"
        response += "Would you like to know anything else about this product?"
        
        dispatcher.utter_message(text=response)
        
        return [SlotSet("last_product", product)]


# ============================================================================
# ORDER TRACKING & MANAGEMENT ACTIONS
# ============================================================================

class ActionTrackOrder(Action):
    """Track order status"""
    
    def name(self) -> Text:
        return "action_track_order"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        order_number = next(tracker.get_latest_entity_values("order_number"), None)
        
        if not order_number:
            dispatcher.utter_message(response="utter_ask_order_number")
            return []
        
        # Get user JWT token from slot (set by frontend)
        user_token = tracker.get_slot("user_jwt_token")
        
        if not user_token:
            dispatcher.utter_message(
                text="To track your order, please sign in to your account first."
            )
            return []
        
        logger.info(f"Tracking order: {order_number}")
        
        # Remove '#' if present
        order_id = order_number.replace("#", "")
        
        api_client = get_api_client()
        result = api_client.get_order_details(order_id, user_token)
        
        if result.get("error"):
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find order {order_number}. Please verify the order number and try again."
            )
            return []
        
        order = result.get("data", {})
        status = order.get("status", "Unknown")
        created_at = order.get("created_at", "N/A")
        total = order.get("total", "N/A")
        
        response = f"📦 **Order {order_number}**\n\n"
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
        
        # Use Gemini to generate personalized recommendations
        gemini_client = get_gemini_client()
        rag_result = gemini_client.generate_response_with_products(
            user_query,
            products
        )
        
        if rag_result.get("success"):
            dispatcher.utter_message(text=rag_result["response"])
        else:
            # Fallback to simple list
            response = "Here are some popular products:\n\n"
            for i, product in enumerate(products[:3], 1):
                response += f"{i}. {product.get('name')} - ${product.get('price')}\n"
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
        
        # Log fallback for improvement
        api_client = get_api_client()
        api_client.log_fallback(user_message, intent, confidence)
        
        # Try to use Gemini for open-ended queries
        gemini_client = get_gemini_client()
        
        # Get conversation history
        events = tracker.events
        conversation_history = []
        for event in events[-6:]:  # Last 3 exchanges
            if event.get("event") == "user":
                conversation_history.append({
                    "role": "user",
                    "text": event.get("text", "")
                })
            elif event.get("event") == "bot":
                conversation_history.append({
                    "role": "assistant",
                    "text": event.get("text", "")
                })
        
        # Try RAG with Gemini if enabled
        if gemini_client.enabled:
            rag_result = gemini_client.handle_open_ended_query(
                user_message,
                conversation_history
            )
            
            if rag_result.get("success") and rag_result.get("response"):
                logger.info(f"RAG successfully handled fallback: {user_message}")
                dispatcher.utter_message(text=rag_result["response"])
                dispatcher.utter_message(
                    text="Mình có thể giúp gì thêm cho bạn không? 😊"
                )
                return []
        
        # Standard fallback if RAG fails or disabled
        logger.warning(f"RAG failed or disabled for: {user_message}")
        dispatcher.utter_message(
            text="Xin lỗi, mình chưa hiểu rõ yêu cầu của bạn 😅\n\n"
                 "Mình có thể hỗ trợ bạn:\n"
                 "• Tìm kiếm & tư vấn sản phẩm (áo, quần, phụ kiện)\n"
                 "• Tư vấn size, chất liệu, phối đồ\n"
                 "• Theo dõi đơn hàng\n"
                 "• Chính sách vận chuyển, đổi trả\n"
                 "• Khuyến mãi & voucher\n\n"
                 "Bạn muốn mình giúp gì nào? 👕"
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
