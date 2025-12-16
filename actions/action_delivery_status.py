"""
Order Delivery Status Action
Provides customers with estimated delivery dates and shipping information.
Backend calculates all dates - chatbot only displays them (deterministic approach).
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import logging

from .api_client import get_api_client

logger = logging.getLogger(__name__)


def get_customer_id_from_tracker(tracker: Tracker) -> int:
    """Extract customer_id from tracker metadata or slots"""
    metadata = tracker.latest_message.get("metadata", {})
    customer_id = metadata.get("customer_id") or tracker.get_slot("customer_id")
    
    if customer_id:
        try:
            return int(customer_id)
        except (ValueError, TypeError):
            return None
    return None


def get_jwt_token_from_tracker(tracker: Tracker) -> str:
    """Extract JWT token from tracker metadata or slots"""
    metadata = tracker.latest_message.get("metadata", {})
    return metadata.get("user_jwt_token") or tracker.get_slot("user_jwt_token")


class ActionGetDeliveryStatus(Action):
    """
    Get delivery status and estimated delivery date for an order.
    
    This action:
    - Calls backend API to get delivery estimation
    - Displays status-specific messages (pending/shipping/delivered)
    - Shows estimated delivery dates (calculated by backend)
    - Provides tracking links when available
    
    Does NOT:
    - Calculate delivery dates (backend does this)
    - Use LLM to generate dates
    - Make delivery guarantees
    """
    
    def name(self) -> Text:
        return "action_get_delivery_status"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Extract order number and authentication
        order_number = next(tracker.get_latest_entity_values("order_number"), None)
        customer_id = get_customer_id_from_tracker(tracker)
        user_token = get_jwt_token_from_tracker(tracker)
        
        logger.info(f"Delivery status inquiry - Order: {order_number}, Customer: {customer_id}")
        
        # Require authentication
        if not customer_id or not user_token:
            dispatcher.utter_message(
                text="To check delivery status, please sign in to your account first."
            )
            return []
        
        # Require order number
        if not order_number:
            dispatcher.utter_message(
                text="Please provide your order number so I can check the delivery status.\n\nExample: \"Check delivery for order 0000000032\""
            )
            return []
        
        # Call backend API for delivery estimation
        api_client = get_api_client()
        order_id = order_number.replace("#", "")
        
        try:
            result = api_client.get_delivery_estimation(order_id, user_token)
        except Exception as e:
            logger.error(f"Failed to get delivery estimation: {e}")
            dispatcher.utter_message(
                text="Sorry, I couldn't retrieve delivery information at the moment. Please try again later."
            )
            return []
        
        # Handle errors
        if result.get("error"):
            error_msg = result.get("message", "")
            if "not found" in error_msg.lower():
                dispatcher.utter_message(
                    text=f"Sorry, I couldn't find delivery information for order {order_number}. Please verify your order number."
                )
            else:
                dispatcher.utter_message(
                    text="Sorry, I couldn't retrieve your order information. Please try again."
                )
            return []
        
        # Format response based on order status
        status = result.get("status", "").lower()
        order_num = result.get("order_number", order_number)
        message_from_backend = result.get("message", "")
        
        logger.info(f"Order {order_num} status: {status}")
        
        # Status: pending
        if status == "pending":
            response = f"📦 **Order #{order_num}**\n\n"
            response += "Your order is currently **pending confirmation** and has not been shipped yet.\n\n"
            response += "Once it is confirmed and shipped, we'll be able to provide an estimated delivery date.\n\n"
            response += "Would you like to know more about our delivery options?"
            
        # Status: confirmed / processing
        elif status in ["confirmed", "processing"]:
            response = f"📦 **Order #{order_num}**\n\n"
            response += "Your order has been **confirmed** and is being prepared for shipment.\n\n"
            response += "Once it is shipped, we'll update you with an estimated delivery date and tracking details.\n\n"
            response += "💡 Standard delivery typically takes:\n"
            response += "• Major cities: 1-2 business days\n"
            response += "• Other provinces: 3-5 business days"
            
        # Status: shipping / shipped (MOST IMPORTANT - WITH DELIVERY DATE)
        elif status in ["shipping", "shipped"]:
            estimated = result.get("estimated_delivery", {})
            delivery_date = estimated.get("formatted", "")
            delivery_from = estimated.get("from", "")
            delivery_to = estimated.get("to", "")
            tracking_url = result.get("tracking_url", "")
            destination = result.get("destination", {})
            city = destination.get("city", "")
            shipping_method = result.get("shipping_method", "standard")
            
            response = f"📦 **Order #{order_num}**\n\n"
            response += "🚚 Your order is currently **on the way**!\n\n"
            
            # Show estimated delivery date
            if delivery_date:
                response += f"📅 **Expected delivery date:** {delivery_date}\n"
            elif delivery_from and delivery_to:
                response += f"📅 **Expected delivery:** Between {delivery_from} and {delivery_to}\n"
            
            # Show destination
            if city:
                response += f"📍 **Destination:** {city}\n"
            
            # Show shipping method
            if shipping_method:
                method_display = shipping_method.replace("_", " ").title()
                response += f"🚚 **Shipping method:** {method_display}\n"
            
            # Show tracking link
            if tracking_url:
                response += f"\n🔍 **Track your package in real-time:**\n{tracking_url}\n"
            
            response += "\nIs there anything else you'd like to know about your delivery?"
            
        # Status: delivered
        elif status == "delivered":
            estimated = result.get("estimated_delivery", {})
            actual_date = estimated.get("formatted", "")
            
            response = f"📦 **Order #{order_num}**\n\n"
            response += "✅ Your order has been **delivered**"
            
            if actual_date:
                response += f" on **{actual_date}**"
            
            response += ".\n\n"
            response += "If you haven't received it yet or have any concerns about the delivery, please let me know and I'll help you contact our support team."
            
        # Status: cancelled
        elif status == "cancelled":
            response = f"📦 **Order #{order_num}**\n\n"
            response += "❌ This order has been **cancelled**.\n\n"
            response += "If you have any questions about this cancellation, please contact our support team."
            
        # Other statuses
        else:
            response = f"📦 **Order #{order_num}**\n\n"
            response += f"Current status: **{status.title()}**\n\n"
            
            if message_from_backend:
                response += f"{message_from_backend}\n\n"
            
            response += "For detailed information, please contact our support team."
        
        dispatcher.utter_message(text=response)
        return []
