# Bug Report: 401 Unauthorized - API Header Name Mismatch

**Date:** 12/12/2024  
**Severity:** 🔴 HIGH - BLOCKER  
**Component:** Backend API  
**Status:** 🔴 BROKEN

---

## 📋 Summary

Backend API returns 401 Unauthorized when chatbot calls add to cart endpoint. Root cause: **Header name mismatch** between backend implementation and documentation.

**Error:**
```
HTTP Error: 401 - {"message":"Invalid or missing internal API key","error":"Unauthorized","statusCode":401}
```

---

## 🐛 Root Cause

### Backend Implementation vs Documentation

**Documentation says:** (BACKEND_API_IMPLEMENTATION_SUMMARY.md, CUSTOMER_ID_INJECTION_GUIDE.md)
```python
headers = {"X-Internal-Api-Key": self.api_key}
```

**Chatbot was using:**
```python
headers = {"x-api-key": self.api_key}
```

**Backend expects:** ❓ (UNCLEAR - needs verification)
- Option A: `X-Internal-Api-Key` (as documented)
- Option B: `x-api-key` (lowercase)
- Option C: Something else entirely?

---

## 🔍 Evidence

### Chatbot Logs
```
2025-12-12 11:42:32 INFO  📤 Calling backend add_to_cart: customer_id=21, variant_id=14, qty=1
2025-12-12 11:42:32 INFO  Adding to cart: customer=21, variant=14, qty=1
2025-12-12 11:42:32 ERROR HTTP Error: 401 - {"message":"Invalid or missing internal API key","error":"Unauthorized","statusCode":401}
```

### API Call Details
```
POST http://localhost:3001/api/chatbot/cart/add
Headers:
  x-api-key: <value_from_env>  ❌ REJECTED by backend
  Content-Type: application/json

Body:
{
  "customer_id": 21,
  "variant_id": 14,
  "quantity": 1
}

Response: 401 Unauthorized
```

---

## 🛠️ Backend Team: Please Verify

### Question 1: What header name does backend ACTUALLY accept?

Check your code in:
- `src/modules/chatbot/guards/internal-api-key.guard.ts` (or similar)
- `src/common/guards/api-key.guard.ts`
- Any middleware that validates API key

**Expected header name:** ?

### Question 2: Is header name case-sensitive?

- `X-Internal-Api-Key` (PascalCase with hyphens)
- `x-internal-api-key` (lowercase)
- `x-api-key` (short form)

Which one is correct?

### Question 3: Update documentation

All documentation currently says `X-Internal-Api-Key`:
- `BACKEND_API_IMPLEMENTATION_SUMMARY.md` line 68, 256
- `CUSTOMER_ID_INJECTION_GUIDE.md`
- Any API documentation

If backend uses different name, **please update all docs**.

---

## ✅ Temporary Fix (Chatbot Side)

Chatbot code updated to use `X-Internal-Api-Key` as per documentation:

**File:** `actions/api_client.py`
```python
self.headers = {
    "X-Internal-Api-Key": self.api_key,  # Changed from x-api-key
    "Content-Type": "application/json"
}
```

---

## 🧪 Test Request

**Backend team, please test with:**

```bash
curl -X POST http://localhost:3001/api/chatbot/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Internal-Api-Key: your_test_key_here" \
  -d '{
    "customer_id": 21,
    "variant_id": 14,
    "quantity": 1
  }'
```

**Expected:** 200 OK or 201 Created  
**Current:** 401 Unauthorized

Also test with lowercase:
```bash
curl -X POST http://localhost:3001/api/chatbot/cart/add \
  -H "x-api-key: your_test_key_here" \
  ...
```

Which one works?

---

## 📊 Impact

- **Severity:** HIGH - Blocks ALL chatbot API calls
- **Affected Endpoints:**
  - `POST /api/chatbot/cart/add` ❌
  - `GET /api/chatbot/cart/:customer_id` ❌
  - `POST /api/chatbot/auth/verify` ❌
  - All `/api/chatbot/*` endpoints ❌

**Status:** Chatbot cannot add to cart, view cart, or use ANY authenticated features.

---

## 🚀 Action Items

### For Backend Team:
1. ⚠️ **URGENT:** Check what header name backend actually validates
2. ⚠️ Confirm: Is it `X-Internal-Api-Key` or `x-api-key` or something else?
3. ⚠️ Test endpoint with curl using both header names
4. ⚠️ Update documentation if header name is different
5. ⚠️ Standardize header name across all `/api/chatbot/*` endpoints

### For Chatbot Team:
- [x] Updated code to use `X-Internal-Api-Key` ✅
- [ ] Wait for backend verification
- [ ] Test after backend confirms correct header name
- [ ] Update `.env.example` if needed

---

## 🔗 Related Files

- `actions/api_client.py` - Chatbot API client (UPDATED)
- `BACKEND_API_IMPLEMENTATION_SUMMARY.md` - Documentation
- `CUSTOMER_ID_INJECTION_GUIDE.md` - Documentation

---

## 📝 Environment Check

**Please also verify:**

1. **Is `INTERNAL_API_KEY` set in backend .env?**
   ```bash
   # backend/.env
   INTERNAL_API_KEY=your_secret_key_here
   ```

2. **Is the key value correct?**
   - Chatbot uses: `os.getenv("INTERNAL_API_KEY", "")`
   - Backend validates against: ?

3. **Key comparison:**
   - Is backend doing exact string match?
   - Is key hashed/encrypted?

---

**Status:** 🔴 BLOCKING - Cannot proceed without backend fix/clarification  
**Priority:** P0 - CRITICAL  
**ETA:** Need response from backend team within 24 hours
