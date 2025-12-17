# Order Cancellation Feature - Chatbot Implementation

**Date:** 2025-12-16  
**Priority:** 🔴 CRITICAL  
**Status:** ✅ IMPLEMENTATION COMPLETE

---

## 📋 Feature Overview

Chatbot now supports intelligent order cancellation with:
- ✅ **Status-based validation** - Only allows cancellation when `fulfillment_status = 'pending'`
- ✅ **Reason tracking** - Automatically extracts cancellation reason from user message
- ✅ **Smart suggestions** - Provides alternative solutions when cancellation is not possible
- ✅ **Detailed error handling** - Different responses for each order status

---

## 🎯 Business Rules

### Cancellation Policy Matrix

| Order Status | Can Cancel? | Chatbot Response |
|--------------|-------------|------------------|
| `pending` | ✅ YES | "Order canceled successfully" |
| `confirmed` | ❌ NO | "Refuse delivery or request return after receiving" |
| `shipping` | ❌ NO | "Refuse delivery or initiate return after delivery" |
| `delivered` | ❌ NO | "Request return/refund according to policy" |
| `cancelled` | ❌ NO | "Order already canceled" |

### Cancellation Reasons (Enum)

```typescript
enum CancelReason {
  CHANGED_MIND = 'changed_mind',
  ORDERED_WRONG_ITEM = 'ordered_wrong_item',
  WRONG_SIZE_COLOR = 'wrong_size_color',
  FOUND_BETTER_PRICE = 'found_better_price',
  DELIVERY_TOO_SLOW = 'delivery_too_slow',
  PAYMENT_ISSUE = 'payment_issue',
  DUPLICATE_ORDER = 'duplicate_order',
  OTHER = 'other'
}
```

---

## 💬 Conversation Examples

### ✅ Case 1: Successful Cancellation (Pending Order)

**User:**
```
I want to cancel order 0000000032 because I changed my mind
```

**Chatbot:**
```
✅ Your order 0000000032 has been successfully canceled.

If you need help placing a new order, feel free to let me know! 😊
```

**Backend Logs:**
```
🚫 Cancel request: order=0000000032, customer=1, reason=changed_mind
📦 Order status: pending
✅ Detected reason: changed my mind -> changed_mind
```

---

### ❌ Case 2: Cannot Cancel (Confirmed Order)

**User:**
```
Cancel order 0000000033
```

**Chatbot:**
```
Your order has been confirmed and is waiting for delivery. 📦

At this stage, the order can no longer be canceled.

💡 You can refuse the package upon delivery or request a return after receiving it, according to our return policy.
```

---

### ❌ Case 3: Cannot Cancel (Shipping)

**User:**
```
I need to cancel order 0000000034
```

**Chatbot:**
```
Your order is currently being shipped. 🚚
📍 Tracking: VN123456789 (GHTK)

At this stage, cancellation is no longer possible.

💡 A common option is to refuse the delivery when the courier arrives, or initiate a return after the package is delivered.
```

---

### ❌ Case 4: Cannot Cancel (Delivered)

**User:**
```
Can I cancel order 0000000035?
```

**Chatbot:**
```
This order has already been delivered. ✅

Cancellation is no longer possible, but you may request a return or refund according to our return policy if the product meets the conditions.
```

---

### ⚠️ Case 5: Already Canceled

**User:**
```
Cancel my order 0000000032
```

**Chatbot:**
```
This order has already been canceled. ✅

Is there anything else I can help you with?
```

---

## 🔧 Technical Implementation

### 1. API Client Update

**File:** `actions/api_client.py`

```python
def cancel_order(self, order_id: int, customer_id: int, cancel_reason: str = "other") -> Dict[str, Any]:
    """
    Cancel order using internal chatbot API
    Endpoint: POST /api/chatbot/orders/:id/cancel
    """
    data = {
        "customer_id": customer_id,
        "cancel_reason": cancel_reason
    }
    return self._make_request("POST", f"/api/chatbot/orders/{order_id}/cancel", data=data)
```

### 2. Action Handler

**File:** `actions/actions.py`

**Class:** `ActionCancelOrder`

**Key Features:**
- Validates customer authentication
- Extracts order number from entity or slot
- Auto-detects cancellation reason from user message
- Calls backend API with reason
- Handles 5 different error codes with contextual responses

**Reason Detection Logic:**
```python
CANCEL_REASONS = {
    "changed my mind": "changed_mind",
    "ordered wrong item": "ordered_wrong_item",
    "wrong size": "wrong_size_color",
    "better price": "found_better_price",
    "too slow": "delivery_too_slow",
    "payment issue": "payment_issue",
    "duplicate": "duplicate_order",
}
```

### 3. NLU Training

**File:** `data/nlu.yml`

**Intent:** `cancel_order`

**Examples:** 38 training examples covering:
- Basic cancellation requests
- Cancellation with order number
- Cancellation with reason phrases
- Various reason combinations

### 4. Domain Configuration

**File:** `domain.yml`

**Action registered:** `action_cancel_order`

---

## 🧪 Testing Guide

### Prerequisites
1. Backend server running with cancellation API
2. Database has orders with different statuses
3. Chatbot action server running

### Test Scenarios

#### Test 1: Cancel Pending Order
```bash
# Setup: Create pending order
INSERT INTO orders (id, order_number, customer_id, fulfillment_status)
VALUES (32, '0000000032', 1, 'pending');

# Test in chatbot
User: "I want to cancel order 0000000032 because I changed my mind"

# Expected: Success message
```

#### Test 2: Try Cancel Confirmed Order
```bash
# Setup: Update order to confirmed
UPDATE orders SET fulfillment_status = 'confirmed' WHERE id = 33;

# Test in chatbot
User: "Cancel order 0000000033"

# Expected: Cannot cancel + return suggestion
```

#### Test 3: Try Cancel Shipping Order
```bash
# Setup: Update to shipping with tracking
UPDATE orders 
SET fulfillment_status = 'shipping',
    tracking_number = 'VN123456789',
    carrier_name = 'GHTK'
WHERE id = 34;

# Test in chatbot
User: "Cancel my order 0000000034"

# Expected: Cannot cancel + tracking info + refuse delivery option
```

#### Test 4: Reason Detection
```bash
# Test various reason phrases
User: "Cancel order 0000000035 wrong size"
Expected reason: wrong_size_color

User: "Cancel 0000000036 I found it cheaper"
Expected reason: found_better_price

User: "Cancel order 0000000037 delivery too slow"
Expected reason: delivery_too_slow
```

#### Test 5: Without Order Number
```bash
User: "I want to cancel my order"

# Expected: "Which order would you like to cancel?"
```

#### Test 6: Not Authenticated
```bash
# Test without customer_id in metadata
User: "Cancel order 0000000038"

# Expected: "To cancel an order, please sign in first! 🔐"
```

---

## 📊 Analytics Queries

### Track Cancellation Reasons
```sql
SELECT 
  cancel_reason,
  COUNT(*) as total,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM orders
WHERE fulfillment_status = 'cancelled'
  AND cancelled_at >= NOW() - INTERVAL '30 days'
GROUP BY cancel_reason
ORDER BY total DESC;
```

### Cancellation Rate by Status
```sql
SELECT 
  status_before_cancel,
  COUNT(*) as cancel_attempts
FROM order_cancellation_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY status_before_cancel;
```

---

## 🎓 Academic Value (For KLTN Report)

### Design Principles
1. **Rule-based validation** - Backend enforces business rules, chatbot reflects them
2. **Transparency** - Always explain why cancellation is not possible
3. **User guidance** - Provide alternative solutions (refuse delivery, return)
4. **Data collection** - Track reasons for business improvement

### Technical Contribution
- **Structured reason tracking** enables data-driven UX improvements
- **Status-based branching** ensures correct business logic
- **Graceful degradation** when cancellation not possible

### Report-ready Description
```
The chatbot supports order cancellation requests under strict business rules.
Cancellation is only allowed when the order is in the "pending" state, verified 
by backend services. For orders that have progressed beyond this stage, the 
chatbot explains the current order status and suggests alternative options such 
as refusing delivery or initiating a return, reflecting common e-commerce practices.

The system collects structured cancellation reasons (changed_mind, wrong_size_color, 
delivery_too_slow, etc.) enabling analysis of customer behavior patterns. This 
approach ensures correctness, transparency, and user trust while providing 
valuable business intelligence.
```

---

## 🚀 Deployment Steps

### 1. Restart Action Server
```bash
cd c:\Users\USER\Downloads\kltn_chatbot

# Stop current server (Ctrl+C)
# Then restart:
rasa run actions
```

### 2. Verify Action Registered
Check logs for:
```
[ActionExecutor] Registered function for 'action_cancel_order'
```

### 3. Test End-to-End
```bash
# Test in Rasa shell (optional)
rasa shell

# Or test via frontend integration
```

### 4. Monitor Logs
Watch for:
```
🚫 Cancel request: order=..., customer=..., reason=...
📦 Order status: ...
✅ Detected reason: ... -> ...
```

---

## 📝 API Contract

### Request Format (Internal Chatbot API)
```http
POST /api/chatbot/orders/{order_id}/cancel
Headers:
  X-Internal-Api-Key: <API_KEY>
Body:
{
  "customer_id": 1,
  "cancel_reason": "changed_mind"
}
```

### Success Response
```json
{
  "success": true,
  "message": "Order cancelled successfully",
  "order": {
    "order_id": 32,
    "order_number": "0000000032",
    "fulfillment_status": "cancelled",
    "cancelled_at": "2025-12-16T13:00:00.000Z",
    "cancel_reason": "changed_mind"
  }
}
```

### Error Response (Cannot Cancel)
```json
{
  "success": false,
  "error": "CANNOT_CANCEL_CONFIRMED",
  "message": "This order has been confirmed and is waiting for delivery",
  "current_status": "confirmed",
  "suggestion": "You can refuse the package upon delivery or request a return after receiving it"
}
```

---

## ✅ Feature Checklist

- [x] API client updated with `cancel_reason` parameter
- [x] `ActionCancelOrder` implemented with status-based logic
- [x] Reason detection from natural language
- [x] NLU training examples enhanced (38 examples)
- [x] Domain.yml updated
- [x] Error handling for 5 status scenarios
- [x] Alternative suggestions for non-cancelable orders
- [x] Customer authentication check
- [x] Logging for analytics
- [x] Documentation complete

---

## 🔗 Related Files

- **Action Handler:** `actions/actions.py` - `ActionCancelOrder` class
- **API Client:** `actions/api_client.py` - `cancel_order()` method
- **NLU Training:** `data/nlu.yml` - `cancel_order` intent
- **Domain Config:** `domain.yml` - Action registration
- **Backend API:** `/api/chatbot/orders/:id/cancel` endpoint
- **Backend DTO:** `cancel-order-internal.dto.ts`

---

## 📞 Support

**For Issues:**
- Check action server logs for errors
- Verify customer is authenticated (`customer_id` in metadata)
- Verify order exists and belongs to customer
- Check order status in database

**Common Issues:**
- "Order not found" → Check order_number format
- "Sign in first" → Customer not authenticated
- "Generic error" → Check backend API logs

---

**Implementation Date:** 2025-12-16  
**Implementation Status:** ✅ COMPLETE  
**Ready for Production:** YES
