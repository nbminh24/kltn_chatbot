# 🐛 CRITICAL BUG - Rasa Server Not Integrated with Backend

**Date:** December 7, 2025  
**Reporter:** Frontend Team  
**Severity:** CRITICAL (Blocking AI chatbot feature)  
**Status:** OPEN  
**Assigned to:** Backend Team + AI/Rasa Team

---

## 📋 SUMMARY

Backend API `POST /chat/send` đang trả về hardcoded responses thay vì gọi Rasa server để xử lý NLU và trả lời thông minh.

---

## 🔴 ISSUE

### **Evidence:**

**User Input:**
```
"are you bot?"
```

**Backend Response:**
```json
{
  "bot_messages": [
    {
      "message": "I'm an AI shopping assistant here to help you find products, track orders, and answer your questions!"
    }
  ]
}
```

### **Problem:**
- ✅ Backend API hoạt động
- ✅ Message được lưu database
- ❌ **KHÔNG GỌI RASA SERVER**
- ❌ Response là hardcoded text
- ❌ Không có NLU processing
- ❌ Không có intent detection
- ❌ Không có slot filling
- ❌ Không có custom actions

---

## 💥 IMPACT

### **Blocked Features:**
1. ❌ Product search by natural language
2. ❌ Size consultation
3. ❌ Order tracking
4. ❌ Slot filling (size/color selection)
5. ❌ Product recommendations
6. ❌ All 29 intents
7. ❌ Gemini AI fallback

### **Current State:**
- Backend: ✅ Working (but not calling Rasa)
- Rasa: ❓ Unknown status (may be working but not called)
- Frontend: ✅ Ready to receive Rasa responses

---

## ✅ EXPECTED BEHAVIOR

### **Flow Should Be:**

```
User sends message
  ↓
Frontend → POST /chat/send → Backend
  ↓
Backend → Rasa webhook → Rasa Server
  ↓
Rasa processes:
  - NLU (intent + entities)
  - Dialog management
  - Custom actions (if needed)
  - Calls backend Internal APIs
  ↓
Rasa → Response → Backend
  ↓
Backend → Response → Frontend
```

### **Expected Rasa Integration:**

**Backend should call:**
```bash
POST {RASA_URL}/webhooks/rest/webhook
Content-Type: application/json

{
  "sender": "session_21",  # or customer_id
  "message": "are you bot?"
}
```

**Rasa should return:**
```json
[
  {
    "recipient_id": "session_21",
    "text": "Vâng, mình là chatbot hỗ trợ mua sắm! Mình có thể giúp bạn tìm sản phẩm, tư vấn size, và tra cứu đơn hàng. Bạn cần gì không?",
    "custom": null
  }
]
```

---

## 🔍 ROOT CAUSE ANALYSIS

### **Possible Issues:**

#### **Option A: Rasa Integration Not Implemented**
```typescript
// Backend currently doing:
async sendMessage(message: string) {
  // Save to database ✅
  const savedMessage = await this.saveMessage(message);
  
  // Return hardcoded response ❌
  return {
    user_message: savedMessage,
    bot_messages: [{
      message: "I'm an AI shopping assistant..." // HARDCODED
    }]
  };
}
```

**Should be:**
```typescript
async sendMessage(message: string) {
  // Save to database ✅
  const savedMessage = await this.saveMessage(message);
  
  // Call Rasa ✅
  const rasaResponse = await this.callRasaWebhook(message);
  
  // Process Rasa response ✅
  const botMessages = await this.processRasaResponse(rasaResponse);
  
  return {
    customer_message: savedMessage,
    bot_responses: botMessages
  };
}
```

#### **Option B: Rasa Server Not Running**
- Check if Rasa is running on configured port
- Default: `http://localhost:5005`

#### **Option C: Configuration Missing**
- `RASA_URL` not set in `.env`
- Network connection issue between backend and Rasa

---

## 🛠️ HOW TO FIX

### **Step 1: Verify Rasa Server Status**

```bash
# Check if Rasa is running
curl http://localhost:5005/webhooks/rest/webhook \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test",
    "message": "hello"
  }'
```

**Expected:** Rasa returns response  
**If fails:** Start Rasa server

### **Step 2: Backend Integration**

**File:** `src/chat/chat.service.ts`

**Add Rasa Client:**
```typescript
import axios from 'axios';

private readonly rasaUrl = process.env.RASA_URL || 'http://localhost:5005';

async callRasaWebhook(message: string, senderId: string) {
  try {
    const response = await axios.post(
      `${this.rasaUrl}/webhooks/rest/webhook`,
      {
        sender: senderId,
        message: message
      },
      {
        timeout: 10000 // 10 seconds
      }
    );
    
    return response.data; // Array of Rasa responses
  } catch (error) {
    console.error('[Rasa] Failed to call webhook:', error);
    
    // Fallback: Call Gemini AI
    return await this.callGeminiFallback(message);
  }
}
```

**Update sendMessage:**
```typescript
async sendMessage(dto: SendMessageDto) {
  // 1. Save user message
  const userMessage = await this.messagesRepository.save({
    session_id: dto.session_id,
    sender: 'customer',
    message: dto.message,
  });
  
  // 2. Call Rasa
  const rasaResponses = await this.callRasaWebhook(
    dto.message,
    `session_${dto.session_id}`
  );
  
  // 3. Save bot responses
  const botMessages = [];
  for (const rasaMsg of rasaResponses) {
    const saved = await this.messagesRepository.save({
      session_id: dto.session_id,
      sender: 'bot',
      message: rasaMsg.text,
      custom: rasaMsg.custom || null,
    });
    botMessages.push(saved);
  }
  
  // 4. Return
  return {
    customer_message: userMessage,
    bot_responses: botMessages,
  };
}
```

### **Step 3: Environment Configuration**

**File:** `.env`
```env
RASA_URL=http://localhost:5005
RASA_TIMEOUT=10000
GEMINI_API_KEY=your_gemini_key  # For fallback
```

---

## 🧪 TESTING

### **Test Case 1: Basic Greeting**
```
Input: "Chào shop"
Expected: Rasa greet intent response
Actual: ❌ Hardcoded message
```

### **Test Case 2: Product Search**
```
Input: "Tìm áo thun đen"
Expected: Rasa product_search_text intent + product list with custom data
Actual: ❌ Hardcoded message
```

### **Test Case 3: Size Consultation**
```
Input: "Mình cao 1m7, 65kg nên mặc size gì?"
Expected: Rasa size_get_advice intent + size recommendation
Actual: ❌ Hardcoded message
```

---

## 📊 RELATED DOCUMENTATION

- `chatbot/03_DATA_FLOW.md` - Integration flow
- `chatbot/IMPLEMENTATION_SUMMARY.md` - Rasa completion status
- `README copy.md` - Internal APIs for Rasa

---

## 🎯 PRIORITY

**CRITICAL** - This blocks entire chatbot AI functionality

**Timeline:** URGENT - Need fix ASAP

**Dependencies:**
- Rasa server must be running
- Backend must implement Rasa webhook call
- Internal APIs must be accessible from Rasa

---

## 📞 ACTION ITEMS

### **Backend Team:**
- [ ] Implement Rasa webhook integration
- [ ] Add error handling & fallback (Gemini)
- [ ] Update `.env` configuration
- [ ] Test with running Rasa server

### **AI/Rasa Team:**
- [ ] Confirm Rasa server is running
- [ ] Verify all 29 intents are trained
- [ ] Test webhook endpoint
- [ ] Provide test cases

### **Frontend Team:**
- [x] Ready to receive Rasa responses
- [x] Support `custom` data rendering
- [x] Handle all 7 message types

---

## 📝 NOTES

**Current Workaround:**
Frontend shows hardcoded bot response. User experience is basic text chat without AI intelligence.

**After Fix:**
Full intelligent chatbot with:
- Natural language understanding
- Product recommendations
- Size consultation
- Order tracking
- Slot filling for cart
- And all 29 intents

---

**Bug Report v1.0**  
**Created:** 2024-12-07 17:40  
**Status:** CRITICAL - BLOCKING
