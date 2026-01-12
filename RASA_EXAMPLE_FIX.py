# 🔧 Rasa Actions - Example Fix for Intent Tracking

"""
Team AI: This is an example showing EXACTLY how to add intent to dispatcher.utter_message()
Copy this pattern to ALL your custom actions.
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


# ====================================
# Helper Function (Already implemented by Team AI)
# ====================================
def get_intent_from_tracker(tracker: Tracker) -> str:
    """Extract intent from tracker"""
    try:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        return intent
    except Exception as e:
        return 'unknown'


# ====================================
# ❌ BEFORE (WRONG - No metadata)
# ====================================
class ActionSearchProductsBEFORE(Action):
    def name(self) -> Text:
        return "action_search_products"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_name = get_intent_from_tracker(tracker)  # ← Get intent
        
        # Search products...
        products = self.search_products("áo meow")
        
        # ❌ WRONG: No metadata parameter
        dispatcher.utter_message(
            text=f"Found {len(products)} products",
            custom={"type": "product_list", "products": products}
        )
        
        return []


# ====================================
# ✅ AFTER (CORRECT - With metadata)
# ====================================
class ActionSearchProductsAFTER(Action):
    def name(self) -> Text:
        return "action_search_products"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_name = get_intent_from_tracker(tracker)  # ← Get intent
        
        # Search products...
        products = self.search_products("áo meow")
        
        # ✅ CORRECT: Add metadata parameter with intent
        dispatcher.utter_message(
            text=f"Found {len(products)} products",
            metadata={"intent": intent_name},  # ← ADD THIS LINE!
            custom={"type": "product_list", "products": products}
        )
        
        return []


# ====================================
# ✅ More Examples
# ====================================

class ActionTrackOrder(Action):
    """Example: Order tracking"""
    def name(self) -> Text:
        return "action_track_order"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_name = get_intent_from_tracker(tracker)
        
        # Get order info...
        order = self.get_order_info(tracker)
        
        # ✅ Send with metadata
        dispatcher.utter_message(
            text=f"Your order #{order['id']} is {order['status']}",
            metadata={"intent": intent_name}  # ← Always add this!
        )
        
        return []


class ActionGetStylingAdvice(Action):
    """Example: Styling advice"""
    def name(self) -> Text:
        return "action_get_styling_advice"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_name = get_intent_from_tracker(tracker)
        
        # Get recommendations...
        suggestions = self.get_styling_suggestions(tracker)
        
        # ✅ Multiple messages - ALL need metadata
        dispatcher.utter_message(
            text="Here are some styling suggestions:",
            metadata={"intent": intent_name}  # ← Add to first message
        )
        
        dispatcher.utter_message(
            text="You can pair these items...",
            metadata={"intent": intent_name},  # ← Add to second message
            custom={"type": "product_list", "products": suggestions}
        )
        
        return []


class ActionFallback(Action):
    """Example: Fallback action"""
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_name = get_intent_from_tracker(tracker)
        
        # ✅ Even fallback needs metadata!
        dispatcher.utter_message(
            text="Sorry, I didn't understand that.",
            metadata={"intent": intent_name}  # ← Add metadata even for fallback
        )
        
        return []


# ====================================
# 📋 CHECKLIST FOR TEAM AI
# ====================================
"""
For EVERY action in your codebase:

1. Find all dispatcher.utter_message() calls
2. Add get_intent_from_tracker(tracker) at the start
3. Add metadata={"intent": intent_name} to EVERY utter_message() call
4. Test and verify backend logs show intent

Actions to check:
- ActionSearchProducts ✓
- ActionSearchByPrice ✓
- ActionGetSizingAdvice ✓
- ActionGetStylingAdvice ✓
- ActionTrackOrder ✓
- ActionCancelOrder ✓
- ActionCheckAvailability ✓
- ActionAddToCart ✓
- ActionViewCart ✓
- ActionRecommendProducts ✓
- ActionCompareProducts ✓
- ActionAskGemini ✓
- ActionGetShippingPolicy ✓
- ActionGetReturnPolicy ✓
- ActionRequestHuman ✓
- ActionDefaultFallback ✓
... and ALL other actions
"""
