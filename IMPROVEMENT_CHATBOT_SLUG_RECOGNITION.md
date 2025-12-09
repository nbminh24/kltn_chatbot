# 💡 IMPROVEMENT REQUEST - Chatbot Slug Recognition

**Date:** December 9, 2025, 10:14 AM  
**Reporter:** Backend Team  
**Severity:** ⚠️ MEDIUM (Quality improvement)  
**Status:** ACTIVE  
**Type:** Enhancement  
**Assigned to:** Chatbot/Rasa Team

---

## 📋 SUMMARY

Chatbot NLU không nhận diện được product slugs/codes khi user paste từ URL hoặc search history. Intent confidence rất thấp (20%) dẫn đến fallback không cần thiết.

---

## 🔴 ISSUE

### **Test Case:**

**User input:**
```
"tôi cần tìm ao-khoac-nam-lightweight-windbreaker-form-regular"
```

**Current behavior:**
1. ❌ NLU confidence: **19.7%** (very low)
2. ❌ Trigger fallback (technically correct for low confidence)
3. ❌ Gemini fails → error message

**Expected behavior:**
1. ✅ Recognize this is a product slug/code
2. ✅ Map to `search_product` intent with higher confidence
3. ✅ Extract entity: `product_name = "ao-khoac-nam-lightweight-windbreaker-form-regular"`
4. ✅ Call search API successfully

---

## 📊 EVIDENCE

### **Logs:**
```
2025-12-09 10:14:08 INFO  actions.actions  
- Fallback triggered for message: tôi cần tìm ao-khoac-nam-lightweight-windbreaker-form-regular 
  (intent: search_product, confidence: 0.19749468564987183)
```

**Analysis:**
- Intent detection: `search_product` ✅ (correct)
- Confidence: **0.197** ❌ (only 19.7%)
- Reason: Training data không có examples với slug pattern

---

## 💥 ROOT CAUSE

### **Why Low Confidence?**

**Typical training examples:**
```yaml
# nlu.yml
- intent: search_product
  examples: |
    - tôi muốn tìm áo khoác
    - tìm cho tôi áo thun
    - có áo polo không
    - tìm giày thể thao
```

**Actual user input:**
```
- tôi cần tìm ao-khoac-nam-lightweight-windbreaker-form-regular
```

**Differences:**
1. Slug format: `kebab-case` với dấu gạch ngang
2. Rất dài và cụ thể
3. Chứa technical terms: "form-regular", "lightweight"
4. Pattern khác hẳn natural language

→ NLU model chưa học pattern này → confidence thấp

---

## 🛠️ HOW TO IMPROVE

### **Priority 1: Add Slug Pattern Training Data** (RECOMMENDED)

**File:** `data/nlu.yml`

**Add examples with slug patterns:**

```yaml
- intent: search_product
  examples: |
    # Existing natural examples
    - tôi muốn tìm áo khoác
    - tìm cho tôi áo thun đen
    - có áo polo không
    
    # ✅ ADD: Slug/code pattern examples
    - tôi cần tìm ao-khoac-nam-lightweight-windbreaker-form-regular
    - tìm giúp tôi ao-thun-nam-cotton-basic
    - cho tôi xem quan-jean-nam-slim-fit-den
    - tìm ao-polo-nam-pique-trang
    - có san-pham ao-so-mi-nam-tron-xanh không
    - tìm giay-the-thao-nam-running
    - cho xem ao-khoac-denim-nam-form-loose
    - tìm quan-short-nam-the-thao
    - tìm san-pham [slug]
    - cho tôi xem [slug]
    - tìm giúp tôi [slug]
```

**Entity annotation:**
```yaml
- intent: search_product
  examples: |
    - tôm cần tìm [ao-khoac-nam-lightweight-windbreaker-form-regular](product_name)
    - tìm giúp tôi [ao-thun-nam-cotton-basic](product_name)
    - cho tôi xem [quan-jean-nam-slim-fit-den](product_name)
```

---

### **Priority 2: Add Regex Pattern for Slugs** (OPTIONAL)

**File:** `data/nlu.yml`

**Add regex entity extractor:**

```yaml
- regex: product_slug
  examples: |
    - [a-z0-9]+(?:-[a-z0-9]+){2,}
```

**Explanation:**
- Matches: `ao-khoac-nam-lightweight-windbreaker`
- Pattern: lowercase letters/numbers separated by hyphens
- Minimum 3 segments (e.g., `ao-thun-nam`)

---

### **Priority 3: Add Synonym Mapping** (OPTIONAL)

**File:** `data/nlu.yml`

**Map slug patterns to natural language:**

```yaml
- synonym: áo khoác
  examples: |
    - ao-khoac
    - ao-khoac-nam
    - jacket
    
- synonym: áo thun
  examples: |
    - ao-thun
    - ao-thun-nam
    - t-shirt
    - tshirt
```

---

### **Priority 4: Train & Evaluate**

**After adding examples:**

```bash
# Retrain model
rasa train nlu

# Test with slug inputs
rasa shell nlu

# Expected results:
User: tôi cần tìm ao-khoac-nam-lightweight-windbreaker-form-regular
Intent: search_product
Confidence: >0.80 ✅ (improved from 0.20)
Entities: product_name = "ao-khoac-nam-lightweight-windbreaker-form-regular"
```

---

## ✅ BACKEND STATUS

**Backend API đã được improve** (fixed today):

```typescript
// Before
'(p.name ILIKE :search OR p.description ILIKE :search)'

// After - Now searches slugs too ✅
'(p.name ILIKE :search OR p.description ILIKE :search OR p.slug ILIKE :search)'
```

**Files updated:**
- ✅ `internal.service.ts` (chatbot API)
- ✅ `products.service.ts` (public API)

**Test:**
```bash
# Now works with slug
GET /api/internal/search-products?search=ao-khoac-nam-lightweight-windbreaker-form-regular

# Returns product successfully ✅
```

---

## 🧪 TESTING

### **Test Cases After Training:**

#### **Case 1: Slug Pattern**
```
Input: "tôi cần tìm ao-khoac-nam-lightweight-windbreaker-form-regular"

Expected:
- Intent: search_product
- Confidence: >0.80 (up from 0.20) ✅
- Entity: product_name = "ao-khoac-nam-lightweight-windbreaker-form-regular"
- Action: action_search_products ✅
- API Call: search=ao-khoac-nam-lightweight-windbreaker-form-regular ✅
- Result: Product found ✅
```

#### **Case 2: Short Slug**
```
Input: "tìm ao-polo-nam"

Expected:
- Intent: search_product
- Confidence: >0.90 ✅
- Entity: product_name = "ao-polo-nam"
- Result: Products found ✅
```

#### **Case 3: Natural Language (Should Still Work)**
```
Input: "tìm áo khoác màu đen"

Expected:
- Intent: search_product
- Confidence: >0.95 ✅
- Entity: product_name = "áo khoác màu đen"
- Result: Products found ✅
```

---

## 📊 EXPECTED IMPROVEMENTS

| Scenario | Before | After Training |
|----------|--------|----------------|
| Slug input | Confidence: 20% ❌<br>Fallback triggered | Confidence: 80%+ ✅<br>Direct search |
| Natural language | Confidence: 95%+ ✅ | Confidence: 95%+ ✅<br>(no regression) |
| Mixed input | Confidence: varies | Confidence: improved |

---

## 💡 WHY THIS MATTERS

### **User Behaviors:**

1. **Copy from URL**
   ```
   User sees: /products/ao-khoac-nam-lightweight-windbreaker-form-regular
   User pastes in chat: "ao-khoac-nam-lightweight-windbreaker-form-regular"
   Expected: Find that specific product ✅
   ```

2. **From Search History**
   ```
   Browser autocomplete suggests: ao-polo-nam-pique-trang
   User copies to chat
   Expected: Find products ✅
   ```

3. **From Product Code/SKU**
   ```
   Product code: BMM32410
   User: "tìm BMM32410"
   Expected: Find exact product ✅
   ```

---

## 📞 ACTION ITEMS

### **Chatbot Team:**

**Step 1: Update Training Data (30 min)**
- [ ] Add 20-30 slug pattern examples to `nlu.yml`
- [ ] Annotate entities for slug examples
- [ ] Add regex pattern for slug detection (optional)

**Step 2: Retrain Model (5 min)**
- [ ] Run `rasa train nlu`
- [ ] Verify no errors

**Step 3: Test (15 min)**
- [ ] Test with slug: `ao-khoac-nam-lightweight-windbreaker-form-regular`
- [ ] Verify confidence >0.80
- [ ] Test natural language still works
- [ ] Test search API returns products

**Step 4: Deploy (5 min)**
- [ ] Restart Rasa action server
- [ ] Verify chatbot recognizes slug patterns

**Total time:** ~1 hour

---

### **Backend Team:**
- [x] ✅ API search now supports slug (COMPLETED)
- [x] ✅ Both internal and public APIs updated

---

## 📝 NOTES

### **Alternative Approaches:**

#### **A. Slug Normalization (in action code)**
```python
# If slug detected, normalize before search
def normalize_slug(text):
    # Convert: "ao-khoac-nam" → "áo khoác nam"
    return text.replace('-', ' ')

# Use in action
product_name = tracker.get_slot("product_name")
if is_slug_format(product_name):
    # Search with both original and normalized
    search_query = f"{product_name} OR {normalize_slug(product_name)}"
```

#### **B. Direct Slug Lookup (faster)**
```python
# If input matches slug pattern exactly
if re.match(r'^[a-z0-9-]+$', product_name):
    # Direct lookup by slug first
    product = api.get_product_by_slug(product_name)
    if product:
        return [product]
    else:
        # Fallback to search
        return api.search_products(product_name)
```

---

## 🎯 SUCCESS CRITERIA

After implementation:
- ✅ Slug inputs have >80% intent confidence
- ✅ No fallback for valid product slugs
- ✅ Search API finds products by slug
- ✅ Natural language search still works
- ✅ Response time <3s

---

**Priority:** ⚠️ **MEDIUM** (Quality improvement, not blocking)  
**Impact:** Better UX for users who paste URLs/slugs  
**Timeline:** Can be done when convenient (low urgency)  
**Effort:** ~1 hour

---

**Improvement Request Created:** 2025-12-09 10:14  
**Reporter:** Backend Team  
**Type:** Training Data Enhancement
