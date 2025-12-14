# Bug Report: Add to Cart Flow Failure

**Date:** 12/12/2024  
**Severity:** 🔴 HIGH - BLOCKER  
**Component:** Chatbot + Backend Integration  
**Status:** 🔴 BROKEN

---

## 📋 Summary

Add to cart flow fails after user provides size. The chatbot cannot extract size entity from user input "size XL", causing the flow to break and trigger fallback response instead of completing the cart addition.

**Additional Issue:** Backend returns `customer_id: null` in session even when user is authenticated with valid JWT token.

---

## 🐛 Bug #1: Size Entity Not Extracted from User Input

### Reproduction Steps

1. User: "i want to find a shirt"
2. Bot: Shows 5 products with colors
3. User: "i want more detail about the third one"
4. Bot: Shows product details for "Áo Blazer Men Thêu Chữ Ký Túi Trong Regular Fit"
5. User: "i want to add to cart"
6. Bot: "What size would you like? (S, M, L, XL, etc.)"
7. User: "size XL" ❌
8. Bot: Generic fallback response (WRONG)

### Expected Behavior

After step 7, bot should:
1. Extract entity: `size = "XL"`
2. Set slot: `cart_size = "XL"`
3. Ask: "What color would you prefer?" (since product has colors: Xám, Đỏ, Đen)
4. Continue add to cart flow

### Actual Behavior

```
Bot responds with generic fallback:
"I'm here to help with products, styling, and fashion advice! What would you like to know? 😊"
```

### Chatbot Logs Analysis

```log
2025-12-12 10:55:04 INFO  🛒 Adding to cart: product_id=22, size=None, color=None, qty=1
                                                            ^^^^^^^^^^
                                                            SIZE IS NULL!

2025-12-12 10:55:17 INFO  🤖 ActionAskGemini: intent=nlu_fallback, confidence=0.70, message='size XL...'
                                                       ^^^^^^^^^^^^
                                                       NLU FAILED TO RECOGNIZE INTENT

2025-12-12 10:55:18 ERROR ❌ Gemini Generation Error: 'NoneType' object has no attribute 'from_call'
```

**Root Cause:**
1. User says "size XL"
2. NLU classifies as `nlu_fallback` (confidence 0.70)
3. No entity extracted: `size = None`
4. Slot `cart_size` remains None
5. ActionAddToCart runs with `size=None`, asks for size again (but message never sent)
6. Flow breaks → triggers fallback action
7. Gemini also fails with AttributeError
8. Bot sends generic fallback response

---

## 🐛 Bug #2: Backend Returns customer_id: null Despite Valid JWT

### Frontend Console Logs

```javascript
[ChatStore] Response.data: {
  "session": {
    "id": "21",
    "visitor_id": "ef35fb12-78d5-49af-b8c3-4e218d36bf38",
    "customer_id": null,  // ❌ NULL despite user being logged in
    "created_at": "2025-12-07T10:13:19.422Z",
    "updated_at": "2025-12-12T03:26:40.555Z"
  },
  "is_new": false
}

// JWT Token IS present:
"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5ibWluaDI0QGdtYWlsLmNvbSIsInN1YiI6MjEsImlhdCI6MTc2NTUwNjQ0MiwiZXhwIjoxNzY1NTA3MzQyfQ.fxyX3tIeXRxEdgihaKA1T7O3iq4ZnLQr2Rs3tryilfk"
```

**Decoded JWT:**
```json
{
  "email": "nbminh24@gmail.com",
  "sub": 21,  // customer_id should be 21!
  "iat": 1765506442,
  "exp": 1765507342
}
```

### Expected Behavior

Backend should:
1. Extract JWT token from `Authorization` header
2. Decode JWT and get `customer_id = 21` from `sub` field
3. Update or return session with `customer_id: 21`
4. Pass `customer_id` in metadata when forwarding message to Rasa chatbot

### Actual Behavior

- Backend returns `customer_id: null` in session
- Chatbot receives no `customer_id` in metadata
- When chatbot tries to add to cart, it fails because `customer_id = None`

### Impact

Even if Bug #1 is fixed (size entity extraction), add to cart will still fail because:
```python
# In ActionAddToCart
customer_id = get_customer_id_from_tracker(tracker)
# → Returns None because metadata.customer_id is not set

if not customer_id:
    dispatcher.utter_message(
        text="🔐 Please sign in to view your cart!"
    )
    return []  # ❌ Flow stops here
```

---

## 🔧 Root Cause Analysis

### Issue 1: NLU Entity Extraction Failure

**File:** `data/nlu.yml`

NLU training data has examples like:
```yaml
- intent: add_to_cart
  examples: |
    - Add size [M](size) to cart
    - I want size [L](size)
    - Add [XL](size) please
    - Cho tôi size [M](size)
```

**Problem:**
User input "size XL" doesn't match training patterns because:
1. NLU expects size entity inline: "Add [XL](size)" or "I want size [L](size)"
2. User said just "size XL" which is too short and ambiguous
3. NLU confidence 0.70 triggered fallback threshold

**Why it worked before:**
- Previous messages like "i want to add to cart" matched `add_to_cart` intent with high confidence
- But follow-up message "size XL" is out of context and NLU doesn't recognize it

---

### Issue 2: Backend customer_id Injection Not Implemented

**Expected Flow (from CUSTOMER_ID_INJECTION_GUIDE.md):**

```
Frontend → Backend → Chatbot
         ↓
Backend extracts JWT token
Backend decodes JWT → customer_id = token.sub
Backend injects customer_id into message metadata
         ↓
    {
      message: "size XL",
      metadata: {
        customer_id: 21,
        user_jwt_token: "eyJ..."
      }
    }
         ↓
Chatbot receives customer_id in metadata
```

**Current Implementation:**
```
Frontend → Backend → Chatbot
         ↓
Backend forwards message WITHOUT customer_id
         ↓
    {
      message: "size XL",
      metadata: {}  // ❌ Empty
    }
         ↓
Chatbot receives NO customer_id
```

**Backend Missing:**
- Middleware to extract JWT from request
- Logic to decode JWT and get customer_id
- Injection of customer_id into message metadata before forwarding to Rasa

---

## 🛠️ Solutions

### Solution 1A: Fix NLU Training Data (CHATBOT FIX - RECOMMENDED)

**File:** `data/nlu.yml`

Add more training examples for standalone size responses:

```yaml
- intent: inform_size
  examples: |
    - XL
    - size XL
    - [XL](size)
    - [L](size)
    - [M](size)
    - size [M](size)
    - [S](size) please
    - I want [L](size)
    - [XXL](size)
    - size [L](size) please
    - Cho size [M](size)
    - Size [XL](size)
```

**File:** `data/rules.yml`

Add rule to handle size inform:

```yaml
- rule: Fill cart_size slot when user informs size
  steps:
  - intent: inform_size
  - action: action_add_to_cart
```

**File:** `domain.yml`

Add `inform_size` intent:

```yaml
intents:
  - inform_size
```

Update slot mapping for `cart_size`:

```yaml
slots:
  cart_size:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: size
      intent: inform_size
    - type: custom
```

---

### Solution 1B: Improve ActionAddToCart Slot Extraction (ALTERNATIVE)

**File:** `actions/actions.py`

Update `ActionAddToCart` to extract size from entity even if intent is not recognized:

```python
# Current code:
size = tracker.get_slot("cart_size")

# Updated code:
size = tracker.get_slot("cart_size")

# Fallback: Try to extract size entity from latest message
if not size:
    size_entity = next(tracker.get_latest_entity_values("size"), None)
    if size_entity:
        logger.info(f"📌 Extracted size from entity: {size_entity}")
        size = size_entity
```

---

### Solution 2: Backend Implement customer_id Injection (BACKEND FIX - REQUIRED)

**File:** `src/modules/chat/chat.service.ts` (or middleware)

Add logic to extract customer_id from JWT and inject into Rasa message:

```typescript
async sendMessageToRasa(sessionId: string, message: string, userId?: number) {
  // Get JWT token from request context
  const jwtToken = this.request.headers.authorization?.replace('Bearer ', '');
  
  let customerId = userId;
  
  // Decode JWT to get customer_id if not provided
  if (!customerId && jwtToken) {
    try {
      const decoded = this.jwtService.verify(jwtToken);
      customerId = decoded.sub; // customer_id is in 'sub' field
    } catch (error) {
      this.logger.warn('Failed to decode JWT token', error);
    }
  }
  
  // Build Rasa message with metadata
  const rasaMessage = {
    sender: `session_${sessionId}`,
    message: message,
    metadata: {
      customer_id: customerId,        // ✅ Inject customer_id
      user_jwt_token: jwtToken,       // ✅ Include token
      session_id: sessionId
    }
  };
  
  // Send to Rasa
  const response = await this.rasaClient.post('/webhooks/rest/webhook', rasaMessage);
  return response.data;
}
```

**Also Update:** `POST /chat/session` endpoint

Ensure session is created/updated with customer_id from JWT:

```typescript
async getOrCreateSession(visitorId: string, userId?: number) {
  // Decode JWT if userId not provided
  const jwtToken = this.request.headers.authorization?.replace('Bearer ', '');
  
  if (!userId && jwtToken) {
    try {
      const decoded = this.jwtService.verify(jwtToken);
      userId = decoded.sub;
    } catch (error) {
      this.logger.warn('Failed to decode JWT', error);
    }
  }
  
  // Find or create session
  let session = await this.sessionRepo.findOne({ 
    where: { visitor_id: visitorId } 
  });
  
  if (session) {
    // Update customer_id if user is now logged in
    if (userId && session.customer_id !== userId) {
      session.customer_id = userId;
      await this.sessionRepo.save(session);
    }
  } else {
    session = await this.sessionRepo.save({
      visitor_id: visitorId,
      customer_id: userId  // ✅ Set customer_id from JWT
    });
  }
  
  return session;
}
```

---

## 🧪 Testing Checklist

### Test Case 1: Size Entity Extraction

**Input:**
```
User: "i want to add to cart"
Bot: "What size would you like?"
User: "size XL"
```

**Expected:**
- NLU extracts: `intent=inform_size, entity.size="XL"`
- Slot set: `cart_size = "XL"`
- Bot asks: "What color would you prefer?"

**Test Command:**
```bash
rasa train
rasa shell nlu
> size XL
```

Expected output should show:
```json
{
  "intent": {
    "name": "inform_size",
    "confidence": 0.95
  },
  "entities": [
    {
      "entity": "size",
      "value": "XL"
    }
  ]
}
```

---

### Test Case 2: customer_id Injection

**Test with cURL:**

```bash
# 1. Get JWT token (login)
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "nbminh24@gmail.com", "password": "xxx"}'

# Response: { "access_token": "eyJ..." }

# 2. Create session with JWT
curl -X POST http://localhost:3001/chat/session \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"visitor_id": "test-visitor-123"}'

# Expected response:
{
  "session": {
    "id": "21",
    "visitor_id": "test-visitor-123",
    "customer_id": 21  // ✅ Should NOT be null!
  }
}

# 3. Send message to chatbot
curl -X POST http://localhost:3001/chat/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{
    "session_id": "21",
    "message": "xem giỏ hàng"
  }'

# Backend should forward to Rasa with metadata:
{
  "sender": "session_21",
  "message": "xem giỏ hàng",
  "metadata": {
    "customer_id": 21,  // ✅ Injected by backend
    "user_jwt_token": "eyJ..."
  }
}
```

**Check Chatbot Logs:**
```
✅ Got customer_id from metadata: 21
📥 Cart API response: success=True, items count: 2
```

---

## 📊 Priority & Impact

### Bug #1: Size Entity Extraction
- **Severity:** HIGH
- **Priority:** P1
- **Impact:** Blocks add to cart flow for 100% of users
- **Fix Time:** 30 minutes (add NLU training data + retrain)
- **Owner:** Chatbot Team

### Bug #2: customer_id Null
- **Severity:** CRITICAL
- **Priority:** P0
- **Impact:** Blocks ALL authenticated features (cart, orders, profile)
- **Fix Time:** 1-2 hours (backend middleware implementation)
- **Owner:** Backend Team

---

## 🚀 Action Items

### For Chatbot Team:
- [x] Analyze logs ✅
- [ ] Add `inform_size` intent to NLU training data
- [ ] Add rule for size slot filling
- [ ] Retrain model: `rasa train`
- [ ] Test entity extraction: `rasa shell nlu`
- [ ] Deploy updated model

### For Backend Team:
- [ ] **URGENT:** Implement customer_id extraction from JWT
- [ ] Update `POST /chat/session` to set customer_id from JWT
- [ ] Update `POST /chat/send` to inject customer_id in metadata before forwarding to Rasa
- [ ] Test with cURL/Postman
- [ ] Verify chatbot receives customer_id in metadata
- [ ] Deploy to staging

### For Testing:
- [ ] End-to-end test: Login → Add to cart → View cart
- [ ] Test with multiple users
- [ ] Verify customer_id isolation (user A can't see user B's cart)

---

## 📝 Related Documents

- `CHATBOT_BACKEND_INTEGRATION_COMPLETE.md` - Integration implementation
- `CUSTOMER_ID_INJECTION_GUIDE.md` - Options for customer_id injection
- `BACKEND_API_IMPLEMENTATION_SUMMARY.md` - Backend APIs

---

## 🔗 References

**Chatbot Logs:**
```
2025-12-12 10:55:04 INFO  🛒 Adding to cart: product_id=22, size=None, color=None, qty=1
2025-12-12 10:55:17 INFO  🤖 ActionAskGemini: intent=nlu_fallback, confidence=0.70
2025-12-12 10:55:18 ERROR ❌ Gemini Generation Error
```

**Frontend Logs:**
```javascript
customer_id: null  // ❌ Should be 21
Authorization: "Bearer eyJhbGc...sub:21..."  // JWT has customer_id!
```

**JWT Payload:**
```json
{
  "email": "nbminh24@gmail.com",
  "sub": 21,  // This is customer_id
  "iat": 1765506442,
  "exp": 1765507342
}
```

---

**Status:** 🔴 BLOCKING PRODUCTION DEPLOYMENT  
**ETA:** Fix available within 24 hours after both teams complete their parts
