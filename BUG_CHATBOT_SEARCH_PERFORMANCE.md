# 🐛 BUG REPORT - Chatbot Search Action Performance Issue

**Date:** December 9, 2025, 10:01 AM  
**Reporter:** Backend Team  
**Severity:** 🔴 HIGH (Causing timeouts and poor UX)  
**Status:** ACTIVE  
**Assigned to:** Chatbot/Rasa Team

---

## 📋 SUMMARY

`action_search_products` đang chạy quá lâu (>10 seconds), khiến backend timeout. API call chỉ mất ~2s nhưng sau đó action bị treo/chậm ở bước xử lý response.

---

## 🔴 ISSUE

### **Test Case:**

**User input:**
```
"i want to find a áo khoác"
```

**Current behavior:**
1. ✅ Intent detected: `search_product`
2. ✅ Action triggered: `action_search_products`
3. ✅ API call: `search_products` - took **1.896s** (acceptable)
4. ❌ **Then HANGS** - no more logs after API call
5. ❌ Total time: **>10 seconds** → backend timeout
6. ❌ User sees error message

---

## 📊 EVIDENCE

### **Chatbot Logs:**
```
2025-12-09 09:57:07 INFO  actions.actions  
- 🚀 Starting action_search_products

2025-12-09 09:57:07 INFO  actions.actions  
- Searching products with query: áo khoác

2025-12-09 09:57:07 INFO  actions.api_client  
- BackendAPIClient initialized with base_url: http://localhost:3001

2025-12-09 09:57:07 INFO  actions.api_client  
- Searching products with query: áo khoác, category: None

2025-12-09 09:57:09 INFO  actions.actions  
- ⏱️ API search_products took 1.896s

[NO MORE LOGS - HANGS HERE FOR >8 SECONDS]
```

### **Backend Logs:**
```
[Chat] Sender: ef35fb12-78d5-49af-b8c3-4e218d36bf38, 
       Message: "i want to find a "áo khoác""
[Chat] Rasa webhook failed: timeout of 10000ms exceeded
```

---

## 💥 ROOT CAUSE ANALYSIS

### **Timeline:**
```
T=0s     → Action starts ✅
T=0s     → API call initiated ✅
T=1.9s   → API responds ✅ (2s is acceptable)
T=1.9s   → [MYSTERY GAP - NO LOGS]
T=10s+   → Backend timeout ❌
```

### **Problem:** 
Action bị treo hoặc chậm ở một trong các bước sau API call:
1. Parsing API response
2. Processing/formatting product data
3. Building custom payload
4. Calling `dispatcher.utter_message()`
5. Returning from action

### **Suspected Code Issues:**

```python
# File: actions/actions.py (suspected)

def run(self, dispatcher, tracker, domain):
    # ... API call (1.9s) ✅
    results = api_client.search_products(query)
    logger.info(f"API search_products took {time}s")
    
    # ❌ PROBABLY HANGS HERE - NO LOGGING
    # Possible issues:
    # 1. Heavy data processing without logs
    # 2. Infinite loop in data formatting
    # 3. Large payload causing serialization delay
    # 4. Dispatcher blocking
    # 5. Database operation without timeout
    
    # Process results (NO LOGGING HERE ❌)
    formatted_products = []
    for product in results:
        # Heavy processing?
        # Image downloads?
        # Database lookups?
        formatted_products.append(...)
    
    # Send response (NO LOGGING HERE ❌)
    dispatcher.utter_message(
        text="...",
        custom={"products": formatted_products}  # Large payload?
    )
    
    # ❌ Never reaches this point
    return []
```

---

## 🛠️ HOW TO FIX

### **Priority 1: ADD DETAILED LOGGING** (CRITICAL)

**Thêm log CHI TIẾT cho TỪNG BƯỚC sau API call:**

```python
def run(self, dispatcher, tracker, domain):
    logger.info("🚀 Starting action_search_products")
    
    # Get query
    query = tracker.get_slot("product_name")
    logger.info(f"📝 Query extracted: {query}")
    
    # API call
    logger.info("🌐 Calling backend API...")
    start_time = time.time()
    results = api_client.search_products(query)
    api_time = time.time() - start_time
    logger.info(f"✅ API responded in {api_time:.3f}s with {len(results)} products")
    
    # ✅ ADD: Check response validity
    logger.info(f"📊 Response type: {type(results)}, length: {len(results)}")
    
    # ✅ ADD: Processing step logs
    logger.info("🔄 Starting response processing...")
    try:
        formatted_products = []
        for idx, product in enumerate(results):
            # ✅ ADD: Log every N products to avoid spam
            if idx % 10 == 0:
                logger.info(f"  Processing product {idx}/{len(results)}...")
            
            formatted_products.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "price": product.get("price"),
                # ... other fields
            })
        
        logger.info(f"✅ Finished processing {len(formatted_products)} products")
    
    except Exception as e:
        logger.error(f"❌ Error processing products: {e}", exc_info=True)
        dispatcher.utter_message(text="Xin lỗi, có lỗi khi xử lý kết quả.")
        return []
    
    # ✅ ADD: Before dispatcher
    logger.info("📤 Preparing dispatcher payload...")
    payload = {
        "type": "product_list",
        "products": formatted_products[:10]  # Limit products
    }
    logger.info(f"📦 Payload size: {len(str(payload))} characters")
    
    # ✅ ADD: Dispatcher timing
    logger.info("📨 Sending message via dispatcher...")
    dispatch_start = time.time()
    try:
        dispatcher.utter_message(
            text=f"Tìm thấy {len(formatted_products)} sản phẩm",
            custom=payload
        )
        dispatch_time = time.time() - dispatch_start
        logger.info(f"✅ Dispatcher completed in {dispatch_time:.3f}s")
    
    except Exception as e:
        logger.error(f"❌ Dispatcher error: {e}", exc_info=True)
        dispatcher.utter_message(text="Xin lỗi, không thể gửi kết quả.")
        return []
    
    # ✅ ADD: Action completion
    total_time = time.time() - start_time
    logger.info(f"🏁 Action completed in {total_time:.3f}s total")
    
    return []
```

---

### **Priority 2: OPTIMIZE PERFORMANCE**

#### **A. Limit Product Count**
```python
# ❌ DON'T return all products
formatted_products = [process(p) for p in results]

# ✅ Limit to reasonable amount
MAX_PRODUCTS = 10
formatted_products = [process(p) for p in results[:MAX_PRODUCTS]]
logger.info(f"Limited to {MAX_PRODUCTS} products from {len(results)} results")
```

#### **B. Simplify Product Data**
```python
# ❌ DON'T include unnecessary data
formatted_products.append({
    "id": product["id"],
    "name": product["name"],
    "description": product["long_description"],  # Remove if not needed
    "all_variants": product["variants"],  # Remove if heavy
    "full_images": product["all_images"],  # Remove if not shown
    # ... 50 more fields
})

# ✅ Only include what frontend displays
formatted_products.append({
    "id": product["id"],
    "name": product["name"],
    "price": product["selling_price"],
    "thumbnail": product["thumbnail_url"],  # Only 1 image
    "slug": product["slug"]
})
```

#### **C. Add Timeout to Operations**
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError()
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# Use timeout wrapper
try:
    with timeout(5):  # Max 5s for processing
        formatted_products = process_products(results)
except TimeoutError:
    logger.error("Processing timeout after 5s")
    # Return limited results
```

---

### **Priority 3: IDENTIFY SPECIFIC BOTTLENECK**

**Run với logging chi tiết, sau đó kiểm tra:**

#### **Scenario A: Processing hung**
```
✅ API responded in 1.896s with 50 products
📊 Response type: list, length: 50
🔄 Starting response processing...
  Processing product 0/50...
  Processing product 10/50...
  [HANGS HERE - NEVER FINISHES]
```
→ **Fix:** Có loop vô hạn hoặc heavy operation trong processing

#### **Scenario B: Dispatcher hung**
```
✅ Finished processing 50 products
📤 Preparing dispatcher payload...
📦 Payload size: 250000 characters
📨 Sending message via dispatcher...
[HANGS HERE - DISPATCHER BLOCKS]
```
→ **Fix:** Payload quá lớn, cần giảm size hoặc paginate

#### **Scenario C: External call without timeout**
```
✅ Finished processing 50 products
📤 Calling image CDN to validate URLs...
[HANGS HERE - WAITING FOR CDN]
```
→ **Fix:** Remove external calls hoặc add timeout

---

## 🧪 TESTING REQUIREMENTS

### **After adding logs, test với:**

```
Input: "tìm áo khoác"

Expected logs sequence:
1. ✅ "🚀 Starting action_search_products"
2. ✅ "📝 Query extracted: áo khoác"
3. ✅ "🌐 Calling backend API..."
4. ✅ "✅ API responded in 1.9s with 15 products"
5. ✅ "📊 Response type: list, length: 15"
6. ✅ "🔄 Starting response processing..."
7. ✅ "  Processing product 0/15..."
8. ✅ "  Processing product 10/15..."
9. ✅ "✅ Finished processing 15 products"
10. ✅ "📤 Preparing dispatcher payload..."
11. ✅ "📦 Payload size: 5000 characters"
12. ✅ "📨 Sending message via dispatcher..."
13. ✅ "✅ Dispatcher completed in 0.1s"
14. ✅ "🏁 Action completed in 2.5s total"

Time breakdown:
- API: 1.9s
- Processing: 0.5s
- Dispatcher: 0.1s
- Total: 2.5s ✅ (under 10s limit)
```

---

## 📊 PERFORMANCE TARGETS

| Operation | Current | Target | Max Acceptable |
|-----------|---------|--------|----------------|
| API Call | ~2s ✅ | <2s | <3s |
| Processing | ??? ❌ | <1s | <2s |
| Dispatcher | ??? ❌ | <0.5s | <1s |
| **Total** | **>10s ❌** | **<4s** | **<8s** |

Backend timeout: 10s
Target action time: <5s để có buffer

---

## 🎯 CRITICAL QUESTIONS TO ANSWER

Sau khi add logging, cần trả lời:

1. **Bước nào chiếm >8 giây?**
   - Processing products?
   - Building payload?
   - Dispatcher call?
   - Something else?

2. **Có operation blocking nào không?**
   - Database queries?
   - File I/O?
   - External API calls?
   - Image processing?

3. **Data size có quá lớn không?**
   - Bao nhiêu products được return?
   - Size của mỗi product object?
   - Total payload size?

4. **Có error bị nuốt không?**
   - Try-catch blocks nuốt exceptions?
   - Silent failures?

---

## 📞 ACTION ITEMS

### **Chatbot Team (URGENT):**

**Bước 1: Add logging (30 phút)**
- [ ] Add log trước/sau TỪNG bước quan trọng
- [ ] Log timing cho mỗi operation
- [ ] Log data sizes và types
- [ ] Log errors với full traceback

**Bước 2: Test và collect logs (15 phút)**
- [ ] Run với input: "tìm áo khoác"
- [ ] Collect FULL logs từ start đến end/hang
- [ ] Share logs với backend team

**Bước 3: Identify bottleneck (dựa trên logs)**
- [ ] Xác định operation nào >5s
- [ ] Check có infinite loop không
- [ ] Check có blocking call không

**Bước 4: Apply optimization**
- [ ] Limit product count (MAX 10-20)
- [ ] Simplify product data structure
- [ ] Remove unnecessary operations
- [ ] Add timeouts

**Bước 5: Verify fix**
- [ ] Total action time <5s
- [ ] No backend timeouts
- [ ] Logs show clear flow

---

## 💡 TEMPORARY WORKAROUND

Nếu chưa fix được, có thể:

**Option A: Increase backend timeout**
```typescript
// chat.service.ts
timeout: 20000, // 20 seconds instead of 10
```
⚠️ Not recommended - chỉ che giấu vấn đề

**Option B: Return fewer products immediately**
```python
# Quick fix in action
results = api_client.search_products(query)
quick_results = results[:5]  # Only 5 products
dispatcher.utter_message(
    text=f"Đây là 5 sản phẩm đầu tiên (tìm thấy {len(results)} sản phẩm)",
    custom={"products": quick_results}
)
```

---

## 🔍 DEBUGGING CHECKLIST

When logs are added, check:

```
✅ Action starts
✅ Query extracted
✅ API called
✅ API responds (check time)
❓ Response parsed (ADD LOG)
❓ Loop starts (ADD LOG)
❓ Processing each item (ADD LOG every N items)
❓ Loop completes (ADD LOG)
❓ Payload prepared (ADD LOG + size)
❓ Dispatcher called (ADD LOG)
❓ Dispatcher completes (ADD LOG + time)
❓ Action returns (ADD LOG)
```

**Nếu bất kỳ bước nào không có log → đó là nơi bị treo!**

---

**Priority:** 🔴 **HIGH - URGENT**  
**Impact:** Users cannot get product search results  
**Timeline:** Need detailed logs ASAP to identify bottleneck  
**Next Step:** Add comprehensive logging and re-test

---

**Bug Report Created:** 2025-12-09 10:01  
**Reporter:** Backend Team  
**Status:** Waiting for detailed logs from Chatbot team
