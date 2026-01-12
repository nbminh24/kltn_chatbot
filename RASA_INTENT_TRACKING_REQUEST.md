# 🤖 [Backend Request] Rasa - Intent Tracking Integration

**To:** Team AI (Rasa)  
**From:** Backend Team  
**Date:** 2026-01-10  
**Priority:** HIGH

---

## 📋 Yêu Cầu

Backend cần **intent name** từ Rasa để phục vụ analytics dashboard. Hiện tại backend đã sẵn sàng nhận và lưu intent vào database.

---

## 🔧 Implementation Required

### Option 1: Thêm Intent vào `metadata` (Khuyến nghị)

Trong Rasa response, thêm intent vào `metadata` field:

```python
# actions.py hoặc custom action
def run(self, dispatcher, tracker, domain):
    # Get current intent
    intent_name = tracker.latest_message['intent'].get('name')
    
    # Send response với metadata
    dispatcher.utter_message(
        text="Your response here",
        metadata={"intent": intent_name}
    )
```

**Response format từ Rasa webhook:**
```json
{
  "text": "Here is your product information...",
  "metadata": {
    "intent": "product_inquiry"
  }
}
```

---

### Option 2: Thêm Intent vào `custom` field

```python
def run(self, dispatcher, tracker, domain):
    intent_name = tracker.latest_message['intent'].get('name')
    
    dispatcher.utter_message(
        text="Your response here",
        custom={
            "intent": intent_name,
            "other_data": "..."
        }
    )
```

**Response format:**
```json
{
  "text": "Here is your product information...",
  "custom": {
    "intent": "product_inquiry"
  }
}
```

---

## 🎯 Intent Names Cần Track

Các intents quan trọng cần track cho analytics:

- `product_inquiry` - Hỏi về sản phẩm
- `order_status` - Tra cứu đơn hàng
- `check_product_availability` - Kiểm tra tồn kho
- `ask_styling_advice` - Tư vấn phối đồ
- `ask_sizing_advice` - Tư vấn size
- `check_discount` - Hỏi về khuyến mãi
- `ask_shipping_info` - Thông tin vận chuyển
- `ask_return_policy` - Chính sách đổi trả
- `ask_product_comparison` - So sánh sản phẩm
- `request_human_agent` - Chuyển sang human support

**Lưu ý:** Tất cả intents đều cần track, kể cả những intent khác ngoài list trên.

---

## ✅ Backend Integration Status

Backend đã sẵn sàng:
- ✅ Database column `intent` đã được thêm vào `chat_messages` table
- ✅ Logic auto-extract intent từ `metadata.intent` hoặc `custom.intent`
- ✅ API `/admin/chatbot/top-intents` để hiển thị thống kê

**Code backend xử lý:**
```typescript
// Extract intent from Rasa metadata if available
const intent = rasaMsg.metadata?.intent || rasaMsg.custom?.intent || null;

// Save to database
const botMessage = {
  session_id: dto.session_id,
  sender: 'bot',
  message: rasaMsg.text || '',
  intent: intent, // ✅ Auto-saved to DB
};
```

---

## 🧪 Testing

Sau khi implement, test bằng cách:

1. Gửi message đến Rasa webhook:
```bash
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user",
    "message": "Tôi muốn xem áo sơ mi"
  }'
```

2. Kiểm tra response có chứa intent:
```json
[
  {
    "text": "Đây là các áo sơ mi...",
    "metadata": {"intent": "product_inquiry"}  // ✅ Check this
  }
]
```

3. Gọi API `/admin/chatbot/top-intents` để verify intent đã được lưu

---

## 📞 Contact

Nếu có vấn đề khi implement, liên hệ Backend Team.

**Expected completion:** ASAP (cần cho dashboard analytics)
