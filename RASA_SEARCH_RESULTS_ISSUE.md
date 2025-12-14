# 🐛 Bug Report: Incorrect Product Search Results

**Date:** December 14, 2024  
**Priority:** HIGH  
**Component:** Rasa Chatbot / Backend Product Search API  
**Reporter:** Frontend Team

---

## 🚨 Problem Summary

When users search for products via chatbot, the results returned are **incorrect** and do not match the backend product search API results.

**Search Query:** `"meow shirt"`

---

## 📊 Evidence

### ❌ Chatbot Results (WRONG)

**User message:** "i want to find a meow shirt"

**Bot response:**
```
Found 5 products for 'meow shirt':

1. relaxed-fit-t-shirt: Sushi Meow (product_id: 5)
2. relaxed-fit-t-shirt: Be Bold Become Fearless (product_id: 15)
3. relaxed-fit-t-shirt: Retro Dachshund (product_id: 16)
4. relaxed-fit-t-shirt: Original Summer (product_id: 1)
5. relaxed-fit-t-shirt: Ocean Festival De Verano (product_id: 10)
```

**Issues:**
- ❌ Only 1 product actually has "meow" in the name (Sushi Meow)
- ❌ Other 4 products are completely irrelevant:
  - "Be Bold Become Fearless" - no "meow"
  - "Retro Dachshund" - no "meow", no "shirt"
  - "Original Summer" - no "meow"
  - "Ocean Festival De Verano" - no "meow"

---

### ✅ Backend API Results (CORRECT)

**API Endpoint:** `GET /api/chatbot/products/search?query=meow%20shirt&limit=5`

**API Response:**
```json
{
  "success": true,
  "data": {
    "query": "meow shirt",
    "total": 5,
    "products": [
      {
        "product_id": "492",
        "name": "ringer-t-shirt: Relaxed Fit Sweet Pastry Meow Meow Bead",
        "category": "ringer-t-shirt",
        "price": "13.52"
      },
      {
        "product_id": "448",
        "name": "ringer-t-shirt: Relaxed Fit Animal Mood Funny Meow",
        "category": "ringer-t-shirt",
        "price": "13.52"
      },
      {
        "product_id": "443",
        "name": "ringer-t-shirt: Relaxed Fit Vitamin Meow",
        "category": "ringer-t-shirt",
        "price": "13.52"
      },
      {
        "product_id": "430",
        "name": "ringer-t-shirt: Relaxed Fit Meow Meow Heart",
        "category": "ringer-t-shirt",
        "price": "13.52"
      },
      {
        "product_id": "416",
        "name": "ringer-t-shirt: Relaxed Fit Banana Meow",
        "category": "ringer-t-shirt",
        "price": "13.52"
      }
    ]
  }
}
```

**Analysis:**
- ✅ ALL 5 products contain "meow" in the name
- ✅ ALL products are shirts (ringer-t-shirt category)
- ✅ Results are highly relevant to the search query
- ✅ Correct product_id range (416-492)

---

## 🔍 Root Cause Analysis

### Issue Location

The bug is in **Rasa's `ActionSearchProducts`** action or the way it calls the backend search API.

**Possible causes:**

1. **Wrong API endpoint being called**
   - Rasa may be calling a different search endpoint
   - Or using incorrect query parameters

2. **Hardcoded or cached results**
   - Rasa might be returning static demo data
   - Results not actually from live search API

3. **Query transformation issue**
   - User's search term not properly passed to backend
   - Query parameter encoding problem

4. **Product ID mismatch**
   - Rasa is returning products with IDs: 5, 15, 16, 1, 10
   - Backend returns products with IDs: 492, 448, 443, 430, 416
   - These are completely different product sets

---

## 🔧 Expected Behavior

```python
# In actions/actions.py - ActionSearchProducts

def run(self, dispatcher, tracker, domain):
    query = tracker.get_slot("product_query") or "shirt"
    
    # Call backend search API
    response = requests.get(
        f"{BACKEND_URL}/api/chatbot/products/search",
        params={
            "query": query,
            "limit": 5
        },
        headers={"X-Internal-Api-Key": INTERNAL_API_KEY}
    )
    
    # Response should contain relevant products
    products = response.json()["data"]["products"]
    
    dispatcher.utter_message(
        text=f"Found {len(products)} products for '{query}':",
        json_message={
            "type": "product_list",
            "products": products
        }
    )
```

**Key requirements:**
- ✅ Use actual search query from user
- ✅ Call correct backend endpoint: `/api/chatbot/products/search`
- ✅ Pass query parameter properly
- ✅ Return live search results (not cached/hardcoded)

---

## 🧪 Test Cases

### Test Case 1: "meow shirt"

**Expected:** Products with "meow" in name, shirt category  
**Actual:** Random products (mostly irrelevant)  
**Status:** ❌ FAILED

### Test Case 2: "relaxed fit"

**Expected:** Products with "relaxed fit" in name  
**Actual:** (Need to test)  
**Status:** ⏳ PENDING

### Test Case 3: "ringer"

**Expected:** Products in ringer-t-shirt category  
**Actual:** (Need to test)  
**Status:** ⏳ PENDING

---

## 📝 Debug Checklist for Rasa Team

### Step 1: Verify API Endpoint
```bash
# Check what URL Rasa is calling
# Add logging in actions.py:

logger.info(f"🔍 Calling search API: {url}")
logger.info(f"🔍 Query params: {params}")
logger.info(f"🔍 Response: {response.json()}")
```

### Step 2: Check Query Parameter
```python
# Verify the query is correct
query = tracker.get_slot("product_query")
logger.info(f"🔍 User query: '{query}'")

# Make sure it's passed to API
params = {"query": query, "limit": 5}
```

### Step 3: Compare Results
```python
# Log product IDs returned
product_ids = [p["product_id"] for p in products]
logger.info(f"🔍 Returned product IDs: {product_ids}")

# Should match backend API results
```

### Step 4: Check for Hardcoded Data
```python
# Search for any hardcoded product lists
# Example of WRONG code:
products = [
    {"product_id": "5", "name": "Sushi Meow", ...},  # ❌ Hardcoded
    {"product_id": "15", ...},  # ❌ Hardcoded
]

# Should be:
response = requests.get(...)  # ✅ Live API call
products = response.json()["data"]["products"]  # ✅ Dynamic results
```

---

## 🎯 Success Criteria

**When fixed, this query:**
```
User: "i want to find a meow shirt"
```

**Should return:**
```
Bot: "Found 5 products for 'meow shirt':"

[Product Cards:]
1. ringer-t-shirt: Relaxed Fit Sweet Pastry Meow Meow Bead ($13.52)
2. ringer-t-shirt: Relaxed Fit Animal Mood Funny Meow ($13.52)
3. ringer-t-shirt: Relaxed Fit Vitamin Meow ($13.52)
4. ringer-t-shirt: Relaxed Fit Meow Meow Heart ($13.52)
5. ringer-t-shirt: Relaxed Fit Banana Meow ($13.52)
```

**Validation:**
- ✅ All products contain "meow"
- ✅ All products are shirts
- ✅ Product IDs match backend API (492, 448, 443, 430, 416)
- ✅ Results change based on search query

---

## 🚀 Next Steps

1. **Rasa Team:** Review `ActionSearchProducts` implementation
2. **Verify:** API endpoint and query parameters
3. **Test:** Multiple search queries to confirm fix
4. **Document:** Update if using any caching/indexing layer

---

## 📎 Related Files

**Backend API:**
- Endpoint: `GET /api/chatbot/products/search`
- Location: `chatbot.controller.ts` / `chatbot.service.ts`

**Rasa:**
- Action: `ActionSearchProducts`
- File: `actions/actions.py` (estimated line ~300-350)

**Frontend:** (No changes needed)
- Already displays whatever products Rasa sends
- UI working correctly

---

## 💡 Additional Notes

**Why This Matters:**
- Poor search results destroy user trust in chatbot
- Users expect accurate, relevant product suggestions
- Current behavior makes chatbot seem broken/unreliable

**User Perspective:**
> "I asked for a meow shirt and got 'Retro Dachshund'? What does a dog have to do with cats?"

**Fix Priority:** HIGH - Critical for chatbot credibility

---

**For questions or testing support, contact Frontend Team.**
