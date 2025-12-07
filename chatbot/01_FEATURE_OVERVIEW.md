# 🤖 CHATBOT TRỢ LÝ THÔNG MINH - TỔNG QUAN TÍNH NĂNG

## 1. MỤC TIÊU CHIẾN LƯỢC

### Mô hình hoạt động
**Bot-First & Async Support Model**

- **Bot xử lý 100%:** Tất cả câu hỏi đều được chatbot trả lời tự động
- **Không realtime chat với admin:** Không có tính năng admin chat trực tiếp
- **Support qua ticket:** Khi cần can thiệp → Bot tạo support ticket → Admin xử lý sau qua Email/Dashboard

### Lợi ích
- ✅ Giảm độ phức tạp kỹ thuật (không cần Socket.io/WebSocket)
- ✅ Tận dụng database hiện có (`chat_sessions`, `chat_messages`, `support_tickets`)
- ✅ Scale dễ dàng (stateless)
- ✅ Giảm tải công việc cho admin

---

## 2. KIẾN TRÚC HỆ THỐNG

### 2.1. Luồng dữ liệu chính

```
┌─────────┐         ┌──────────────┐         ┌──────────────┐
│         │  HTTP   │              │  HTTP   │              │
│  USER   │ ◄────► │   BACKEND    │ ◄────► │  RASA SERVER │
│         │         │   (Proxy)    │         │   (Python)   │
└─────────┘         └──────────────┘         └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │   Database   │
                    └──────────────┘
```

### 2.2. Chi tiết luồng xử lý

**Bước 1: User gửi tin nhắn**
- Frontend gọi: `POST /chat/send`
- Body: `{ session_id, message }`

**Bước 2: Backend xử lý**
- Lưu message của user vào `chat_messages`
- Forward request đến Rasa Server: `POST {RASA_URL}/webhooks/rest/webhook`

**Bước 3: Rasa xử lý**
- **NLU:** Phân tích intent + entities
- **Dialog Management:** Quyết định action
- **Actions:** 
  - Nếu cần data → Gọi ngược Backend APIs (product search, order status, etc.)
  - Nếu không cần data → Trả response text có sẵn

**Bước 4: Rasa trả response**
- Format: `[{ "text": "...", "custom": {...} }]`
- Backend nhận response

**Bước 5: Backend xử lý response**
- Lưu bot messages vào `chat_messages`
- Parse custom data (product cards, buttons, etc.)
- Trả về Frontend

**Bước 6: Frontend render**
- Text bubble
- Product cards
- Action buttons
- Stickers

---

## 3. PHÂN CÔNG TRÁCH NHIỆM

### Backend (NestJS/Node.js)
**Role:** API Provider & Data Orchestrator

**Trách nhiệm:**
- ✅ Cung cấp APIs cho Rasa gọi (product search, stock check, create ticket, etc.)
- ✅ Quản lý chat sessions & messages
- ✅ Lưu trữ conversation history
- ✅ Proxy requests giữa Frontend và Rasa
- ✅ Authentication & Authorization
- ✅ Business logic (checkout, inventory, promotions)

**Không làm:**
- ❌ Không xử lý NLU/Intent recognition
- ❌ Không quản lý dialog state

### Rasa Server (Python)
**Role:** Conversation AI Engine

**Trách nhiệm:**
- ✅ NLU: Phân tích intent + entities
- ✅ Dialog Management: Slot filling, context tracking
- ✅ Response Generation: Tạo câu trả lời
- ✅ Gọi Backend APIs khi cần data

**Không làm:**
- ❌ Không lưu database
- ❌ Không xử lý business logic
- ❌ Không authenticate users

### Frontend (Next.js/React)
**Role:** UI/UX Layer

**Trách nhiệm:**
- ✅ Chat widget UI
- ✅ Render messages (text, cards, buttons)
- ✅ Handle user actions (add to cart, buy now, etc.)
- ✅ Gọi Backend APIs

**Không làm:**
- ❌ Không gọi trực tiếp Rasa
- ❌ Không xử lý business logic

---

## 4. CÁC TÍNH NĂNG CHÍNH

### 4.1. Nhóm Giao Tiếp Cơ Bản
- Chào hỏi, tạm biệt, cảm ơn
- Giới thiệu bot

### 4.2. Nhóm Sản Phẩm
- **Tìm kiếm sản phẩm:**
  - Theo text (category, color, keyword)
  - Theo hình ảnh (image search với AI)
- **Thông tin sản phẩm:**
  - Chi tiết sản phẩm (material, price, description)
  - Kiểm tra tồn kho (size, color)
  - Khuyến mãi đang áp dụng
- **Tư vấn:**
  - Gợi ý sản phẩm theo ngữ cảnh
  - Tư vấn size (chart, personal advice)
  - Phối đồ

### 4.3. Nhóm Hành Động Mua Hàng
- Thêm vào giỏ hàng (với slot filling size/color)
- Mua ngay (redirect checkout)
- Thêm vào wishlist

### 4.4. Nhóm Đơn Hàng
- Tra cứu trạng thái đơn hàng
- Yêu cầu hủy đơn (nếu còn trong thời gian cho phép)
- Feedback đơn hàng → Tạo support ticket

### 4.5. Nhóm FAQ & Chính Sách
- Thông tin cửa hàng (địa chỉ, giờ làm việc)
- Phương thức thanh toán
- Chính sách vận chuyển
- Chính sách đổi trả
- Liên hệ admin/nhân viên

### 4.6. Nhóm Fallback
- Câu hỏi ngoài lề → Gọi Gemini API (general knowledge)
- Không hiểu → Gợi ý menu hoặc tạo ticket

---

## 5. UI/UX COMPONENTS

### 5.1. Message Types
| Type | Mô tả | Example |
|------|-------|---------|
| **Text Bubble** | Câu trả lời text thông thường | "Chào bạn! Mình có thể giúp gì?" |
| **Product Card** | Thẻ sản phẩm (ảnh, tên, giá, buttons) | [Carousel 3-5 sản phẩm] |
| **Action Buttons** | Nút hành động | "Thêm vào giỏ", "Mua ngay" |
| **Image** | Hình ảnh (size chart, promo banner) | Bảng size áo/quần |
| **Order Status Card** | Timeline trạng thái đơn hàng | Đang chuẩn bị → Đang giao → Đã giao |
| **Sticker** | Nhãn dán trang trí | 🎉 "Xin chào", 😊 "Cảm ơn" |

### 5.2. Interactive Elements
- **Size/Color Chips:** Chọn size/màu trước khi thêm vào giỏ
- **Quick Replies:** Gợi ý câu trả lời nhanh
- **Contact Admin Button:** Khi fallback nhiều lần

---

## 6. DATABASE TABLES LIÊN QUAN

### Chat Management
- `chat_sessions`: Quản lý phiên chat (customer_id hoặc visitor_id)
- `chat_messages`: Lưu toàn bộ tin nhắn (sender: customer/bot)

### Support System
- `support_tickets`: Tickets cần admin xử lý
- `support_ticket_replies`: Lịch sử trả lời ticket

### E-commerce Core
- `products`, `product_variants`: Sản phẩm & variants
- `categories`: Danh mục
- `orders`, `order_items`: Đơn hàng
- `carts`, `cart_items`: Giỏ hàng
- `wishlist_items`: Danh sách yêu thích
- `promotions`: Khuyến mãi

---

## 7. API ENDPOINTS OVERVIEW

### Chat APIs (Frontend ↔ Backend)
```
POST   /chat/session              # Tạo/lấy session
POST   /chat/send                 # Gửi tin nhắn
GET    /chat/history              # Lịch sử chat
POST   /chat/upload-image         # Upload ảnh trong chat
```

### Rasa Action APIs (Rasa ↔ Backend)
```
GET    /api/chatbot/products/search        # Tìm sản phẩm
GET    /api/chatbot/products/:id           # Chi tiết sản phẩm
GET    /api/chatbot/products/:id/stock     # Kiểm tra tồn kho
GET    /api/chatbot/promotions/active      # Khuyến mãi active
GET    /api/chatbot/orders/customer/:id    # Đơn hàng của khách
POST   /api/chatbot/cart/add               # Thêm vào giỏ
POST   /api/chatbot/wishlist/add           # Thêm vào wishlist
POST   /api/chatbot/support-tickets        # Tạo ticket
GET    /api/chatbot/size-chart/:category   # Bảng size
POST   /api/chatbot/ai/image-search        # Tìm theo ảnh
```

---

## 8. FLOW DIAGRAM CHI TIẾT

### 8.1. Flow: Tìm sản phẩm theo text

```
User: "Tìm áo thun đen"
    ↓
Frontend → POST /chat/send
    ↓
Backend: Lưu message → Forward to Rasa
    ↓
Rasa: 
  - Intent: product_search_text
  - Entities: {category: "áo thun", color: "đen"}
  - Action: action_search_products
    ↓
Rasa → GET /api/chatbot/products/search?category=áo%20thun&color=đen
    ↓
Backend: Query database → Return products
    ↓
Rasa: Generate response với product cards
    ↓
Backend: Lưu bot messages → Return to Frontend
    ↓
Frontend: Render product carousel
```

### 8.2. Flow: Tạo support ticket (Fallback)

```
User: "Gặp nhân viên hỗ trợ"
    ↓
Rasa: 
  - Intent: faq_contact_human
  - Action: action_create_support_ticket
    ↓
Rasa → POST /api/chatbot/support-tickets
Body: {
  customer_id: 123,
  subject: "Yêu cầu hỗ trợ từ chatbot",
  message: "Khách hàng muốn gặp nhân viên"
}
    ↓
Backend: Create ticket → Return ticket_code
    ↓
Rasa: "Đã ghi nhận yêu cầu của bạn. Ticket #TK001234. Admin sẽ liên hệ trong 24h."
```

---

## 9. TECHNICAL STACK

### Backend
- **Framework:** NestJS (Node.js)
- **Database:** PostgreSQL + pgvector
- **ORM:** TypeORM
- **Auth:** JWT
- **APIs:** RESTful

### Rasa Server
- **Version:** Rasa 3.x
- **NLU Pipeline:** DIET Classifier
- **Policies:** TEDPolicy, RulePolicy
- **Custom Actions:** Rasa SDK (Python)

### Frontend
- **Framework:** Next.js 14 (React)
- **Styling:** TailwindCSS + shadcn/ui
- **State:** React Query
- **Chat UI:** Custom widget

---

## 10. DEPLOYMENT ARCHITECTURE

```
┌─────────────────────────────────────────────────┐
│              Vercel (Frontend)                  │
│         https://shop.example.com                │
└────────────────┬────────────────────────────────┘
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────────────┐
│         Railway/Render (Backend API)            │
│         https://api.example.com                 │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│  PostgreSQL  │   │ Rasa Server  │
│   Database   │   │  (Port 5005) │
└──────────────┘   └──────────────┘
```

---

## 11. SECURITY & BEST PRACTICES

### Authentication
- Chat sessions: Public (guest) hoặc JWT (logged-in users)
- Rasa Action APIs: Internal network hoặc API Key protection

### Data Privacy
- Không log sensitive data (password, payment info)
- GDPR compliance: User có thể xóa chat history

### Rate Limiting
- Giới hạn số message/phút để chống spam
- Throttle API calls từ Rasa

### Error Handling
- Rasa down → Backend trả fallback message
- API timeout → Graceful degradation

---

## 12. METRICS & MONITORING

### KPIs cần theo dõi
- **Conversation Metrics:**
  - Total conversations
  - Average messages per session
  - Intent distribution
  - Fallback rate
  
- **Business Metrics:**
  - Conversion rate (chat → purchase)
  - Cart add rate from chatbot
  - Ticket creation rate
  
- **Technical Metrics:**
  - Response time (Backend, Rasa)
  - Error rate
  - Uptime

---

## 13. ROADMAP

### Phase 1: MVP (Current)
- ✅ Basic chat flow
- ✅ Product search (text)
- ✅ FAQ static responses
- ⚠️ Support ticket creation

### Phase 2: Enhancement
- 🔄 Image search
- 🔄 Product recommendations (AI)
- 🔄 Size advice (personalized)
- 🔄 Gemini integration (out-of-scope)

### Phase 3: Advanced
- 📅 Voice input
- 📅 Multi-language support
- 📅 Sentiment analysis
- 📅 A/B testing responses

---

**Ngày tạo:** 2024-12-07  
**Version:** 1.0  
**Team:** PM, Backend Dev, Frontend Dev, AI/Rasa Dev
