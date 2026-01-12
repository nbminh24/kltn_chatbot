# BUG REPORT: Gemini Log Endpoint 404

**Ngày phát hiện:** 06/01/2026  
**Severity:** Low (không ảnh hưởng chức năng chính)  
**Status:** Pending Fix  

---

## 1. MÔ TẢ LỖI

Chatbot gọi API để log Gemini calls nhưng endpoint không tồn tại.

**Error Log:**
```
2026-01-06 17:47:35 INFO     actions.api_client  - 📤 POST http://localhost:3001/api/chatbot/gemini/log
2026-01-06 17:47:35 INFO     actions.api_client  - 📥 Response status: 404
2026-01-06 17:47:35 ERROR    actions.api_client  - ❌ HTTP Error: 404
2026-01-06 17:47:35 ERROR    actions.api_client  - ❌ Response body: {"message":"Cannot POST /api/chatbot/gemini/log","error":"Not Found","statusCode":404}
```

---

## 2. NGUYÊN NHÂN

Chatbot đang gọi endpoint: `POST /api/chatbot/gemini/log`  
Backend chưa implement endpoint này.

**Chatbot Code:**
```python
# @actions/api_client.py
def log_gemini_call(
    self,
    user_message: str,
    rasa_intent: str,
    rasa_confidence: float,
    gemini_response: str,
    response_time_ms: int,
    is_validated: bool,
    auth_token: str = None
):
    """
    Log Gemini AI calls for analytics and monitoring
    """
    # ... calls POST /api/chatbot/gemini/log
```

---

## 3. TÁC ĐỘNG

**Không ảnh hưởng user experience:**
- Chatbot vẫn hoạt động bình thường
- Gemini AI vẫn trả lời được
- Chỉ mất log data

**Ảnh hưởng monitoring:**
- ❌ Không track được Gemini usage
- ❌ Không phân tích được intent confidence
- ❌ Không đo được response time
- ❌ Không biết Gemini validate thành công hay không

---

## 4. ĐỀ XUẤT GIẢI PHÁP

### **Option 1: Backend implement endpoint (Recommended)**

**Ưu điểm:**
- Có đầy đủ analytics data
- Giúp monitor Gemini performance
- Debug dễ hơn khi có vấn đề

**Backend cần làm:**

#### 4.1. Tạo endpoint
```typescript
// POST /api/chatbot/gemini/log
@Post('gemini/log')
@UseGuards(InternalApiKeyGuard)
async logGeminiCall(@Body() logData: GeminiLogDto) {
  // Store log vào database hoặc log service
  return { success: true };
}
```

#### 4.2. DTO
```typescript
class GeminiLogDto {
  user_message: string;
  rasa_intent: string;
  rasa_confidence: number;
  gemini_response: string;
  response_time_ms: number;
  is_validated: boolean;
  customer_id?: number;  // Optional
  timestamp?: Date;      // Auto-generated
}
```

#### 4.3. Database Schema (Optional)
Nếu muốn lưu vào DB để phân tích sau:

```sql
CREATE TABLE gemini_logs (
  id SERIAL PRIMARY KEY,
  user_message TEXT,
  rasa_intent VARCHAR(100),
  rasa_confidence DECIMAL(3,2),
  gemini_response TEXT,
  response_time_ms INTEGER,
  is_validated BOOLEAN,
  customer_id INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Index for analytics
CREATE INDEX idx_gemini_logs_created_at ON gemini_logs(created_at);
CREATE INDEX idx_gemini_logs_intent ON gemini_logs(rasa_intent);
```

---

### **Option 2: Chatbot bỏ logging (Quick Fix)**

**Ưu điểm:**
- Fix nhanh, không cần backend
- Bỏ error logs

**Nhược điểm:**
- Mất dữ liệu analytics
- Khó debug vấn đề Gemini

**Chatbot cần làm:**

#### 2.1. Wrap log call trong try-except
```python
# @actions/api_client.py:324-330
try:
    api_client.log_gemini_call(...)
except Exception as e:
    logger.warning(f"⚠️ Failed to log Gemini call: {e}")
    # Continue without breaking
```

#### 2.2. Hoặc make logging optional
```python
# Add config flag
ENABLE_GEMINI_LOGGING = os.getenv("ENABLE_GEMINI_LOGGING", "false").lower() == "true"

if ENABLE_GEMINI_LOGGING:
    try:
        api_client.log_gemini_call(...)
    except:
        pass
```

---

### **Option 3: Chatbot log locally (Alternative)**

**Ưu điểm:**
- Vẫn có logs để debug
- Không phụ thuộc backend

**Nhược điểm:**
- Log file có thể lớn
- Khó tổng hợp phân tích

**Implementation:**
```python
import json
from datetime import datetime

def log_gemini_call_locally(self, **kwargs):
    """Log to local file instead of API"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    with open("logs/gemini_calls.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

---

## 5. KHUYẾN NGHỊ

**Khuyến nghị: Option 1 (Backend implement)**

### Lý do:
1. **Analytics**: Cần data để biết Gemini đang hoạt động tốt hay không
2. **Monitoring**: Track response time, validation rate
3. **Debugging**: Khi user report lỗi, có thể review Gemini responses
4. **Cost tracking**: Biết Gemini được gọi bao nhiêu lần (nếu có billing)

### Timeline:
- **Estimate:** 30-60 phút development
- **Priority:** Low (không urgent)
- **Can wait:** Có, không block user

---

## 6. QUICK FIX TẠM THỜI

Trong khi chờ backend implement, chatbot có thể:

```python
# @actions/api_client.py - Modify log_gemini_call
def log_gemini_call(self, ...):
    try:
        # ... existing code ...
        return self._make_request("POST", "/api/chatbot/gemini/log", data=data)
    except Exception as e:
        # Fail silently - don't break the flow
        logger.debug(f"⚠️ Gemini log skipped: {e}")
        return {"success": False, "error": str(e)}
```

---

## 7. TEST AFTER FIX

### Backend Test:
```bash
# Test endpoint exists
curl -X POST http://localhost:3001/api/chatbot/gemini/log \
  -H "X-Internal-Api-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "test",
    "rasa_intent": "nlu_fallback",
    "rasa_confidence": 0.5,
    "gemini_response": "test response",
    "response_time_ms": 1000,
    "is_validated": true
  }'

# Expected: 200/201 status
```

### Chatbot Test:
1. Trigger Gemini fallback: "thời tiết hôm nay thế nào"
2. Check logs: Không có error 404
3. Verify: Gemini vẫn trả lời được

---

## 8. LIÊN HỆ

**Team Backend:** Implement endpoint nếu chọn Option 1  
**Team Chatbot:** Có thể apply quick fix Option 2 tạm thời  

---

**END OF DOCUMENT**
