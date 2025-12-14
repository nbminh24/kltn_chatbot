# Customer ID Injection Guide for Chatbot Integration

## Problem
Chatbot cần `customer_id` để thực hiện các thao tác như add to cart, view cart, track orders. Hiện tại slot `customer_id` luôn = `None` trong tracker.

## Solutions

### ✅ Option A: Frontend gửi customer_id qua metadata (RECOMMENDED - EASIEST)

**Implementation:**
Frontend gửi customer_id trong metadata của mỗi message khi user đã đăng nhập:

```javascript
// Frontend code (React/Vue/Angular)
const sendChatMessage = (message) => {
  const userData = getUserFromLocalStorage(); // hoặc Redux/Vuex store
  
  rasa.sendMessage({
    text: message,
    metadata: {
      customer_id: userData?.id || null,
      user_jwt_token: userData?.token || null
    }
  });
};
```

**Chatbot sẽ extract:**
```python
# File: actions/actions.py
customer_id = tracker.latest_message.get("metadata", {}).get("customer_id")

if not customer_id:
    dispatcher.utter_message(text="Vui lòng đăng nhập để thực hiện thao tác này.")
    return []
```

**Pros:**
- Đơn giản nhất
- Không cần thay đổi backend
- Frontend đã có thông tin user

**Cons:**
- Frontend phải gửi customer_id trong mọi message
- Cần validate customer_id mỗi lần chatbot gọi API

---

### Option B: Chatbot gọi API verify JWT token

**Backend endpoint cần tạo:**
```typescript
// File: chatbot.controller.ts
@Post('auth/verify')
@ApiOperation({
    summary: '[Internal] Verify JWT token',
    description: 'Verify JWT token and return customer information',
})
async verifyToken(@Body() dto: { jwt_token: string }) {
    const result = await this.chatbotService.verifyToken(dto.jwt_token);
    
    return {
        success: true,
        data: {
            customer_id: result.customerId,
            email: result.email,
            name: result.name
        }
    };
}
```

**Chatbot implementation:**
```python
# File: actions/api_client.py
def verify_jwt_token(self, jwt_token: str) -> dict:
    response = requests.post(
        f"{self.base_url}/api/chatbot/auth/verify",
        headers={"X-Internal-Api-Key": self.api_key},
        json={"jwt_token": jwt_token}
    )
    return response.json()

# File: actions/actions.py
jwt_token = tracker.latest_message.get("metadata", {}).get("user_jwt_token")
if jwt_token:
    user_data = api_client.verify_jwt_token(jwt_token)
    customer_id = user_data["data"]["customer_id"]
```

**Pros:**
- Bảo mật hơn Option A
- Backend verify token đảm bảo tính hợp lệ

**Cons:**
- Cần thêm 1 API endpoint mới
- Chatbot phải gọi thêm 1 API request để verify token

---

### ⭐ Option C: Backend middleware tự động inject customer_id (BEST - MOST SECURE)

**Backend middleware:**
```typescript
// File: src/common/middleware/chatbot-auth.middleware.ts
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { JwtService } from '@nestjs/jwt';

@Injectable()
export class ChatbotAuthMiddleware implements NestMiddleware {
  constructor(private jwtService: JwtService) {}

  use(req: Request, res: Response, next: NextFunction) {
    // Extract JWT from Rasa webhook request
    const authHeader = req.headers.authorization;
    
    if (authHeader && authHeader.startsWith('Bearer ')) {
      try {
        const token = authHeader.substring(7);
        const decoded = this.jwtService.verify(token);
        
        // Inject customer_id vào request body metadata
        if (req.body && req.body.metadata) {
          req.body.metadata.customer_id = decoded.sub;
          req.body.metadata.customer_email = decoded.email;
        }
      } catch (error) {
        // Token invalid, skip injection
      }
    }
    
    next();
  }
}
```

**Apply middleware:**
```typescript
// File: src/app.module.ts hoặc main.ts
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(ChatbotAuthMiddleware)
      .forRoutes('webhooks/rasa'); // Rasa webhook endpoint
  }
}
```

**Pros:**
- Transparent cho chatbot
- Bảo mật cao nhất
- Tự động inject customer_id vào mọi message

**Cons:**
- Phức tạp nhất
- Cần config Rasa webhook endpoint

---

## Recommended Implementation

**Phase 1: Use Option A (Quick Win)**
- Frontend team implement gửi customer_id trong metadata
- Chatbot extract customer_id từ metadata
- Test với các API đã có

**Phase 2: Upgrade to Option C (Long-term)**
- Backend implement middleware
- Test thoroughly
- Deploy to production

---

## Testing

### Test Case: User chưa đăng nhập
```
User: "Thêm vào giỏ hàng"
Expected: Bot nhắc "Vui lòng đăng nhập để tiếp tục"
```

### Test Case: User đã đăng nhập
```
User logged in (customer_id = 123)
User: "Thêm áo size M vào giỏ"
Expected: Bot gọi API với customer_id = 123 và add to cart thành công
```

### Test Case: Token expired
```
User token hết hạn
Expected: Bot nhắc "Phiên đăng nhập hết hạn, vui lòng đăng nhập lại"
```

---

## Security Notes

1. **Validate customer_id:** Backend luôn validate customer_id tồn tại trong database trước khi thực hiện thao tác
2. **Rate limiting:** Implement rate limiting cho chatbot endpoints
3. **Logging:** Log tất cả chatbot API calls với customer_id để audit
4. **API Key rotation:** Định kỳ rotate `X-Internal-Api-Key`

---

## Contact
Nếu cần hỗ trợ implement, liên hệ Backend Team Lead.
