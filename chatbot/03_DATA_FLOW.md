# 🔄 LUỒNG DỮ LIỆU - CHATBOT E-COMMERCE

## 1. KIẾN TRÚC TỔNG QUAN

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                    (Next.js Frontend - Vercel)                   │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │ Chat Widget │  │ Product Page │  │ Checkout    │            │
│  └─────────────┘  └──────────────┘  └─────────────┘            │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTPS (REST API)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND API SERVER                            │
│              (NestJS - Railway/Render)                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Chat Module  │  │ Product API  │  │ Order API    │          │
│  │ (Proxy)      │  │              │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         │                  │                  ▼                  │
│         │                  │         ┌──────────────┐           │
│         │                  └────────►│  PostgreSQL  │           │
│         │                            │   Database   │           │
│         │                            └──────────────┘           │
│         │ Forward message                                       │
│         ▼                                                        │
│  ┌────────────────┐                                             │
│  │ Rasa Webhook   │◄──────────────┐                             │
│  │ Handler        │               │                             │
│  └────────────────┘               │                             │
└────────────┬───────────────────────┼──────────────────────────┘
             │ HTTP POST             │ HTTP (Action Server)
             ▼                       │
┌──────────────────────────────────┐ │
│      RASA SERVER (Python)        │ │
│                                  │ │
│  ┌────────────┐  ┌─────────────┐│ │
│  │ NLU Engine │  │   Policies  ││ │
│  │ (DIET)     │  │  (TED)      ││ │
│  └──────┬─────┘  └──────┬──────┘│ │
│         │                │       │ │
│         ▼                ▼       │ │
│  ┌─────────────────────────────┐│ │
│  │   Dialog Management         ││ │
│  │   (Slot Filling, Context)   ││ │
│  └──────────┬──────────────────┘│ │
│             │                    │ │
│             ▼                    │ │
│  ┌─────────────────────────────┐│ │
│  │    Custom Actions           ││─┘
│  │  (Python SDK)               ││
│  │                             ││
│  │  - action_search_products   ││──┐
│  │  - action_check_stock       ││  │
│  │  - action_add_to_cart       ││  │
│  │  - action_create_ticket     ││  │
│  └─────────────────────────────┘│  │
└──────────────────────────────────┘  │
                                      │
        ┌─────────────────────────────┘
        │ Call Backend APIs
        └──► /api/chatbot/products/search
        └──► /api/chatbot/products/:id/stock
        └──► /api/chatbot/cart/add
        └──► /api/chatbot/support-tickets
```

---

## 2. LUỒNG CHI TIẾT: GỬI TIN NHẮN

### 2.1. User gửi message "Tìm áo thun đen"

```
┌─────────┐
│  USER   │ Nhập: "Tìm áo thun đen"
└────┬────┘
     │
     │ 1. POST /chat/send
     │    Body: {
     │      session_id: 123,
     │      message: "Tìm áo thun đen"
     │    }
     ▼
┌─────────────────────┐
│  BACKEND (NestJS)   │
│                     │
│  ChatController     │
│  ├─ Validate input  │
│  ├─ Lưu user msg    │──► INSERT INTO chat_messages
│  │   vào DB         │    (session_id, sender='customer', message)
│  │                  │
│  ├─ Forward to Rasa │
│  │                  │
│  └─ POST {RASA_URL}/webhooks/rest/webhook
│       Body: {
│         sender: "session_123",
│         message: "Tìm áo thun đen"
│       }
└────┬────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│         RASA SERVER                 │
│                                     │
│  1. NLU Processing                  │
│     ├─ Intent: product_search_text  │
│     ├─ Entities:                    │
│     │   - category: "áo thun"       │
│     │   - color: "đen"              │
│     └─ Confidence: 0.95             │
│                                     │
│  2. Dialog Management               │
│     ├─ Check slots                  │
│     │   ✓ category: filled          │
│     │   ✓ color: filled             │
│     └─ Decision: Execute action     │
│                                     │
│  3. Action: action_search_products  │
│     ├─ Extract entities             │
│     └─ Call Backend API             │
└────┬────────────────────────────────┘
     │
     │ GET /api/chatbot/products/search?
     │     category=áo%20thun&color=đen
     ▼
┌─────────────────────┐
│  BACKEND API        │
│                     │
│  ProductService     │
│  ├─ Parse query     │
│  ├─ Query DB:       │
│  │   SELECT *      │
│  │   FROM products │──► PostgreSQL
│  │   JOIN variants │
│  │   WHERE ...     │
│  └─ Return JSON     │
│      {              │
│        products: [  │
│          {id, name, │
│           price...} │
│        ]            │
│      }              │
└────┬────────────────┘
     │
     │ Response: {products: [...]}
     ▼
┌─────────────────────────────────────┐
│         RASA SERVER                 │
│                                     │
│  4. Generate Response               │
│     ├─ Format product cards         │
│     └─ Create response array:       │
│         [                           │
│           {                         │
│             "text": "Mình tìm...", │
│             "custom": {             │
│               "type": "products",   │
│               "data": [...]         │
│             }                       │
│           }                         │
│         ]                           │
│                                     │
│  5. Return to Backend               │
└────┬────────────────────────────────┘
     │
     │ Response: [{text, custom}]
     ▼
┌─────────────────────┐
│  BACKEND (NestJS)   │
│                     │
│  ChatService        │
│  ├─ Parse response  │
│  ├─ Save bot msgs   │──► INSERT INTO chat_messages
│  │   to DB          │    (sender='bot', message)
│  │                  │
│  └─ Return to       │
│     Frontend        │
│      {              │
│        bot_messages,│
│        user_message,│
│        session_id   │
│      }              │
└────┬────────────────┘
     │
     │ Response: {bot_messages: [...]}
     ▼
┌─────────┐
│  USER   │ Hiển thị:
│         │ - Text bubble: "Mình tìm thấy..."
│         │ - Product carousel với 5 sản phẩm
└─────────┘
```

---

## 3. LUỒNG: SLOT FILLING (Thêm vào giỏ hàng)

### Scenario: User thiếu thông tin size/màu

```
USER: "Thêm vào giỏ"
   │
   ▼
RASA NLU: intent=action_add_cart
   │
   ▼
DIALOG MANAGER:
   ├─ Check slots:
   │   ✓ product_id: 456 (from context)
   │   ✗ size: None  ◄── MISSING
   │   ✗ color: None ◄── MISSING
   │
   └─ Decision: ASK for missing slots

Response: {
  "text": "Bạn muốn size nào nhỉ?",
  "custom": {
    "type": "size_selector",
    "options": ["S", "M", "L", "XL"]
  }
}
   │
   ▼
USER: Chọn "M" (hoặc nhập "Size M")
   │
   ▼
RASA:
   ├─ Update slot: size="M"
   ├─ Check slots again:
   │   ✓ product_id: 456
   │   ✓ size: M
   │   ✗ color: None ◄── STILL MISSING
   │
   └─ ASK again

Response: "Màu nào bạn nhỉ?"
   │
   ▼
USER: "Đen"
   │
   ▼
RASA:
   ├─ Update slot: color="đen"
   ├─ All slots filled! ✓
   │
   └─ Execute: action_add_to_cart
       │
       └─ POST /api/chatbot/cart/add
          Body: {
            customer_id: 123,
            product_id: 456,
            size: "M",
            color: "đen",
            quantity: 1
          }

BACKEND:
   ├─ Find variant_id (product_id + size + color)
   ├─ Check stock
   ├─ Add to cart
   └─ Return success

Response: "Đã thêm vào giỏ hàng! 🛒"
```

---

## 4. LUỒNG: TẠO SUPPORT TICKET

```
USER: "Tôi muốn gặp nhân viên"
   │
   ▼
RASA:
   ├─ Intent: faq_contact_human
   └─ Action: action_create_support_ticket
       │
       └─ POST /api/chatbot/support-tickets
          Body: {
            customer_id: 123,
            customer_email: "user@example.com",
            subject: "Yêu cầu hỗ trợ từ chatbot",
            message: "Khách hàng muốn gặp nhân viên",
            priority: "normal",
            source: "chatbot"
          }

BACKEND:
   ├─ Generate ticket_code (TK001234)
   ├─ INSERT INTO support_tickets
   ├─ [Optional] Send email notification to admin
   └─ Return: { ticket_code: "TK001234" }

RASA: Generate response

Response: {
  "text": "Đã ghi nhận yêu cầu của bạn. 
          Ticket #TK001234. 
          Admin sẽ liên hệ trong 24h qua email.",
  "custom": {
    "type": "ticket_created",
    "ticket_code": "TK001234"
  }
}
```

---

## 5. SESSION MANAGEMENT

### 5.1. Guest User (Chưa login)

```
┌─────────────────────────────────────────────┐
│  Frontend khởi tạo chat widget             │
│                                             │
│  1. Generate visitor_id (UUID)             │
│     visitor_id = crypto.randomUUID()       │
│                                             │
│  2. POST /chat/session                     │
│     Body: { visitor_id: "uuid..." }        │
│                                             │
│  3. Backend:                               │
│     - Tìm hoặc tạo session                 │
│     - INSERT INTO chat_sessions            │
│       (visitor_id, customer_id=NULL)       │
│                                             │
│  4. Return: { session_id: 123 }            │
│                                             │
│  5. Frontend lưu session_id vào state      │
└─────────────────────────────────────────────┘
```

### 5.2. Logged-in User

```
┌─────────────────────────────────────────────┐
│  User đã login (có JWT token)              │
│                                             │
│  1. POST /chat/session                     │
│     Headers: { Authorization: Bearer ... } │
│     Body: {}  (không cần visitor_id)       │
│                                             │
│  2. Backend:                               │
│     - Parse JWT → customer_id              │
│     - Tìm hoặc tạo session                 │
│     - INSERT INTO chat_sessions            │
│       (customer_id, visitor_id=NULL)       │
│                                             │
│  3. Return: { session_id: 456 }            │
└─────────────────────────────────────────────┘
```

### 5.3. Merge Sessions (Sau khi login)

```
┌─────────────────────────────────────────────┐
│  Guest chat → Login → Merge history        │
│                                             │
│  Old: visitor_id="abc-123" (guest)         │
│  New: customer_id=789 (logged in)          │
│                                             │
│  PUT /chat/merge                           │
│  Headers: { Authorization: Bearer ... }    │
│  Body: { visitor_id: "abc-123" }           │
│                                             │
│  Backend:                                  │
│  UPDATE chat_sessions                      │
│  SET customer_id = 789,                    │
│      visitor_id = NULL                     │
│  WHERE visitor_id = 'abc-123'              │
│                                             │
│  → Toàn bộ history được merge              │
└─────────────────────────────────────────────┘
```

---

## 6. CONTEXT TRACKING

### 6.1. Rasa Context Slots

```python
# Rasa tracker lưu các slots trong memory

slots:
  - session_id: str          # Chat session ID
  - customer_id: int         # User ID (nếu login)
  - current_product_id: int  # Sản phẩm đang xem
  - cart_size: str           # Size đã chọn
  - cart_color: str          # Màu đã chọn
  - last_order_id: int       # Đơn hàng gần nhất
  - context: str             # "browsing", "checkout", "support"
```

### 6.2. Flow với context

```
USER: "Tìm áo thun"
   → RASA: product_search_text
   → Products found: [123, 456, 789]
   → Set slot: current_product_id = 123 (first result)

USER: "Cái này giá bao nhiêu?"  ◄── NO product_id mentioned
   → RASA: product_ask_info (entities: info_type="price")
   → Read slot: current_product_id = 123  ✓
   → Action: Get product 123 details
   → Response: "Sản phẩm này giá 299k"

USER: "Thêm vào giỏ"
   → RASA: action_add_cart
   → Read slot: current_product_id = 123  ✓
   → Slot filling: Ask size/color
```

---

## 7. ERROR HANDLING FLOWS

### 7.1. Rasa Server Down

```
USER → BACKEND → (X) RASA TIMEOUT
               ↓
          FALLBACK Response:
          {
            text: "Xin lỗi, chatbot tạm thời 
                   không khả dụng. Vui lòng 
                   thử lại sau.",
            error: "rasa_unavailable"
          }
```

### 7.2. Backend API Error (trong Action)

```
RASA → action_search_products
       ↓
       GET /api/chatbot/products/search
       ↓
       (X) 500 Error
       ↓
    RASA catches exception:
       ↓
    Response: "Có lỗi xảy ra khi tìm kiếm. 
               Bạn có thể thử lại sau."
```

### 7.3. Out of Stock

```
USER: "Thêm vào giỏ size M"
   ↓
RASA → action_add_to_cart
   ↓
BACKEND: Check stock
   ├─ variant_id not found → "Size này không có"
   └─ stock = 0 → "Size này hết hàng"
   ↓
Response: {
  text: "Size M đã hết hàng. Bạn có muốn 
         đăng ký thông báo khi có hàng?",
  custom: {
    type: "button",
    action: "notify_restock",
    variant_id: 456
  }
}
```

---

## 8. API ENDPOINT MAPPING

### Frontend → Backend

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat/session` | POST | Tạo/lấy chat session |
| `/chat/send` | POST | Gửi tin nhắn |
| `/chat/history` | GET | Lấy lịch sử chat |
| `/chat/upload-image` | POST | Upload ảnh trong chat |

### Rasa → Backend (Action APIs)

| Endpoint | Method | Purpose | Rasa Action |
|----------|--------|---------|-------------|
| `/api/chatbot/products/search` | GET | Tìm sản phẩm | `action_search_products` |
| `/api/chatbot/products/:id` | GET | Chi tiết sản phẩm | `action_get_product_detail` |
| `/api/chatbot/products/:id/stock` | GET | Kiểm tra tồn kho | `action_check_stock` |
| `/api/chatbot/promotions/active` | GET | Khuyến mãi active | `action_get_promotions` |
| `/api/chatbot/cart/add` | POST | Thêm vào giỏ | `action_add_to_cart` |
| `/api/chatbot/wishlist/add` | POST | Thêm vào wishlist | `action_add_to_wishlist` |
| `/api/chatbot/orders/customer/:id` | GET | Đơn hàng của khách | `action_get_orders` |
| `/api/chatbot/orders/:id/cancel` | POST | Hủy đơn hàng | `action_cancel_order` |
| `/api/chatbot/support-tickets` | POST | Tạo support ticket | `action_create_ticket` |
| `/api/chatbot/size-chart/:category` | GET | Bảng size | `action_get_size_chart` |
| `/api/chatbot/size-advice` | POST | Tư vấn size | `action_size_advice` |
| `/api/chatbot/ai/image-search` | POST | Tìm theo ảnh | `action_image_search` |

---

## 9. PERFORMANCE CONSIDERATIONS

### Caching Strategy

```
┌─────────────────────────────────────────┐
│  Redis Cache (Optional)                 │
│                                         │
│  - Active promotions (TTL: 5 min)      │
│  - Size chart images (TTL: 1 day)      │
│  - FAQ responses (TTL: 1 hour)         │
│  - Product details (TTL: 15 min)       │
└─────────────────────────────────────────┘
```

### Async Processing

```
Tạo support ticket:
   ├─ Save to DB (sync) ✓
   ├─ Return response ngay
   └─ Send email (async, queue) ⏳
```

---

## 10. SECURITY FLOWS

### Authentication

```
┌────────────────────────────────────────┐
│  Frontend → Backend APIs               │
│                                        │
│  Public endpoints:                     │
│  ✓ POST /chat/session (guest OK)      │
│  ✓ POST /chat/send                    │
│  ✓ GET /chat/history                  │
│                                        │
│  Protected endpoints:                  │
│  🔒 PUT /chat/merge (JWT required)    │
│  🔒 Actions requiring customer_id     │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Backend → Rasa                        │
│                                        │
│  Internal network hoặc API Key         │
│  X-Api-Key: {secret}                   │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Rasa → Backend Action APIs            │
│                                        │
│  Internal endpoints                    │
│  X-Internal-Api-Key: {secret}          │
│  Không public ra internet              │
└────────────────────────────────────────┘
```

---

**Ngày tạo:** 2024-12-07  
**Version:** 1.0
