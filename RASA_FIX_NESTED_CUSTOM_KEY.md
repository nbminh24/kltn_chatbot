# 🚨 RASA URGENT FIX: Nested Custom Key

**Priority:** CRITICAL  
**Impact:** Product cards showing "No message" due to double-nested custom key  
**Date:** 14/12/2025 10:32

---

## 📋 PROBLEM

Rasa actions đang wrap `json_message` trong key `"custom"`, gây ra **double nesting**.

### Current Response (WRONG):
```json
{
  "text": "Found 5 products:",
  "custom": {
    "custom": {              // ← NESTED 2 LẦN!
      "type": "product_list",
      "products": [...]
    }
  }
}
```

### Expected Response (CORRECT):
```json
{
  "text": "Found 5 products:",
  "custom": {                // ← CHỈ 1 LẦN
    "type": "product_list",
    "products": [...]
  }
}
```

### Frontend Log:
```javascript
// Console shows:
message.custom.custom.type = "product_list"  // ❌ WRONG

// Frontend expects:
message.custom.type = "product_list"         // ✅ CORRECT
```

---

## 🔧 FIX

### File: `actions/actions.py`

#### ALL Product-Related Actions Need This Fix:

**WRONG:**
```python
dispatcher.utter_message(
    text="Found 5 products for 'shirt':",
    json_message={
        "custom": {           # ← XOÁ KEY NÀY
            "type": "product_list",
            "products": product_list
        }
    }
)
```

**CORRECT:**
```python
dispatcher.utter_message(
    text="Found 5 products for 'shirt':",
    json_message={            # ← KHÔNG CẦN "custom" KEY
        "type": "product_list",
        "products": product_list
    }
)
```

---

## 📝 WHY?

**Rasa's `json_message` Parameter Behavior:**

Khi bạn dùng `json_message`, Rasa **TỰ ĐỘNG** wrap content vào key `"custom"`:

```python
# Code bạn viết:
dispatcher.utter_message(
    text="Hello",
    json_message={"type": "product_list", "products": [...]}
)

# Rasa webhook response:
{
  "text": "Hello",
  "custom": {              # ← Rasa TỰ ĐỘNG THÊM
    "type": "product_list",
    "products": [...]
  }
}
```

Nếu bạn viết:
```python
json_message={"custom": {"type": "product_list"}}
```

Kết quả sẽ là:
```json
{
  "custom": {              # ← Rasa thêm
    "custom": {            # ← Bạn thêm
      "type": "product_list"
    }
  }
}
```

→ **NESTED 2 LẦN!**

---

## ✅ ACTIONS CẦN FIX

### 1. ActionSearchProducts

**Before:**
```python
dispatcher.utter_message(
    text=f"Found {len(products)} products for '{search_query}':",
    json_message={
        "custom": {                    # ← XOÁ
            "type": "product_list",
            "products": product_list
        }
    }
)
```

**After:**
```python
dispatcher.utter_message(
    text=f"Found {len(products)} products for '{search_query}':",
    json_message={
        "type": "product_list",        # ← TRỰC TIẾP
        "products": product_list
    }
)
```

---

### 2. ActionRecommendProducts

**Before:**
```python
json_message={
    "custom": {                        # ← XOÁ
        "type": "product_list",
        "products": recommendations
    }
}
```

**After:**
```python
json_message={
    "type": "product_list",            # ← TRỰC TIẾP
    "products": recommendations
}
```

---

### 3. ActionViewCart

**Before:**
```python
json_message={
    "custom": {                        # ← XOÁ
        "type": "cart_summary",
        "items": formatted_items,
        "total": total
    }
}
```

**After:**
```python
json_message={
    "type": "cart_summary",            # ← TRỰC TIẾP
    "items": formatted_items,
    "total": total
}
```

---

## 🧪 TESTING

### Test 1: Check Console

**Send message:** "i want to find a shirt"

**Check console log:**
```javascript
// ✅ CORRECT:
message.custom.type === "product_list"
message.custom.products.length > 0

// ❌ WRONG (before fix):
message.custom.custom.type === "product_list"
```

### Test 2: Check UI

**Expected:**
- ✅ ProductCarousel displays
- ✅ 5 product cards visible
- ✅ NO "No message" text

**Wrong (before fix):**
- ❌ "No message" appears
- ❌ No ProductCarousel

---

## 📋 CHECKLIST

- [ ] Remove `"custom"` key from `json_message` in ActionSearchProducts
- [ ] Remove `"custom"` key from `json_message` in ActionRecommendProducts
- [ ] Remove `"custom"` key from `json_message` in ActionViewCart
- [ ] Restart Rasa actions server: `rasa run actions`
- [ ] Test: Send "i want to find a shirt"
- [ ] Verify console: `message.custom.type` (not `message.custom.custom.type`)
- [ ] Verify UI: ProductCarousel displays

---

## 🚀 QUICK FIX COMMAND

```bash
# In Rasa project folder
cd c:\Users\USER\Downloads\kltn_chatbot

# Find and replace in actions.py
# FIND: json_message={\n        "custom": {
# REPLACE WITH: json_message={

# Restart actions
rasa run actions --debug
```

---

## 📞 CONTACT

**Reporter:** Frontend Team  
**Priority:** CRITICAL  
**Blocking:** Product cards feature  
**ETA:** 5 minutes (simple find & replace)
