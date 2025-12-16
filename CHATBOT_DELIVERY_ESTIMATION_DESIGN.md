# Chatbot Design: Order Delivery Estimation Feature

## 📋 Overview

**Feature:** Intelligent delivery status and estimation inquiry  
**Language:** English  
**Approach:** Deterministic (backend-calculated dates, not LLM-generated)  
**Priority:** Medium  

---

## 🎯 User Stories

1. **As a customer**, I want to know when my order will arrive, so I can plan accordingly.
2. **As a customer**, I want to understand why my order hasn't shipped yet, so I have clear expectations.
3. **As a customer**, I want tracking information for shipped orders, so I can monitor delivery progress.

---

## 🗣️ Conversation Flows

### **Flow 1: Order Status = `pending`**

```
User: "When will I receive my order?"

Chatbot:
"Your order #0000000032 is currently pending confirmation and has not been shipped yet.
Once it is confirmed and shipped, we'll be able to provide an estimated delivery date.
Would you like to know more about our delivery options?"
```

---

### **Flow 2: Order Status = `confirmed`**

```
User: "When will my order arrive?"

Chatbot:
"Your order #0000000032 has been confirmed and is being prepared for shipment.
Once it is shipped, we'll update you with an estimated delivery date and tracking details.
Standard delivery typically takes 3-5 business days for most locations."
```

---

### **Flow 3: Order Status = `shipping` (WITH DELIVERY DATE)**

**Backend Response:**
```json
{
  "order_number": "0000000032",
  "status": "shipping",
  "estimated_delivery": {
    "date": "2025-03-19",
    "formatted": "March 19, 2025",
    "from": "2025-03-18",
    "to": "2025-03-20"
  },
  "tracking_url": "https://carrier.vn/track/XYZ123"
}
```

**Chatbot Response:**
```
📦 Your order #0000000032 is currently on the way!

📅 Expected delivery date: March 19, 2025
📍 Destination: Ho Chi Minh City

You can track your package in real-time:
🔗 Track Order: https://carrier.vn/track/XYZ123

Is there anything else you'd like to know about your delivery?
```

---

### **Flow 4: Order Status = `delivered`**

**Backend Response:**
```json
{
  "status": "delivered",
  "estimated_delivery": {
    "actual_date": "2025-03-18",
    "formatted": "March 18, 2025"
  }
}
```

**Chatbot Response:**
```
✅ According to our system, your order #0000000032 was delivered on March 18, 2025.

If you haven't received it yet or have any concerns, please let me know and I'll help you contact our support team.
```

---

### **Flow 5: Delivery Delayed (Future Enhancement)**

```
User: "My order is late. Where is it?"

Chatbot:
"I understand your concern. Let me check your order status.

Your order #0000000032 was expected to arrive by March 19, 2025, but appears to be delayed.
Current tracking shows it's still in transit.

I've created a support ticket for you (Ticket #T12345) and our team will investigate immediately.
Would you like me to provide contact information for urgent assistance?"
```

---

### **Flow 6: General Delivery Options Inquiry**

```
User: "What delivery options do you offer?"

Chatbot (Static CMS Response):
"🚚 Delivery Options

**Standard Delivery**
• 3-5 Business Days
• Free (Domestic)

**Express Delivery**
• 1-2 Business Days
• $15.99

**Next Day Delivery**
• Order by 2PM
• $24.99

We ship nationwide across Vietnam with free domestic delivery.
International shipping is also available to selected regions.

Would you like to know more about international shipping?"
```

---

## 🔧 Technical Implementation

### **New Chatbot Action: `action_get_delivery_status`**

**Triggers:**
- Intent: `check_delivery_status`
- Entity: `order_number`

**NLU Training Examples:**
```yaml
- intent: check_delivery_status
  examples: |
    - when will I receive my order?
    - when will my order arrive?
    - delivery date for order [0000000032](order_number)
    - where is my order?
    - how long until my order arrives?
    - estimated delivery time
    - when can I expect my package?
    - delivery status for [0000000032](order_number)
    - track my delivery
```

**Action Logic:**

```python
class ActionGetDeliveryStatus(Action):
    def name(self) -> Text:
        return "action_get_delivery_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract order number and customer authentication
        order_number = next(tracker.get_latest_entity_values("order_number"), None)
        customer_id = get_customer_id_from_tracker(tracker)
        user_token = get_jwt_token_from_tracker(tracker)
        
        if not customer_id or not user_token:
            dispatcher.utter_message(
                text="To check delivery status, please sign in to your account first."
            )
            return []
        
        if not order_number:
            dispatcher.utter_message(
                text="Please provide your order number so I can check the delivery status."
            )
            return []
        
        # Call backend API for delivery estimation
        api_client = BackendAPIClient()
        result = api_client.get_delivery_estimation(order_number, user_token)
        
        if result.get("error"):
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find delivery information for order {order_number}."
            )
            return []
        
        # Format response based on order status
        status = result.get("status", "").lower()
        order_num = result.get("order_number", order_number)
        
        if status == "pending":
            response = f"Your order #{order_num} is currently pending confirmation and has not been shipped yet.\n\n"
            response += "Once it is confirmed and shipped, we'll be able to provide an estimated delivery date.\n"
            response += "Would you like to know more about our delivery options?"
            
        elif status == "confirmed":
            response = f"Your order #{order_num} has been confirmed and is being prepared for shipment.\n\n"
            response += "Once it is shipped, we'll update you with an estimated delivery date and tracking details.\n"
            response += "Standard delivery typically takes 3-5 business days for most locations."
            
        elif status == "shipping":
            estimated = result.get("estimated_delivery", {})
            delivery_date = estimated.get("formatted", "")
            tracking_url = result.get("tracking_url", "")
            destination = result.get("destination", {})
            city = destination.get("city", "")
            
            response = f"📦 Your order #{order_num} is currently on the way!\n\n"
            
            if delivery_date:
                response += f"📅 **Expected delivery date:** {delivery_date}\n"
            
            if city:
                response += f"📍 **Destination:** {city}\n"
            
            if tracking_url:
                response += f"\nYou can track your package in real-time:\n"
                response += f"🔗 {tracking_url}\n"
            
            response += "\nIs there anything else you'd like to know about your delivery?"
            
        elif status == "delivered":
            estimated = result.get("estimated_delivery", {})
            actual_date = estimated.get("formatted", "")
            
            response = f"✅ According to our system, your order #{order_num} was delivered"
            if actual_date:
                response += f" on {actual_date}"
            response += ".\n\n"
            response += "If you haven't received it yet or have any concerns, please let me know."
            
        else:
            response = f"Your order #{order_num} status: {status.title()}\n\n"
            response += "For detailed information, please contact our support team."
        
        dispatcher.utter_message(text=response)
        return []
```

---

### **Backend API Client Method**

**New method in `api_client.py`:**

```python
def get_delivery_estimation(self, order_id: str, auth_token: str = None) -> Dict[str, Any]:
    """
    Get delivery estimation for an order.
    
    Args:
        order_id: Order number (e.g., "0000000032")
        auth_token: JWT authentication token
        
    Returns:
        Dictionary containing delivery estimation data
    """
    params = {"order_id": order_id}
    return self._make_request(
        "GET",
        "/orders/track/delivery-estimation",
        params=params,
        auth_token=auth_token
    )
```

---

## 📚 NLU Intent Design

### **Intent: `check_delivery_status`**

**Training Examples (50+ recommended):**

```yaml
- intent: check_delivery_status
  examples: |
    - when will I receive my order?
    - when will my order arrive?
    - when can I expect my order?
    - delivery date for order [0000000032](order_number)
    - estimated delivery time
    - how long until my order arrives?
    - where is my order?
    - when is my package coming?
    - delivery status
    - track my delivery
    - shipping information
    - when will it be delivered?
    - expected delivery date
    - arrival time
    - when should I expect my package?
    - delivery estimate
    - how many days until delivery?
    - when will this arrive?
    - check delivery status for [0000000001](order_number)
    - my order [0000000032](order_number) delivery date
    - order [0000000015](order_number) when will it arrive?
```

---

## 🎨 Response Templates (domain.yml)

```yaml
responses:
  utter_ask_delivery_options:
    - text: |
        🚚 **Delivery Options**
        
        **Standard Delivery**
        • 3-5 Business Days
        • Free (Domestic)
        
        **Express Delivery**
        • 1-2 Business Days
        • $15.99
        
        **Next Day Delivery**
        • Order by 2PM
        • $24.99
        
        We ship nationwide across Vietnam with free domestic delivery.
        International shipping is also available to selected regions.

  utter_delivery_international:
    - text: |
        🌍 **International Shipping**
        
        **Asia** (Thailand, Singapore, Malaysia, etc.)
        • 5-7 business days - $8.99
        
        **Rest of the world**
        • 10-14 business days - $15.99
        
        Express international shipping available upon request.
        
        Note: Customs duties and taxes may apply depending on your country's regulations.
```

---

## 🧪 Testing Scenarios

### **Test 1: Pending Order**
```
Input: "when will my order arrive? order number is 0000000001"
Expected: Message explaining order is pending, delivery date unavailable
```

### **Test 2: Shipping Order with Date**
```
Input: "delivery status for 0000000032"
Expected: Estimated delivery date (March 19, 2025), tracking link
```

### **Test 3: Delivered Order**
```
Input: "where is order 0000000025?"
Expected: Confirmation of delivery with actual date
```

### **Test 4: No Authentication**
```
Input: "when will my order arrive?" (not logged in)
Expected: "Please sign in to check delivery status"
```

### **Test 5: General Delivery Inquiry**
```
Input: "what delivery options do you have?"
Expected: Static response with delivery options (not order-specific)
```

---

## 📊 Analytics & Logging

**Events to Track:**
- `delivery_status_checked` - Customer checked delivery status
- `delivery_date_provided` - System provided estimated date
- `tracking_link_clicked` - Customer clicked tracking link
- `delivery_delayed_inquiry` - Customer asked about delayed order

**Logs to Capture:**
```python
logger.info(f"Delivery status checked for order {order_number} by customer {customer_id}")
logger.info(f"Estimated delivery: {delivery_date}, Status: {status}")
```

---

## 🚫 What the Chatbot Should NOT Do

❌ **DO NOT** calculate delivery dates autonomously  
❌ **DO NOT** use LLM to generate delivery dates  
❌ **DO NOT** promise guaranteed delivery dates (use "estimated" or "expected")  
❌ **DO NOT** provide tracking information from external carriers directly  
❌ **DO NOT** handle delivery complaints without escalating to support  

✅ **DO** rely on backend API for all date calculations  
✅ **DO** use clear, customer-friendly language  
✅ **DO** provide tracking links when available  
✅ **DO** escalate to human support when issues detected  

---

## 📝 Academic Justification (for Report)

> "The chatbot provides delivery date information based on **estimated delivery data calculated and returned by backend services**.  
> Rather than generating delivery dates autonomously, the system relies on **deterministic shipping rules** and order status to ensure correctness and avoid misleading commitments.  
> This approach improves user experience while maintaining **reliability and auditability**."

**Key Terms:**
- **Deterministic**: Rule-based, not probabilistic
- **Backend-calculated**: Not LLM-generated
- **Estimated**: Not guaranteed
- **Auditable**: Traceable and verifiable

---

## 🔄 Future Enhancements (Phase 2)

1. **Proactive Notifications**
   - "Your order will arrive tomorrow!"
   - "Your delivery is delayed. New estimated date: ..."

2. **Delivery Preferences**
   - "Would you like to change your delivery address?"
   - "Reschedule delivery to a different date"

3. **Real-time Carrier Integration**
   - Live tracking updates from shipping carriers
   - GPS-based delivery location

4. **Delivery Issues Automation**
   - Auto-detect delayed deliveries
   - Create support tickets automatically
   - Offer compensation for late deliveries

---

## ✅ Implementation Checklist

- [ ] Create `action_get_delivery_status` in `actions.py`
- [ ] Add `get_delivery_estimation()` method to `api_client.py`
- [ ] Create NLU intent `check_delivery_status` with 50+ examples
- [ ] Add entity `order_number` examples to NLU
- [ ] Create response templates in `domain.yml`
- [ ] Update stories for delivery status flow
- [ ] Add unit tests for action
- [ ] Backend API endpoint ready (`/orders/track/delivery-estimation`)
- [ ] Integration testing with backend
- [ ] User acceptance testing
- [ ] Documentation updated

---

## 📞 Dependencies

**Backend:**
- API endpoint `/orders/track/delivery-estimation` must be implemented
- Backend must calculate business days correctly
- Backend must verify customer ownership

**Frontend:**
- JWT token passed to chatbot in metadata
- Customer ID available in tracker

**Chatbot:**
- No additional dependencies required
- Works with existing authentication flow
