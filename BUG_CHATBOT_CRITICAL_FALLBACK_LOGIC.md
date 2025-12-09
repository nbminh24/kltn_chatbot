# 🐛 CRITICAL BUG - Rasa Fallback Logic Error

**Date:** December 9, 2025, 09:27 AM  
**Reporter:** Backend Team  
**Severity:** 🔴 CRITICAL (Blocking core product search feature)  
**Status:** ACTIVE  
**Assigned to:** Chatbot/Rasa Team

---

## 📋 SUMMARY

Rasa chatbot đang trigger fallback khi KHÔNG CẦN THIẾT. Intent detection đã ĐÚNG với confidence rất cao (98.52%) nhưng vẫn gọi Gemini fallback thay vì thực thi action search product.

---

## 🔴 ISSUE

### **Test Case:**

**User input:**
```
"i want to find a polo"
```

**Expected behavior:**
1. ✅ Detect intent: `search_product`
2. ✅ Extract entity: "polo"
3. ✅ Call backend API: `GET /products?search=polo`
4. ✅ Return product list to user

**Actual behavior:**
1. ✅ Intent detected correctly: `search_product` (confidence: **98.52%**)
2. ❌ **FALLBACK TRIGGERED** (không nên xảy ra!)
3. ❌ Call Gemini AI instead of product search API
4. ❌ Gemini client crashed: `'NoneType' object has no attribute 'from_call'`
5. ❌ Timeout after 10 seconds
6. ❌ User receives error message

---

## 📊 EVIDENCE

### **Rasa Logs:**
```
2025-12-09 09:23:12 INFO  actions.actions  
- Fallback triggered for message: i want to find a polo 
  (intent: search_product, confidence: 0.9852145314216614)

2025-12-09 09:23:12 INFO  actions.api_client  
- Logging fallback for message: i want to find a polo

2025-12-09 09:23:12 ERROR actions.api_client  
- HTTP Error: 404 - {"message":"Cannot POST /api/chatbot/log-fallback","error":"Not Found","statusCode":404}

2025-12-09 09:23:12 INFO  actions.gemini_client  
- Handling open-ended query: i want to find a polo...

2025-12-09 09:23:12 ERROR actions.gemini_client  
- Error handling open-ended query: 'NoneType' object has no attribute 'from_call'

2025-12-09 09:23:12 WARNING actions.actions  
- RAG failed or disabled for: i want to find a polo
```

### **Backend Logs:**
```
[Chat] Calling Rasa webhook: http://localhost:5005/webhooks/rest/webhook
[Chat] Sender: ef35fb12-78d5-49af-b8c3-4e218d36bf38, Message: "i want to find a polo"
[Chat] Rasa webhook failed: timeout of 10000ms exceeded
```

---

## 💥 ROOT CAUSE ANALYSIS

### **Identified Issues:**

#### 1. 🔴 **Fallback Logic Error** (CRITICAL)
**Problem:** Fallback được trigger khi confidence = 98.52%

**Expected:** Fallback chỉ nên trigger khi:
- Confidence < threshold (thường < 0.7 hoặc 0.8)
- Intent = `nlu_fallback`
- Không extract được entities quan trọng

**Actual:** Fallback trigger ngay cả khi intent ĐÚNG và confidence CAO

**Code location (suspected):**
```python
# File: actions/actions.py (hoặc tương tự)

# ❌ WRONG LOGIC:
if intent == "search_product":
    # Có thể đang check entities sai
    # hoặc luôn return fallback
    return ActionFallback()

# ✅ SHOULD BE:
if intent == "search_product":
    product_name = tracker.get_slot("product_name")
    if product_name:
        # Call backend search API
        return search_products_action(product_name)
    else:
        # Ask for clarification
        return ask_product_name()
```

#### 2. 🔴 **Gemini Client Configuration Error** (CRITICAL)
**Error:** `'NoneType' object has no attribute 'from_call'`

**Problem:** Gemini client không được initialize đúng cách

**Code location (suspected):**
```python
# File: actions/gemini_client.py

# ❌ WRONG:
gemini_model = None  # Không init
response = gemini_model.from_call(...)  # → NoneType error

# ✅ SHOULD BE:
import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')
response = gemini_model.generate_content(...)
```

#### 3. ⚠️ **Missing Backend Endpoint** (MINOR)
**Error:** `Cannot POST /api/chatbot/log-fallback`

Endpoint này không critical cho chức năng chính, chỉ để logging.

#### 4. ⚠️ **Timeout Due to Retry Loop** (CONSEQUENCE)
Fallback retry 3 lần, mỗi lần crash → total >10s → backend timeout

---

## 🛠️ HOW TO FIX

### **Priority 1: Fix Fallback Logic** (URGENT)

**File:** `actions/actions.py` (hoặc file chứa action logic)

**Check điều kiện trigger fallback:**

```python
# ❌ REMOVE or FIX:
def should_trigger_fallback(intent, confidence):
    # Don't always trigger fallback for valid intents!
    if intent == "search_product":
        return False  # Should NOT fallback for high confidence
    
    # Only fallback if confidence is LOW
    return confidence < 0.7

# ✅ CORRECT ACTION:
class ActionSearchProduct(Action):
    def name(self):
        return "action_search_product"
    
    def run(self, dispatcher, tracker, domain):
        # Get entities
        product_name = tracker.get_slot("product_name") or \
                       next(tracker.get_latest_entity_values("product_name"), None)
        
        if not product_name:
            # Ask for clarification if no entity
            dispatcher.utter_message(
                text="Bạn muốn tìm sản phẩm gì? Ví dụ: áo polo, quần jean, giày thể thao..."
            )
            return []
        
        # Call backend search API
        try:
            results = self.search_products_api(product_name)
            
            if results:
                # Return products
                dispatcher.utter_message(
                    text=f"Tìm thấy {len(results)} sản phẩm cho '{product_name}'",
                    custom={"type": "product_list", "products": results}
                )
            else:
                dispatcher.utter_message(
                    text=f"Xin lỗi, không tìm thấy sản phẩm nào với từ khóa '{product_name}'"
                )
        except Exception as e:
            logger.error(f"Search API failed: {e}")
            dispatcher.utter_message(
                text="Xin lỗi, có lỗi khi tìm kiếm. Vui lòng thử lại."
            )
        
        return []
```

---

### **Priority 2: Fix Gemini Client** (HIGH)

**File:** `actions/gemini_client.py`

**Correct initialization:**

```python
import os
import google.generativeai as genai
from typing import Optional

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        # ✅ CORRECT INIT
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def ask(self, question: str) -> Optional[str]:
        try:
            # ✅ CORRECT METHOD
            response = self.model.generate_content(question)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None

# Initialize once
gemini_client = GeminiClient()
```

---

### **Priority 3: Review Stories & Rules**

**File:** `data/stories.yml` and `data/rules.yml`

**Check if stories are routing to fallback incorrectly:**

```yaml
# ❌ WRONG STORY:
stories:
- story: search product fallback
  steps:
  - intent: search_product
  - action: action_fallback  # ← THIS IS WRONG!

# ✅ CORRECT STORY:
stories:
- story: search product
  steps:
  - intent: search_product
    entities:
    - product_name: "polo"
  - action: action_search_product  # ← Call search action
  - slot_was_set:
    - product_name: "polo"
```

---

### **Priority 4: Add Logging for Debugging**

**Add detailed logs to understand why fallback triggers:**

```python
def run(self, dispatcher, tracker, domain):
    intent = tracker.latest_message.get('intent', {})
    intent_name = intent.get('name')
    confidence = intent.get('confidence', 0)
    entities = tracker.latest_message.get('entities', [])
    
    logger.info(f"[DEBUG] Intent: {intent_name}, Confidence: {confidence}")
    logger.info(f"[DEBUG] Entities: {entities}")
    logger.info(f"[DEBUG] Slots: {tracker.current_slot_values()}")
    
    # Continue with action logic...
```

---

## 🧪 TESTING

### **Test Case 1: Product Search**
```
Input: "i want to find a polo"
Expected:
- Intent: search_product (confidence > 0.9) ✅
- Entity: product_name = "polo" ✅
- Action: action_search_product (NOT fallback) ✅
- API Call: GET /products?search=polo ✅
- Response: Product list ✅
```

### **Test Case 2: Vietnamese Product Search**
```
Input: "tìm áo thun đen"
Expected:
- Intent: search_product ✅
- Entity: product_name = "áo thun đen" ✅
- Action: action_search_product ✅
- Response: Product list ✅
```

### **Test Case 3: Vague Query (Actual Fallback Case)**
```
Input: "what is the meaning of life?"
Expected:
- Intent: nlu_fallback OR confidence < 0.7 ✅
- Action: action_fallback ✅
- Gemini: Handle philosophical question ✅
```

---

## 📞 ACTION ITEMS

### **Chatbot Team (URGENT):**
- [ ] Review `actions/actions.py` - tìm nơi trigger fallback cho `search_product`
- [ ] Fix fallback condition - chỉ trigger khi confidence thấp
- [ ] Implement `action_search_product` đúng cách
- [ ] Fix Gemini client initialization
- [ ] Review `stories.yml` và `rules.yml` 
- [ ] Add detailed logging
- [ ] Test với các queries: "polo", "shirt", "áo thun"

### **Backend Team:**
- [x] Verified backend API `/products?search=...` works ✅
- [ ] Add optional endpoint `/api/chatbot/log-fallback` (low priority)

---

## 💡 EXPECTED FLOW

```
User: "i want to find a polo"
  ↓
Rasa NLU: 
  - Intent: search_product (98.5%)
  - Entity: product_name = "polo"
  ↓
Rasa Dialog:
  - Match story/rule for search_product
  - Trigger: action_search_product (NOT fallback!)
  ↓
Custom Action:
  - Extract slot: product_name = "polo"
  - Call: GET http://localhost:3001/products?search=polo
  - Get: [list of polo products]
  ↓
Response:
  {
    "text": "Tìm thấy 5 sản phẩm polo",
    "custom": {
      "type": "product_list",
      "products": [...]
    }
  }
  ↓
User sees: Product cards in chat
```

---

## 🎯 IMPACT

**Current State:**
- ❌ Product search COMPLETELY BROKEN
- ❌ Users cannot find any products via chat
- ❌ Core chatbot feature NON-FUNCTIONAL
- ❌ 10s timeout on every search query
- ❌ Bad user experience

**After Fix:**
- ✅ Product search works instantly
- ✅ High confidence intents execute correctly
- ✅ Fallback only for truly ambiguous queries
- ✅ Fast response (<2s)
- ✅ Core feature functional

---

**Priority:** 🔴 **CRITICAL - HIGHEST PRIORITY**  
**Timeline:** Fix ASAP (within today)  
**Blocking:** Entire product search via chatbot feature

---

**Bug Report Created:** 2025-12-09 09:27  
**Reporter:** Backend Team  
**Assigned:** Chatbot/Rasa Team
