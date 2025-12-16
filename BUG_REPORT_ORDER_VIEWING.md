# 🐛 BUG REPORT: Order Viewing Authentication Failure

## Issue ID: BE-RASA-001
**Severity:** HIGH  
**Component:** Backend → Rasa Integration  
**Status:** OPEN  
**Date:** 2025-12-16

---

## 📋 Summary
User asks "can i view my order" but chatbot responds "To track your order, please sign in to your account first." even when user is **already logged in** with valid JWT token and customer_id.

---

## 🔍 Problem Analysis

### Frontend Logs (Correct ✅)
```javascript
// Session Response
{
  "session": {
    "id": "25",
    "customer_id": 1,        // ✅ Customer is authenticated
    "visitor_id": null
  }
}

// JWT Token Present
Authorization: "Bearer eyJhbGc..." // ✅ Valid JWT token attached
```

### Backend Behavior (Incorrect ❌)
Backend correctly:
1. ✅ Authenticates user with JWT
2. ✅ Creates/retrieves chat session with `customer_id: 1`
3. ❌ **FAILS to send `customer_id` and JWT to Rasa webhook**

### Rasa Chatbot Behavior
```python
# actions.py - ActionTrackOrder
customer_id = tracker.get_slot("customer_id")  # ❌ Returns None
user_token = tracker.get_slot("user_jwt_token")  # ❌ Returns None

if not customer_id and not user_token:
    # This condition is TRUE because both are None
    dispatcher.utter_message("To track your order, please sign in...")
```

---

## 🔎 Root Cause

**Backend does NOT send user context (customer_id, JWT) to Rasa webhook.**

When calling Rasa webhook endpoint (e.g., `POST http://localhost:5005/webhooks/rest/webhook`), the backend only sends:
```json
{
  "sender": "session_25",
  "message": "can i view my order"
}
```

**Missing fields:**
- `metadata` with customer_id and JWT token
- Slot initialization data

---

## ✅ Solution

### **1. Update Backend Rasa Webhook Call**

**Current (Broken):**
```javascript
// Backend calling Rasa - WRONG
const response = await axios.post('http://localhost:5005/webhooks/rest/webhook', {
  sender: `session_${sessionId}`,
  message: userMessage
});
```

**Fixed (Correct):**
```javascript
// Backend calling Rasa - CORRECT
const rasaPayload = {
  sender: `session_${sessionId}`,
  message: userMessage,
  metadata: {
    customer_id: session.customer_id,        // Pass authenticated customer_id
    user_jwt_token: req.headers.authorization?.replace('Bearer ', ''),  // Pass JWT
    session_id: sessionId
  }
};

const response = await axios.post('http://localhost:5005/webhooks/rest/webhook', rasaPayload);
```

---

### **2. Verify Slot Initialization in Rasa**

The Rasa chatbot already has code to extract metadata:

**File:** `actions/actions.py`
```python
def get_customer_id(tracker: Tracker) -> Optional[int]:
    """Extract customer ID from tracker slots or metadata"""
    
    # Strategy 1: Check customer_id slot
    customer_id = tracker.get_slot("customer_id")
    if customer_id:
        return int(customer_id)
    
    # Strategy 2: Extract from metadata (sent by backend)
    metadata = tracker.latest_message.get("metadata", {})
    customer_id = metadata.get("customer_id")
    if customer_id:
        return int(customer_id)
    
    # Strategy 3: Verify JWT token if available
    jwt_token = metadata.get("user_jwt_token")
    if jwt_token:
        # Decode and verify JWT...
```

**This code is READY** but backend is not sending the metadata!

---

## 📝 Required Backend Changes

### **File to Update:** Backend Chat Controller/Service
Location: `kltn_be/src/controllers/chat.controller.ts` (or similar)

### **Function to Modify:** `sendMessageToRasa()` or `callRasaWebhook()`

**Add these fields to Rasa request:**
```typescript
interface RasaWebhookPayload {
  sender: string;
  message: string;
  metadata: {
    customer_id?: number;      // ← ADD THIS
    user_jwt_token?: string;   // ← ADD THIS
    session_id: string;        // ← ADD THIS
  };
}
```

**Example Implementation:**
```typescript
async sendMessageToRasa(sessionId: string, message: string, customerId?: number, jwtToken?: string) {
  const payload: RasaWebhookPayload = {
    sender: `session_${sessionId}`,
    message: message,
    metadata: {
      session_id: sessionId,
      customer_id: customerId,         // From authenticated session
      user_jwt_token: jwtToken         // From request headers
    }
  };

  const response = await axios.post(
    `${process.env.RASA_URL}/webhooks/rest/webhook`,
    payload
  );

  return response.data;
}
```

---

## 🧪 Testing Steps

### **1. After Backend Fix**
Start new chat session, send:
```
User: "can i view my order"
```

**Expected Response:**
```
Bot: "Please provide your order number or tell me which product you ordered."
```

**NOT:**
```
Bot: "To track your order, please sign in to your account first."  ❌
```

### **2. Verify Rasa Logs**
Check Rasa action server logs:
```bash
# Should see this in logs:
🔐 User authenticated - customer_id: 1, has_token: True
```

### **3. Check Frontend Console**
No errors about missing slots or authentication.

---

## 📊 Impact

**Affected Features:**
- ❌ Order tracking (`can i view my order`)
- ❌ Order cancellation
- ❌ Return/Exchange requests
- ❌ Quality issue reports
- ❌ Stock notifications
- ❌ Any feature requiring user authentication

**User Experience:**
- Users cannot track orders via chatbot
- Frustration: "I'm already signed in!"
- Reduced chatbot utility

---

## 🔧 Chatbot Changes Already Done ✅

**File:** `domain.yml`
- ✅ Added `user_jwt_token` slot

**File:** `actions/actions.py`
- ✅ Updated `ActionTrackOrder` to check `customer_id` OR `user_jwt_token`
- ✅ Updated 5 other order-related actions similarly
- ✅ Added debug logging for authentication status

**Chatbot is READY** - waiting for backend fix.

---

## 📌 Priority Justification

**HIGH Priority** because:
1. Core feature (order tracking) is broken for logged-in users
2. Multiple features affected (6+ actions)
3. Simple fix (add 2 fields to webhook call)
4. Blocking user testing and production deployment

---

## 👨‍💻 Assigned To
**Backend Team** - Chat/Rasa Integration Module

## ✅ Acceptance Criteria
- [ ] Backend sends `customer_id` in `metadata` when calling Rasa webhook
- [ ] Backend sends `user_jwt_token` in `metadata` when user is authenticated
- [ ] Logged-in users can successfully track orders via chatbot
- [ ] Rasa logs show `customer_id: <id>, has_token: True`
- [ ] No authentication errors in frontend console

---

## 📎 Additional Context

**Rasa Webhook Documentation:**
https://rasa.com/docs/rasa/connectors/your-own-website#webhooks

**Example Payload with Metadata:**
```json
{
  "sender": "user123",
  "message": "hello",
  "metadata": {
    "customer_id": 1,
    "user_jwt_token": "eyJhbGc...",
    "session_id": "25"
  }
}
```

---

## 🔗 Related Files

**Backend (needs fix):**
- `kltn_be/src/controllers/chat.controller.ts`
- `kltn_be/src/services/rasa.service.ts`

**Chatbot (already fixed):**
- `kltn_chatbot/domain.yml` ✅
- `kltn_chatbot/actions/actions.py` ✅

**Frontend (working correctly):**
- `kltn_fe/lib/stores/useChatStore.ts` ✅

---

**END OF BUG REPORT**
