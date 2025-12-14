# 🚨 RASA FIX: Product Search Action Missing Custom Data

**Priority:** HIGH  
**Impact:** Product cards không hiển thị vì Rasa không gửi custom data  
**Date:** 14/12/2025

---

## 📋 PROBLEM

Rasa action `action_search_products` chỉ gửi **text message**, thiếu **custom data** cho product cards.

### Current Behavior (WRONG):

**Rasa Response:**
```python
dispatcher.utter_message(
    text="Found 5 products for 'shirt':\n\n" +
         "1. **relaxed-fit-t-shirt: Be Bold** - $6.36\n" +
         "2. **relaxed-fit-t-shirt: Retro** - $6.36\n" +
         "..."
)
```

**Backend Receives:**
```json
[
  {
    "text": "Found 5 products for 'shirt':\n\n1. **...",
    "recipient_id": "customer_1"
    // ❌ NO custom field
  }
]
```

**Frontend Receives:**
```json
{
  "bot_responses": [
    {
      "message": "Found 5 products...",
      "sender": "bot"
      // ❌ NO custom field
    }
  ]
}
```

**Result:** Only text displayed, NO ProductCarousel 😢

---

## ✅ SOLUTION

### File: `actions/actions.py`

**Action:** `ActionSearchProducts`

#### Before (WRONG):
```python
class ActionSearchProducts(Action):
    def name(self) -> Text:
        return "action_search_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get search query
        query = tracker.get_slot('product_query') or tracker.latest_message.get('text')
        
        # Call backend API
        api_client = BackendAPIClient()
        result = api_client.search_products(query=query, limit=5)
        
        if result and result.get('products'):
            products = result['products']
            
            # ❌ WRONG: Only send text
            message = f"Found {len(products)} products for '{query}':\n\n"
            for i, p in enumerate(products, 1):
                name = p.get('name', 'Unknown')
                slug = p.get('slug', 'unknown')
                price = p.get('selling_price', 0)
                stock = "✅" if p.get('stock_quantity', 0) > 0 else "❌"
                message += f"{i}. **{slug}: {name}** - ${price:.2f} {stock}\n"
            
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text="Sorry, I couldn't find any products.")
        
        return []
```

#### After (CORRECT):
```python
class ActionSearchProducts(Action):
    def name(self) -> Text:
        return "action_search_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get search query
        query = tracker.get_slot('product_query') or tracker.latest_message.get('text')
        
        # Call backend API
        api_client = BackendAPIClient()
        result = api_client.search_products(query=query, limit=5)
        
        if result and result.get('products'):
            products = result['products']
            
            # ✅ Format products for frontend
            product_list = []
            for p in products:
                product_list.append({
                    "product_id": p.get('id'),
                    "name": p.get('name'),
                    "slug": p.get('slug'),
                    "price": float(p.get('selling_price', 0)),
                    "thumbnail": p.get('thumbnail_url'),
                    "rating": float(p.get('average_rating', 0)),
                    "reviews": p.get('total_reviews', 0),
                    "in_stock": p.get('stock_quantity', 0) > 0
                })
            
            # ✅ CORRECT: Send text + custom data
            dispatcher.utter_message(
                text=f"Found {len(products)} products for '{query}':",
                json_message={
                    "custom": {
                        "type": "product_list",
                        "products": product_list
                    }
                }
            )
            
            # Optional: Add follow-up message
            dispatcher.utter_message(
                text="💡 Click on any product to see details! 😊"
            )
        else:
            dispatcher.utter_message(text="Sorry, I couldn't find any products.")
        
        return []
```

---

## 🔍 KEY CHANGES

### 1. **Format Product Data**
```python
product_list = []
for p in products:
    product_list.append({
        "product_id": p.get('id'),           # ← Frontend needs this
        "name": p.get('name'),
        "slug": p.get('slug'),               # ← For navigation
        "price": float(p.get('selling_price', 0)),
        "thumbnail": p.get('thumbnail_url'), # ← For image display
        "in_stock": p.get('stock_quantity', 0) > 0
    })
```

### 2. **Use `json_message` Parameter**
```python
dispatcher.utter_message(
    text="Found 5 products:",              # Text message
    json_message={                          # Custom data
        "custom": {
            "type": "product_list",         # Frontend expects this type
            "products": product_list
        }
    }
)
```

### 3. **Remove Text-Only List**
```python
# ❌ DELETE THIS
message = "1. **Product A** - $6.36\n2. **Product B** - $12.72"
dispatcher.utter_message(text=message)

# ✅ USE THIS
dispatcher.utter_message(
    text="Found 5 products:",
    json_message={"custom": {...}}
)
```

---

## 🧪 TESTING

### Step 1: Restart Rasa Actions Server
```bash
cd rasa-project
rasa run actions --debug
```

### Step 2: Test with Rasa Shell
```bash
rasa shell
# Type: "i want to find a shirt"
```

**Expected Output:**
```json
{
  "text": "Found 5 products for 'shirt':",
  "custom": {
    "type": "product_list",
    "products": [
      {
        "product_id": 496,
        "name": "Be Bold Become Fearless",
        "slug": "relaxed-fit-t-shirt-be-bold",
        "price": 6.36,
        "thumbnail": "https://...",
        "in_stock": true
      }
    ]
  }
}
```

### Step 3: Test with Frontend
1. Open chat widget
2. Type: "i want to find a shirt"
3. Check console:
   ```javascript
   bot_responses[0].custom !== undefined  // ✅ Must be true
   ```
4. Check UI:
   - ✅ ProductCarousel displays
   - ✅ 5 product cards visible
   - ✅ Click card → Navigate to product detail

---

## 📊 FLOW VERIFICATION

```
User: "i want to find a shirt"
    ↓
Rasa NLU: intent=search_product, entities=[shirt]
    ↓
Rasa Action: action_search_products
    ↓
API Call: GET /api/v1/products?search=shirt&limit=5
    ↓
Rasa Response: {
  text: "Found 5 products:",
  custom: {                    // ← MUST HAVE
    type: "product_list",
    products: [...]
  }
}
    ↓
Backend Receives: rasaResponse[0].custom
    ↓
Backend Attaches: botMessage.custom = rasaMsg.custom
    ↓
Frontend Receives: bot_responses[0].custom
    ↓
MessageRenderer: case 'product_list': return <ProductCarousel />
    ↓
UI: Product cards displayed! ✅
```

---

## 📝 CHECKLIST

- [ ] Update `actions/actions.py` - `ActionSearchProducts`
- [ ] Format products with all required fields
- [ ] Use `dispatcher.utter_message(text=..., json_message={...})`
- [ ] Remove old text-only list formatting
- [ ] Restart Rasa actions server
- [ ] Test with rasa shell - verify custom field
- [ ] Test with frontend - verify ProductCarousel displays
- [ ] Update other actions if needed (recommendations, cart, etc.)

---

## 🔗 RELATED ACTIONS

Apply same fix to other product-related actions:

### ActionProductRecommendations
```python
dispatcher.utter_message(
    text="Here are some recommendations:",
    json_message={
        "custom": {
            "type": "product_list",
            "products": [...]
        }
    }
)
```

### ActionShowCart
```python
dispatcher.utter_message(
    text="Your cart:",
    json_message={
        "custom": {
            "type": "cart_summary",
            "items": [...],
            "total": 300.00
        }
    }
)
```

---

## 📞 SUPPORT

**Backend Fixed:** ✅ (custom field forwarding)  
**Frontend Ready:** ✅ (ProductCarousel component)  
**Rasa Needs Fix:** ❌ (this document)

**Contact:** Rasa Team  
**Priority:** HIGH - Blocking product cards feature
