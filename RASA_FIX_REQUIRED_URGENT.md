# 🚨 [URGENT] Rasa Intent Tracking - Implementation Issue

**To:** Team AI (Rasa)  
**From:** Backend Team  
**Date:** 2026-01-11  
**Priority:** CRITICAL - BLOCKING ANALYTICS DASHBOARD

---

## ❌ Current Issue

Backend logs show Rasa is **NOT sending intent in response**:

```
[Chat] 🎯 Intent extraction: {
  hasMetadata: false,        ← NO metadata in response
  metadataIntent: undefined,
  customIntent: undefined,
  extractedIntent: null      ← INTENT IS NULL!
}
```

**Current Rasa response structure:**
```json
[
  {
    "recipient_id": "session_47",
    "text": "Mình đã tìm thấy 5 sản phẩm...",
    // ❌ NO metadata field at all
  },
  {
    "recipient_id": "session_47",
    "custom": {
      "type": "product_list",
      "products": [...]
      // ❌ NO intent field in custom
    }
  }
]
```

---

## ✅ Required Response Structure

Rasa **MUST** add `metadata` field to **EVERY** response:

```json
[
  {
    "recipient_id": "session_47",
    "text": "Mình đã tìm thấy 5 sản phẩm...",
    "metadata": {
      "intent": "product_inquiry"  // ← ADD THIS!
    }
  },
  {
    "recipient_id": "session_47",
    "text": "...",
    "metadata": {
      "intent": "product_inquiry"  // ← ADD THIS!
    },
    "custom": {
      "type": "product_list",
      "products": [...]
    }
  }
]
```

---

## 🔧 Implementation Fix

### ❌ Current Code (WRONG)
```python
def run(self, dispatcher, tracker, domain):
    intent_name = get_intent_from_tracker(tracker)
    
    # This is NOT ENOUGH - metadata is not sent to webhook
    dispatcher.utter_message(
        text="Found products...",
        custom={"type": "product_list", "products": products}
    )
```

### ✅ Fixed Code (CORRECT)
```python
def run(self, dispatcher, tracker, domain):
    intent_name = get_intent_from_tracker(tracker)
    
    # MUST add metadata parameter with intent
    dispatcher.utter_message(
        text="Found products...",
        metadata={"intent": intent_name},  # ← ADD THIS LINE!
        custom={"type": "product_list", "products": products}
    )
```

---

## 📋 What Team AI Needs to Do

### 1. Check `dispatcher.utter_message()` Calls

Search for ALL `dispatcher.utter_message()` in actions and ensure they include `metadata`:

```bash
cd /path/to/rasa/project
grep -r "dispatcher.utter_message" actions/
```

### 2. Add `metadata={"intent": ...}` to ALL Calls

**Example from ActionSearchProducts:**

```python
# actions/actions.py - ActionSearchProducts
def run(self, dispatcher, tracker, domain):
    intent_name = get_intent_from_tracker(tracker)  # Get intent
    
    # Search products...
    products = search_products(query)
    
    # ✅ CORRECT: Add metadata with intent
    dispatcher.utter_message(
        text=f"Found {len(products)} products...",
        metadata={"intent": intent_name},  # ← MUST HAVE THIS!
        custom={"type": "product_list", "products": products}
    )
```

### 3. Verify ALL Custom Actions

Check these actions have `metadata` parameter:
- ✅ ActionSearchProducts
- ✅ ActionTrackOrder
- ✅ ActionGetStylingAdvice
- ✅ ActionCheckAvailability
- ✅ ActionAddToCart
- ✅ ActionAskGemini
- ✅ ... ALL 30+ custom actions

---

## 🧪 Testing

### Step 1: Restart Rasa
```bash
rasa run actions  # Restart actions server
```

### Step 2: Test Request
```bash
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user",
    "message": "tôi muốn áo meow"
  }'
```

### Step 3: Verify Response Has Metadata
```json
[
  {
    "recipient_id": "test_user",
    "text": "...",
    "metadata": {"intent": "product_inquiry"}  // ← MUST BE HERE!
  }
]
```

---

## 🔍 Debug Helper

Add logging in actions to verify intent is extracted:

```python
def run(self, dispatcher, tracker, domain):
    intent_name = get_intent_from_tracker(tracker)
    
    # Debug log
    print(f"🎯 Extracted intent: {intent_name}")
    
    # Send with metadata
    dispatcher.utter_message(
        text="...",
        metadata={"intent": intent_name}
    )
    
    # Verify it's in the response
    print(f"✅ Sent metadata: {{'intent': '{intent_name}'}}")
```

---

## ⏰ Timeline

**This is blocking the admin dashboard analytics.**

Expected completion: **TODAY** (urgent fix)

---

## 📞 Contact

Nếu có vấn đề khi implement, liên hệ Backend Team ngay.

**Verification:** After fix, backend logs should show:
```
[Chat] 🎯 Intent extraction: {
  hasMetadata: true,           ← Should be true
  metadataIntent: "product_inquiry",  ← Should have value
  extractedIntent: "product_inquiry"  ← Should NOT be null
}
```
