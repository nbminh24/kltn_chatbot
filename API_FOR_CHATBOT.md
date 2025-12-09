# 📡 API Documentation for Chatbot/Rasa Integration

**Date:** December 9, 2025  
**For:** Rasa Action Server / Chatbot Team  
**Backend:** NestJS (TypeScript)

---

## 🔑 Authentication

**Header:** `x-api-key`  
**Value:** `KhoaBiMatChoRasaGoi` (from backend `.env`)  
**Required:** YES (all internal APIs)

---

## 🛍️ Product Search API

### **Endpoint:**
```
GET /internal/products
```

### **Base URL:**
```
http://localhost:3001
```

### **Full URL:**
```
http://localhost:3001/internal/products?search={query}&category={category}&limit={limit}
```

---

### **Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `search` | string | No | Product search query (name, description, or slug) | `tanktop`, `jacket`, `blue shirt` |
| `category` | string | No | Category slug to filter by | `jackets`, `t-shirts` |
| `limit` | integer | No | Max number of results (default: 10) | `5`, `20` |

---

### **Important: What to send in `search` parameter**

❌ **WRONG - Do NOT send full user sentence:**
```python
# WRONG
search = "i want to find a tanktop"  # ❌ Will return 0 results
search = "tôi cần tìm áo khoác"      # ❌ Will return 0 results
```

✅ **CORRECT - Send ONLY the product name/keyword:**
```python
# CORRECT
search = "tanktop"           # ✅ Returns products
search = "jacket"            # ✅ Returns products
search = "blue shirt"        # ✅ Returns products
search = "jacket-men-black"  # ✅ Returns products (slug)
```

---

### **How to Extract Product Name from User Input:**

**User says:** `"i want to find a tanktop"`  
**You should extract:** `"tanktop"`  
**Then call API with:** `search=tanktop`

**User says:** `"tôi cần tìm áo khoác xanh"`  
**You should extract:** `"áo khoác xanh"` or `"ao khoac xanh"`  
**Then call API with:** `search=ao khoac xanh`

---

### **Request Example (Python):**

```python
import requests

# API Configuration
BASE_URL = "http://localhost:3001"
API_KEY = "KhoaBiMatChoRasaGoi"

def search_products(query: str, category: str = None, limit: int = 10):
    """
    Search products via backend API
    
    Args:
        query: Product name/keyword ONLY (not full sentence!)
        category: Optional category slug
        limit: Max results (default 10)
    
    Returns:
        dict: {products: [...], count: int}
    """
    headers = {"x-api-key": API_KEY}
    params = {
        "search": query,  # ⚠️ MUST be extracted product name, NOT full sentence
        "limit": limit
    }
    
    if category:
        params["category"] = category
    
    try:
        response = requests.get(
            f"{BASE_URL}/internal/products",
            headers=headers,
            params=params,
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return {"products": [], "count": 0}
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"products": [], "count": 0}


# ✅ CORRECT USAGE:
# User input: "i want to find a tanktop"
product_name = extract_product_name("i want to find a tanktop")  # Should return "tanktop"
results = search_products(query=product_name)

# ❌ WRONG USAGE:
# results = search_products(query="i want to find a tanktop")  # Will return 0 results!
```

---

### **Response Format:**

**Success (200 OK):**
```json
{
  "products": [
    {
      "id": "22",
      "name": "Tank Top Men Slimfit Basic",
      "slug": "tanktop-men-slimfit-basic",
      "description": "Basic tank top for men...",
      "selling_price": 150000,
      "total_stock": 50,
      "category_name": "T-Shirts",
      "thumbnail_url": "https://example.com/image.jpg",
      "available_sizes": ["S", "M", "L", "XL"],
      "available_colors": ["White", "Black", "Gray"],
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
      ]
    }
  ],
  "count": 1
}
```

**No Results (200 OK):**
```json
{
  "products": [],
  "count": 0
}
```

**Unauthorized (401):**
```json
{
  "statusCode": 401,
  "message": "Unauthorized"
}
```

---

## 🧪 Test Cases

### **Test Case 1: Simple Search**

**Request:**
```bash
GET /internal/products?search=tanktop
Headers: x-api-key: KhoaBiMatChoRasaGoi
```

**Expected Response:**
```json
{
  "products": [...],
  "count": 8
}
```

---

### **Test Case 2: Search with Multiple Words**

**Request:**
```bash
GET /internal/products?search=blue jacket
Headers: x-api-key: KhoaBiMatChoRasaGoi
```

**Expected:** Returns jackets with "blue" in name/description

---

### **Test Case 3: Search by Slug**

**Request:**
```bash
GET /internal/products?search=jacket-men-lightweight
Headers: x-api-key: KhoaBiMatChoRasaGoi
```

**Expected:** Returns products matching that slug pattern

---

### **Test Case 4: Search with Category Filter**

**Request:**
```bash
GET /internal/products?search=shirt&category=t-shirts&limit=5
Headers: x-api-key: KhoaBiMatChoRasaGoi
```

**Expected:** Max 5 t-shirts with "shirt" in name

---

### **Test Case 5: No Results**

**Request:**
```bash
GET /internal/products?search=xyznotexist123
Headers: x-api-key: KhoaBiMatChoRasaGoi
```

**Expected:**
```json
{
  "products": [],
  "count": 0
}
```

---

## 🚨 Common Mistakes

### **Mistake 1: Sending Full Sentence**

❌ **WRONG:**
```python
# User says: "i want to find a tanktop"
search_products(query="i want to find a tanktop")  # ❌ 0 results
```

✅ **CORRECT:**
```python
# User says: "i want to find a tanktop"
product_name = extract_entity("tanktop")  # Extract from NLU or clean text
search_products(query=product_name)  # ✅ Returns results
```

---

### **Mistake 2: Not Handling No Results**

❌ **WRONG:**
```python
results = search_products("xyz")
product = results["products"][0]  # ❌ IndexError if no results!
```

✅ **CORRECT:**
```python
results = search_products("xyz")
if results["count"] > 0:
    products = results["products"]
    # Show products to user
else:
    # Tell user no products found
    dispatcher.utter_message("Sorry, I couldn't find any products matching that.")
```

---

### **Mistake 3: Forgetting API Key**

❌ **WRONG:**
```python
response = requests.get(f"{BASE_URL}/internal/products")  # ❌ 401 Unauthorized
```

✅ **CORRECT:**
```python
headers = {"x-api-key": "KhoaBiMatChoRasaGoi"}
response = requests.get(f"{BASE_URL}/internal/products", headers=headers)  # ✅
```

---

## 💡 Helper Function: Extract Product Name

**Implement this in your Rasa actions:**

```python
import re

def extract_product_name(user_text: str) -> str:
    """
    Extract product name from user input by removing common phrases
    
    Examples:
        "i want to find a tanktop" → "tanktop"
        "tôi cần tìm áo khoác" → "áo khoác"
        "show me blue shirts" → "blue shirts"
    """
    # Convert to lowercase
    text = user_text.lower().strip()
    
    # Remove common English prefixes
    en_prefixes = [
        r'^i\s+want\s+to\s+(find|buy|see|search)\s+(a\s+|an\s+|some\s+)?',
        r'^find\s+(me\s+)?(a\s+|an\s+|some\s+)?',
        r'^show\s+(me\s+)?(a\s+|an\s+|some\s+)?',
        r'^search\s+(for\s+)?(a\s+|an\s+|some\s+)?',
        r'^(can|could)\s+you\s+(find|show)\s+(me\s+)?(a\s+|an\s+)?',
    ]
    
    # Remove common Vietnamese prefixes
    vi_prefixes = [
        r'^tôi\s+cần\s+(tìm|mua)\s+',
        r'^tôi\s+muốn\s+(tìm|mua)\s+',
        r'^tìm\s+(cho\s+tôi\s+)?',
        r'^cho\s+tôi\s+(xem|tìm)\s+',
        r'^tìm\s+giúp\s+tôi\s+',
    ]
    
    # Apply all patterns
    for pattern in en_prefixes + vi_prefixes:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


# Test
assert extract_product_name("i want to find a tanktop") == "tanktop"
assert extract_product_name("tôi cần tìm áo khoác") == "áo khoác"
assert extract_product_name("show me blue jackets") == "blue jackets"
assert extract_product_name("tanktop") == "tanktop"
```

---

## 🔧 Complete Action Example

**File:** `actions/actions.py`

```python
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import re

class ActionSearchProducts(Action):
    
    def name(self) -> Text:
        return "action_search_products"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Step 1: Try to get entity from NLU
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        
        # Step 2: If no entity, try slot
        if not product_name:
            product_name = tracker.get_slot("product_name")
        
        # Step 3: If still no entity, extract from user text
        if not product_name:
            user_text = tracker.latest_message.get('text', '')
            product_name = self.extract_product_name(user_text)
        
        # Step 4: If still nothing, ask user
        if not product_name:
            dispatcher.utter_message(
                text="What product are you looking for? For example: jacket, t-shirt, jeans..."
            )
            return []
        
        # Log what we're searching
        print(f"🔍 Extracted product name: '{product_name}'")
        
        # Step 5: Call backend API
        results = self.search_products(product_name)
        
        # Step 6: Handle response
        if results["count"] > 0:
            products = results["products"][:5]  # Show max 5
            
            response = f"I found {results['count']} products:\n\n"
            for p in products:
                response += f"• {p['name']} - ${p['selling_price']:,} VND\n"
            
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find any products matching '{product_name}'. "
                     "Could you try a different search term?"
            )
        
        return []
    
    def extract_product_name(self, user_text: str) -> str:
        """Extract product name from user input"""
        text = user_text.lower().strip()
        
        # Remove common prefixes
        patterns = [
            r'^i\s+want\s+to\s+(find|buy)\s+(a\s+|an\s+)?',
            r'^find\s+(me\s+)?(a\s+|an\s+)?',
            r'^show\s+(me\s+)?(a\s+|an\s+)?',
            r'^tôi\s+cần\s+tìm\s+',
            r'^tìm\s+(cho\s+tôi\s+)?',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def search_products(self, query: str) -> dict:
        """Call backend search API"""
        try:
            response = requests.get(
                "http://localhost:3001/internal/products",
                headers={"x-api-key": "KhoaBiMatChoRasaGoi"},
                params={"search": query, "limit": 10},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error: {response.status_code}")
                return {"products": [], "count": 0}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return {"products": [], "count": 0}
```

---

## 📊 Expected Behavior

### **Scenario 1: User says "i want to find a tanktop"**

**Step 1:** Extract entity
- NLU extracts: `product_name = "tanktop"`  
OR  
- Text cleanup: `"i want to find a tanktop"` → `"tanktop"`

**Step 2:** Call API
```python
GET /internal/products?search=tanktop
```

**Step 3:** Get response
```json
{
  "products": [8 tank tops],
  "count": 8
}
```

**Step 4:** Show to user
```
I found 8 products:
• Tank Top Men Slimfit Basic - 150,000 VND
• Tank Top Men Extra Cool - 180,000 VND
...
```

---

### **Scenario 2: User says "tanktop" (direct)**

**Step 1:** Extract entity
- `product_name = "tanktop"` (already clean)

**Step 2-4:** Same as above ✅

---

## 🎯 Summary

**Key Points for Chatbot Team:**

1. ✅ **Always extract product name** before calling API
2. ✅ **Never send full sentence** as search query
3. ✅ **Include API key** in all requests
4. ✅ **Handle empty results** gracefully
5. ✅ **Add timeout** (5 seconds recommended)
6. ✅ **Log extracted query** for debugging

---

## 🐛 Related Bug Reports

- **`BUG_CHATBOT_ENTITY_EXTRACTION.md`** - Full details on entity extraction issue
- **`IMPROVEMENT_CHATBOT_SLUG_RECOGNITION.md`** - NLU training for slug patterns

---

**API Status:** ✅ Working  
**Backend Version:** 1.0  
**Last Updated:** 2025-12-09  
**Contact:** Backend Team
