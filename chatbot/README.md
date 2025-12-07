# 🤖 CHATBOT TRỢ LÝ THÔNG MINH - DOCUMENTATION

## 📚 TỔNG QUAN

Thư mục này chứa tài liệu đầy đủ về tính năng **Chatbot Trợ Lý Thông Minh** cho sàn thương mại điện tử.

---

## 📂 CẤU TRÚC DOCUMENTS

### [01_FEATURE_OVERVIEW.md](./01_FEATURE_OVERVIEW.md)
**Tổng quan tính năng & Kiến trúc hệ thống**

- Mục tiêu chiến lược (Bot-First & Async Support)
- Kiến trúc tổng quan (Frontend ↔ Backend ↔ Rasa)
- Phân công trách nhiệm (Backend/Rasa/Frontend)
- Các tính năng chính
- UI/UX components
- Database tables liên quan
- API endpoints overview
- Technical stack
- Deployment architecture

**Đọc file này trước tiên để hiểu tổng quan!**

---

### [02_INTENT_LOGIC_TABLE.md](./02_INTENT_LOGIC_TABLE.md)
**Bảng logic Intent & xử lý chi tiết**

- 29 intents được phân thành 7 nhóm:
  - Chào hỏi & Giao tiếp cơ bản (4 intents)
  - Tìm kiếm & Sản phẩm (6 intents)
  - Size & Tư vấn (2 intents)
  - Hành động mua hàng (3 intents)
  - Đơn hàng & Hậu mãi (3 intents)
  - Chính sách & FAQ (9 intents)
  - Fallback (2 intents)

- Chi tiết từng intent:
  - Ví dụ User input
  - Entities cần extract
  - Logic xử lý
  - Backend API required
  - Response template
  - UI components
  - Notes

**File quan trọng cho AI/Rasa Dev!**

---

### [03_DATA_FLOW.md](./03_DATA_FLOW.md)
**Luồng dữ liệu chi tiết**

- Kiến trúc tổng quan với diagram
- Luồng chi tiết: Gửi tin nhắn (step by step)
- Luồng Slot Filling (thêm vào giỏ hàng)
- Luồng tạo Support Ticket
- Session Management (Guest, Logged-in, Merge)
- Context Tracking (Rasa slots)
- Error Handling Flows
- API Endpoint Mapping
- Performance Considerations
- Security Flows

**File quan trọng cho Backend Dev & System Architect!**

---

### [04_DATABASE_SCHEMA.md](./04_DATABASE_SCHEMA.md)
**Database Schema & Queries**

- Chat Management Tables:
  - `chat_sessions`
  - `chat_messages`
  
- Support System Tables:
  - `support_tickets`
  - `support_ticket_replies`
  
- E-commerce Core Tables:
  - `products`, `product_variants`
  - `categories`, `sizes`, `colors`
  - `orders`, `order_items`
  - `carts`, `cart_items`
  - `wishlist_items`
  - `promotions`

- Query Examples cho Chatbot
- Indexes & Optimization
- Migration Notes

**File quan trọng cho Backend Dev & Database Admin!**

---

### [05_BACKEND_ASSESSMENT.md](./05_BACKEND_ASSESSMENT.md) ⭐
**Phân tích Backend & APIs cần implement**

- ✅ **Phân tích chi tiết:** APIs đã có vs APIs cần tạo
- ✅ **Mapping Intent → Backend API:** 29 intents đã được kiểm tra
- ✅ **Priority:** HIGH / MEDIUM / LOW
- ✅ **Implementation Plan:** 3 weeks roadmap
- ✅ **Kiến trúc module mới:** `/api/chatbot/*`
- ✅ **Security:** Internal API Key Guard
- ✅ **Testing Checklist**

**Kết luận:**
- Backend đã có ~70% APIs cần thiết
- Cần tạo module `/api/chatbot/` mới với 8 APIs
- Estimate: 3 weeks để hoàn thiện

**FILE QUAN TRỌNG NHẤT CHO PM & BACKEND DEV!**

---

## 🎯 QUICK START

### Cho Project Manager (PM)
1. Đọc: `01_FEATURE_OVERVIEW.md` (Hiểu tổng quan)
2. Đọc: `05_BACKEND_ASSESSMENT.md` (Xem roadmap & estimate)
3. Đọc: `02_INTENT_LOGIC_TABLE.md` (Hiểu tính năng chi tiết)

### Cho Backend Developer
1. Đọc: `05_BACKEND_ASSESSMENT.md` (APIs cần implement)
2. Đọc: `03_DATA_FLOW.md` (Hiểu luồng xử lý)
3. Đọc: `04_DATABASE_SCHEMA.md` (Hiểu database)
4. Implement module `/api/chatbot/` theo plan

### Cho AI/Rasa Developer
1. Đọc: `02_INTENT_LOGIC_TABLE.md` (29 intents chi tiết)
2. Đọc: `03_DATA_FLOW.md` (Hiểu cách gọi Backend APIs)
3. Đọc: `05_BACKEND_ASSESSMENT.md` (Xem endpoints available)
4. Implement Rasa NLU & Custom Actions

### Cho Frontend Developer
1. Đọc: `01_FEATURE_OVERVIEW.md` (UI/UX components)
2. Đọc: `02_INTENT_LOGIC_TABLE.md` (Response types cần render)
3. Đọc: `03_DATA_FLOW.md` (Session management)
4. Implement Chat Widget UI

---

## 📊 STATISTICS

| Metric | Value |
|--------|-------|
| Tổng số Intents | 29 |
| Tổng số nhóm Intent | 7 |
| APIs đã có (reusable) | ~10 |
| APIs cần tạo mới | 8 |
| Database tables liên quan | 15+ |
| Estimate timeline | 3 weeks |
| Priority HIGH APIs | 3 |
| Priority MEDIUM APIs | 4 |
| Priority LOW APIs | 1 |

---

## 🔗 LIÊN KẾT NHANH

### Backend APIs (Existing)
- `/products` - Product search & details
- `/products/availability` - Stock check
- `/products/on-sale` - Flash sale products
- `/cart/*` - Cart management (auth required)
- `/wishlist/*` - Wishlist (auth required)
- `/orders/*` - Order management
- `/orders/track` - Public order tracking
- `/promotions/active` - Active promotions
- `/chat/*` - Chat sessions & messages
- `/ai/search/image` - Image search

### APIs Cần Tạo (New)
- `/api/chatbot/cart/add` - Add to cart (internal)
- `/api/chatbot/wishlist/add` - Add to wishlist (internal)
- `/api/chatbot/orders/:id/cancel` - Cancel order (internal)
- `/api/chatbot/size-chart/:category` - Size chart
- `/api/chatbot/size-advice` - Size advice
- `/api/chatbot/products/recommend` - Product recommendations
- `/api/chatbot/gemini/ask` - Gemini integration
- `/api/chatbot/support-tickets` - Create ticket (reuse)

---

## 🛠️ TECH STACK

### Backend
- **Framework:** NestJS (Node.js + TypeScript)
- **Database:** PostgreSQL + pgvector
- **ORM:** TypeORM
- **Auth:** JWT
- **API Style:** RESTful

### Rasa
- **Version:** Rasa 3.x
- **NLU:** DIET Classifier
- **Policies:** TEDPolicy, RulePolicy
- **Actions:** Rasa SDK (Python)

### Frontend
- **Framework:** Next.js 14 (React)
- **Styling:** TailwindCSS + shadcn/ui
- **State:** React Query
- **Chat UI:** Custom widget

---

## 📝 CHANGELOG

### Version 1.0 (2024-12-07)
- ✅ Hoàn thành 5 documents chính
- ✅ Phân tích 29 intents
- ✅ Assessment backend đầy đủ
- ✅ Roadmap 3 weeks
- ✅ Security considerations
- ✅ Testing checklist

---

## 👥 TEAM ROLES

| Role | Trách nhiệm | File cần đọc |
|------|-------------|--------------|
| **PM** | Quản lý timeline, features | 01, 05, 02 |
| **Backend Dev** | Implement APIs | 05, 03, 04 |
| **AI/Rasa Dev** | NLU & Actions | 02, 03, 05 |
| **Frontend Dev** | Chat UI | 01, 02, 03 |

---

## ⚡ NEXT STEPS

### Week 1 (MVP)
- [ ] Backend: Tạo module `/api/chatbot/`
- [ ] Backend: Implement 3 APIs HIGH priority
- [ ] Rasa: Setup project structure
- [ ] Rasa: Implement 10 basic intents
- [ ] Frontend: Chat widget mockup

### Week 2 (Enhancement)
- [ ] Backend: Implement 4 APIs MEDIUM priority
- [ ] Rasa: Implement 19 remaining intents
- [ ] Rasa: Custom actions integration
- [ ] Frontend: Chat UI components
- [ ] Testing: Integration tests

### Week 3 (Polish)
- [ ] Backend: Optimization & caching
- [ ] Rasa: Fine-tune NLU model
- [ ] Frontend: UI polish
- [ ] Testing: End-to-end tests
- [ ] Deploy: Staging environment

---

## 📧 CONTACT

**Project Manager:** [PM Name]  
**Backend Lead:** [Backend Dev Name]  
**AI/Rasa Lead:** [AI Dev Name]  
**Frontend Lead:** [Frontend Dev Name]

---

**Ngày tạo:** 2024-12-07  
**Version:** 1.0  
**Status:** ✅ Documentation Complete
