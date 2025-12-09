# 🧪 PHASE 1 - TESTING GUIDE

**Status:** ✅ Code Complete - Ready for Testing  
**Date:** December 9, 2025  
**Phase:** Hybrid Architecture Implementation

---

## 📋 PRE-TESTING CHECKLIST

### **1. Install Dependencies**
```bash
# Install Gemini package
pip install google-generativeai

# Verify installation
pip list | grep google-generativeai
```

### **2. Verify Environment Variables**
Check `.env` file contains:
```env
GEMINI_API_KEY=AIzaSyDpca8OMZ6rH2bfoGW-yAji66x2qZyEnGQ
GEMINI_MODEL=gemini-1.5-flash
BACKEND_URL=http://localhost:3001
```

### **3. Train Rasa Model**
```bash
rasa train

# Expected output:
# - Model trained successfully
# - Possible warnings about story conflicts (normal)
# - Model saved to ./models/
```

---

## 🧪 TEST CASES

### **Test Case 1: Repeated Product Search** ✅ Critical
**Purpose:** Verify Story Conflict fix

```
You: search for jacket
Bot: [Shows products]

You: search for jacket
Bot: [Shows products] ✅ Should work without crash

You: find me a shirt
Bot: [Shows products] ✅ Should work

You: search for pants
Bot: [Shows products] ✅ Should work
```

**Expected:** No crash, no "I don't understand"

---

### **Test Case 2: Gemini Fallback** ✅ Critical
**Purpose:** Verify FallbackClassifier triggers Gemini

```
You: what's the weather today?
Bot: [Gemini response about weather] ✅

You: tell me a joke
Bot: [Gemini tells a joke] ✅

You: who is the president?
Bot: [Gemini answers] ✅
```

**Expected:** Gemini responds naturally, not "I don't understand"

---

### **Test Case 3: Open-Ended Fashion Queries** ✅ High Priority
**Purpose:** Verify open_ended_query intent works

```
You: what colors go well with navy blue?
Bot: [Gemini gives fashion advice] ✅

You: how should I dress for a job interview?
Bot: [Gemini gives outfit advice] ✅

You: what's trending in fashion?
Bot: [Gemini responds] ✅
```

**Expected:** Helpful fashion advice from Gemini

---

### **Test Case 4: Order Tracking** ✅ Medium Priority
**Purpose:** Verify track_order rule works repeatedly

```
You: track order 123
Bot: [Shows order status] ✅

You: check order 456
Bot: [Shows order status] ✅

You: track my order
Bot: [Asks for order number or shows status] ✅
```

**Expected:** Works multiple times without crash

---

### **Test Case 5: Mixed Conversation** ✅ High Priority
**Purpose:** Verify bot handles context switching

```
You: search for jacket
Bot: [Shows products]

You: what's the weather?
Bot: [Gemini responds]

You: search for shoes
Bot: [Shows products] ✅ Should switch back to search

You: tell me about sustainable fashion
Bot: [Gemini responds]

You: track order 123
Bot: [Shows order status] ✅
```

**Expected:** Smooth context switching, no confusion

---

## 🐛 DEBUGGING COMMANDS

### **Check NLU Confidence**
```bash
rasa shell --debug

# Watch for:
# - Intent prediction confidence
# - When nlu_fallback triggers
# - FallbackClassifier threshold (0.7)
```

### **Check Action Server Logs**
```bash
rasa run actions --debug

# Watch for:
# - Gemini client initialization
# - API calls to backend
# - Error messages
```

### **Test Specific Intent**
```bash
rasa shell nlu

# Type message and see:
# - Intent classification
# - Entity extraction
# - Confidence score
```

---

## ❌ COMMON ISSUES & SOLUTIONS

### **Issue 1: "google-generativeai not found"**
```bash
pip install google-generativeai
```

### **Issue 2: "Gemini API key invalid"**
Check `.env` file has correct key:
```env
GEMINI_API_KEY=AIzaSyDpca8OMZ6rH2bfoGW-yAji66x2qZyEnGQ
```

### **Issue 3: "Model not found"**
```bash
rasa train
# Then restart action server
```

### **Issue 4: "Bot still crashes on repeat search"**
Check `data/rules.yml` has:
```yaml
- rule: Always search products
  steps:
  - intent: search_product
  - action: action_search_products
```

### **Issue 5: "Gemini not responding"**
Check action server logs for:
- "✅ Gemini initialized successfully"
- If "❌ Failed to initialize", check API key

---

## 📊 SUCCESS METRICS

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Repeated search works | 100% | Test Case 1 |
| Fallback triggers Gemini | >80% | Test Case 2 |
| Open-ended queries work | >80% | Test Case 3 |
| No NoneType errors | 0 | Check logs |
| Response time | <3s | Use --debug mode |

---

## ✅ PHASE 1 ACCEPTANCE CRITERIA

- [ ] All 5 test cases pass
- [ ] No crashes during 10-minute conversation
- [ ] Gemini responds to at least 3/5 random questions
- [ ] Backend API calls work (product search, order tracking)
- [ ] No errors in action server logs
- [ ] Model trains without critical errors

---

## 🚀 NEXT STEPS AFTER PHASE 1

Once all tests pass:
1. Document any issues found
2. Proceed to **Phase 3: Transaction Flow (Cart Forms)**
3. Keep monitoring logs for edge cases

---

**Prepared by:** AI Assistant (Cascade)  
**Testing Duration:** ~30 minutes  
**Required Tools:** rasa shell, rasa run actions, browser/postman (for API testing)
