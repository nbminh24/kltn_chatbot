# 🔍 BACKEND ASSESSMENT - CHATBOT APIs

## TỔNG QUAN

Document này phân tích backend hiện tại và xác định APIs cần implement cho Chatbot.

**Kết luận tổng quát:**
- ✅ **Backend đã có ~70% APIs cần thiết** cho các tính năng cơ bản
- ⚠️ **Cần tạo module mới `/api/chatbot/` để Rasa gọi**
- 🔑 **Vấn đề chính:** APIs hiện tại yêu cầu JWT auth, không phù hợp cho Rasa actions

---

## 1. PHÂN TÍCH THEO INTENT

### ✅ NHÓM 1: CHÀO HỎI & GIAO TIẾP (100% OK)

| Intent | Backend API Required | Status | Note |
|--------|---------------------|--------|------|
| `greet` | None (static response) | ✅ | Rasa xử lý |
| `goodbye` | None | ✅ | Rasa xử lý |
| `thanks` | None | ✅ | Rasa xử lý |
| `bot_identity` | None | ✅ | Rasa xử lý |

**Conclusion:** Không cần backend API.

---

### ⚠️ NHÓM 2: TÌM KIẾM & SẢN PHẨM (60% OK - Cần adapt)

#### 2.1. product_search_text - Tìm sản phẩm theo text

**Intent:** User tìm sản phẩm theo category, color, keyword

**API hiện có:**
```
✅ GET /products
   Query params: 
   - search (keyword)
   - category_slug
   - colors (tên hoặc ID)
   - sizes
   - min_price, max_price
   - sort_by
   - page, limit
```

**Location:** `src/modules/products/products.controller.ts` line 14-32

**Đánh giá:** 
- ✅ Đã có đầy đủ filters
- ✅ Public API (không cần auth)
- ⚠️ Response format có thể cần adjust cho chatbot

**Cần làm:**
- **Option 1:** Rasa gọi trực tiếp `/products` (khuyến nghị)
- **Option 2:** Tạo `/api/chatbot/products/search` với response format tối ưu cho chatbot

---

#### 2.2. product_search_image - Tìm theo ảnh

**Intent:** User upload ảnh tìm sản phẩm tương tự

**API hiện có:**
```
✅ POST /ai/search/image
   Content-Type: multipart/form-data
   Field: image
```

**Location:** `src/modules/ai/ai.controller.ts` line 32-53

**Đánh giá:**
- ✅ Đã implement với pgvector
- ✅ Public API
- ⚠️ Đang dùng mock vector (cần FastAPI integration)

**Cần làm:**
- ✅ API sẵn sàng, chỉ cần Rasa gọi
- 📅 Future: Integrate FastAPI service thực tế

---

#### 2.3. product_ask_info - Hỏi chi tiết sản phẩm

**Intent:** "Chất vải gì?", "Giá bao nhiêu?"

**API hiện có:**
```
✅ GET /products/id/:id
   Response: Full product details including attributes
```

**Location:** `src/modules/products/products.controller.ts` line 69-83

**Đánh giá:**
- ✅ Đã có API chi tiết sản phẩm
- ✅ Public API
- ✅ Có field `attributes` (JSONB) chứa material, origin, etc.

**Cần làm:**
- ✅ Rasa gọi trực tiếp API này
- **Logic Rasa:** Parse `attributes` JSON để trả lời câu hỏi cụ thể

---

#### 2.4. product_check_stock - Kiểm tra tồn kho

**Intent:** "Còn size M màu đen không?"

**API hiện có:**
```
✅ GET /products/availability
   Query params:
   - name (product name)
   - size (optional)
   - color (optional)
```

**Location:** `src/modules/products/products.controller.ts` line 118-130

**Đánh giá:**
- ✅ Đã có API check availability
- ✅ Public API
- ✅ Hỗ trợ filter theo size + color

**Cần làm:**
- ✅ API sẵn sàng, Rasa gọi trực tiếp

---

#### 2.5. ask_promotion - Hỏi khuyến mãi

**Intent:** "Có mã giảm giá không?"

**API hiện có:**
```
✅ GET /promotions/active
   Response: Active promotions
```

**Location:** `src/modules/promotions/promotions.controller.ts` line 45-53

**Đánh giá:**
- ✅ Đã có API lấy promotions active
- ✅ Public API

**Cần làm:**
- ✅ API sẵn sàng
- **TODO:** Cần API lấy sản phẩm thuộc promotion (flash sale products)

---

#### 2.6. product_recommend_context - Gợi ý theo ngữ cảnh

**Intent:** "Đi đám cưới mặc gì?"

**API hiện có:**
```
❌ KHÔNG CÓ
```

**Cần tạo:**
```typescript
GET /api/chatbot/products/recommend
Query: context (string: "wedding", "beach", "work")

Logic:
- Map context → collection tags in attributes
- Query products có tag tương ứng
- Hoặc dùng AI recommendation (future)
```

**Priority:** MEDIUM (Phase 2)

---

### ⚠️ NHÓM 3: SIZE & TƯ VẤN (0% - Cần implement)

#### 3.1. consult_size_chart - Xem bảng size

**API cần tạo:**
```typescript
GET /api/chatbot/size-chart/:category
Params: category (ao, quan, giay)

Response: {
  category: "ao",
  image_url: "https://...",
  chart: {...}  // Optional structured data
}

Logic:
- Lấy từ `pages` table hoặc static config
- Map category → size chart image URL
```

**Priority:** HIGH

---

#### 3.2. consult_size_advice - Tư vấn size cá nhân

**API cần tạo:**
```typescript
POST /api/chatbot/size-advice
Body: {
  height: number,  // cm
  weight: number,  // kg
  category?: string
}

Response: {
  recommended_size: "M",
  confidence: "high",
  reason: "Dựa trên chiều cao và cân nặng của bạn"
}

Logic rules:
- Height 160-170, Weight 50-60 → Size M
- Height 170-180, Weight 60-70 → Size L
- Custom logic theo category
```

**Priority:** MEDIUM

---

### ❌ NHÓM 4: HÀNH ĐỘNG MUA HÀNG (Cần adapt vì auth)

#### 4.1. action_add_cart - Thêm vào giỏ

**API hiện có:**
```
⚠️ POST /cart/items
   Auth: JWT required ❌
   Body: { variant_id, quantity }
```

**Location:** `src/modules/cart/cart.controller.ts` line 27-40

**Vấn đề:** 
- ❌ Yêu cầu JWT authentication
- ❌ Rasa không thể gọi trực tiếp

**Giải pháp:**

**Option 1: Internal API (Khuyến nghị)**
```typescript
// TẠO MỚI
POST /api/chatbot/cart/add
Headers: X-Internal-Api-Key: {secret}
Body: {
  customer_id: number,  // From Rasa context
  variant_id: number,
  quantity: number
}

Logic:
- Không cần JWT
- Dùng internal API key
- Gọi CartService.addItem() trực tiếp
```

**Option 2: Frontend bypass**
- Rasa trả về `custom` data với variant info
- Frontend nhận được → Gọi `/cart/items` với JWT của user
- User phải đăng nhập

**Priority:** HIGH

---

#### 4.2. action_buy_now - Mua ngay

**Giải pháp:**
- Rasa trả về response với `action: "redirect_checkout"`
- Frontend redirect sang `/checkout?variant_id={}&quantity={}`
- Không cần API mới

**Priority:** LOW (Frontend handling)

---

#### 4.3. action_add_wishlist - Thêm yêu thích

**API hiện có:**
```
⚠️ POST /wishlist
   Auth: JWT required ❌
```

**Giải pháp tương tự action_add_cart:**
```typescript
// TẠO MỚI
POST /api/chatbot/wishlist/add
Headers: X-Internal-Api-Key
Body: { customer_id, variant_id }
```

**Priority:** MEDIUM

---

### ⚠️ NHÓM 5: ĐƠN HÀNG (80% OK)

#### 5.1. order_status_check - Tra cứu đơn hàng

**API hiện có:**
```
✅ GET /orders/track
   Public API ✓
   Query: order_id hoặc phone+email
```

**Location:** `src/modules/orders/orders.controller.ts` line 15-28

**Đánh giá:**
- ✅ Public API, không cần auth
- ✅ Hỗ trợ tra cứu bằng order_id hoặc thông tin cá nhân

**Cần làm:**
- ✅ Rasa gọi trực tiếp
- **Note:** Cần customer_id từ context nếu user đã login

---

#### 5.2. order_cancel_request - Yêu cầu hủy đơn

**API hiện có:**
```
⚠️ POST /orders/:id/cancel
   Auth: JWT required ❌
```

**Location:** `src/modules/orders/orders.controller.ts` line 73-87

**Giải pháp:**
```typescript
// TẠO MỚI
POST /api/chatbot/orders/:id/cancel
Headers: X-Internal-Api-Key
Body: { customer_id: number }

Logic:
- Verify customer owns order
- Check status (only pending can cancel)
- Call OrdersService.cancelOrder()
```

**Priority:** HIGH

---

#### 5.3. order_feedback - Gửi phản hồi/khiếu nại

**API hiện có:**
```
✅ POST /api/chatbot/support-tickets
   (Đã có trong support module)
```

**Đánh giá:**
- ✅ Có thể tạo ticket qua support API

**Cần làm:**
- ✅ Rasa gọi API tạo ticket với priority HIGH khi detect negative sentiment

---

### ✅ NHÓM 6: CHÍNH SÁCH & FAQ (90% OK)

#### 6.1. faq_store_info - Thông tin cửa hàng

**Giải pháp:**
- **Option 1:** Static response trong Rasa (khuyến nghị)
- **Option 2:** Tạo API `/api/chatbot/store-info` lấy từ `pages` table

**Priority:** LOW (Static OK)

---

#### 6.2. faq_contact_human - Gặp nhân viên

**API sử dụng:**
```
✅ POST /api/chatbot/support-tickets
```

**Đánh giá:**
- ✅ Đã có API tạo ticket (admin module)

---

#### 6.3-6.9. FAQ khác (payment, shipping, return policy...)

**Giải pháp:**
- ✅ Static responses trong Rasa (khuyến nghị)
- **Alternative:** Lưu trong `pages` table → API dynamic

**Priority:** LOW

---

### ⚠️ NHÓM 7: FALLBACK

#### 7.1. out_of_scope_gemini - Câu hỏi ngoài lề

**API cần tạo:**
```typescript
POST /api/chatbot/gemini/ask
Body: {
  message: string,
  context?: string
}

Response: {
  answer: string,
  source: "gemini"
}

Logic:
- Call Google Gemini API
- Prompt: "Trả lời ngắn gọn, lái về mua sắm thời trang"
- Rate limit: 5 calls/session
```

**Priority:** MEDIUM (Phase 2)

---

## 2. SUMMARY TABLE: APIs CẦN TẠO

### 🔴 Priority HIGH (MVP)

| Endpoint | Method | Purpose | Reason |
|----------|--------|---------|--------|
| `/api/chatbot/cart/add` | POST | Thêm vào giỏ (internal) | Bypass JWT auth |
| `/api/chatbot/orders/:id/cancel` | POST | Hủy đơn (internal) | Bypass JWT auth |
| `/api/chatbot/size-chart/:category` | GET | Lấy bảng size | Tư vấn size |

### 🟡 Priority MEDIUM (Phase 2)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chatbot/wishlist/add` | POST | Thêm wishlist (internal) |
| `/api/chatbot/size-advice` | POST | Tư vấn size cá nhân |
| `/api/chatbot/products/recommend` | GET | Gợi ý theo ngữ cảnh |
| `/api/chatbot/gemini/ask` | POST | Câu hỏi ngoài lề |

### 🟢 Priority LOW (Optional)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chatbot/store-info` | GET | Thông tin cửa hàng (có thể static) |
| `/api/chatbot/policies/:type` | GET | FAQs dynamic (có thể static) |

---

## 3. KIẾN TRÚC MODULE CHATBOT MỚI

### 3.1. Cấu trúc thư mục đề xuất

```
src/modules/chatbot/
├── chatbot.module.ts
├── chatbot.controller.ts
├── chatbot.service.ts
├── guards/
│   └── internal-api-key.guard.ts
├── dto/
│   ├── add-to-cart-internal.dto.ts
│   ├── size-advice.dto.ts
│   └── gemini-ask.dto.ts
└── README.md
```

### 3.2. Controller Structure

```typescript
@Controller('api/chatbot')
@UseGuards(InternalApiKeyGuard)  // X-Internal-Api-Key
export class ChatbotController {
  
  // ===== PRODUCTS =====
  @Get('products/search')
  async searchProducts(@Query() query) {
    // Proxy to ProductsService.findAll()
  }
  
  @Get('products/:id')
  async getProduct(@Param('id') id) {
    // Proxy to ProductsService.findById()
  }
  
  @Get('products/:id/stock')
  async checkStock(@Param('id') id, @Query() query) {
    // Check variant stock
  }
  
  // ===== CART (INTERNAL) =====
  @Post('cart/add')
  async addToCart(@Body() dto: AddToCartInternalDto) {
    // dto: { customer_id, variant_id, quantity }
    // Call CartService.addItem() trực tiếp
    // Không cần JWT
  }
  
  // ===== WISHLIST (INTERNAL) =====
  @Post('wishlist/add')
  async addToWishlist(@Body() dto) {
    // dto: { customer_id, variant_id }
  }
  
  // ===== ORDERS =====
  @Post('orders/:id/cancel')
  async cancelOrder(@Param('id') id, @Body() dto) {
    // dto: { customer_id }
    // Verify ownership
    // Call OrdersService.cancelOrder()
  }
  
  // ===== SIZE =====
  @Get('size-chart/:category')
  async getSizeChart(@Param('category') category) {
    // Return size chart image URL
  }
  
  @Post('size-advice')
  async getSizeAdvice(@Body() dto: SizeAdviceDto) {
    // dto: { height, weight, category }
    // Apply rules logic
  }
  
  // ===== SUPPORT =====
  @Post('support-tickets')
  async createTicket(@Body() dto) {
    // Already exists in admin module
    // Can reuse
  }
  
  // ===== AI =====
  @Post('gemini/ask')
  async geminiAsk(@Body() dto) {
    // dto: { message, context }
    // Call Gemini API
  }
  
  // ===== PROMOTIONS =====
  @Get('promotions/active')
  async getActivePromotions() {
    // Proxy to PromotionsService
  }
}
```

### 3.3. Internal API Key Guard

```typescript
@Injectable()
export class InternalApiKeyGuard implements CanActivate {
  constructor(private configService: ConfigService) {}
  
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers['x-internal-api-key'];
    const validKey = this.configService.get('INTERNAL_API_KEY');
    
    return apiKey === validKey;
  }
}
```

**Environment Variable:**
```env
INTERNAL_API_KEY=your-super-secret-key-for-rasa
```

---

## 4. RESPONSE FORMAT CHUẨN

### Cho Rasa Actions

```json
{
  "success": true,
  "data": {...},
  "meta": {
    "timestamp": "2024-12-07T10:00:00Z",
    "source": "backend_api"
  }
}
```

### Error Format

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Không tìm thấy sản phẩm",
    "details": {}
  }
}
```

---

## 5. SECURITY CONSIDERATIONS

### 5.1. Internal APIs Protection

- ✅ Sử dụng `InternalApiKeyGuard`
- ✅ Không expose ra internet public
- ✅ Chỉ Rasa server được phép gọi
- ✅ Rate limiting (nếu cần)

### 5.2. Customer ID Validation

```typescript
// Trong internal APIs
async addToCart(dto: AddToCartInternalDto) {
  // Verify customer exists
  const customer = await this.customerRepo.findOne({
    where: { id: dto.customer_id }
  });
  
  if (!customer) {
    throw new NotFoundException('Customer not found');
  }
  
  // Proceed...
}
```

### 5.3. Network Isolation

**Production Architecture:**
```
┌──────────────────┐
│  Rasa Server     │ (Private network)
│  10.0.1.100:5005 │
└────────┬─────────┘
         │ Internal API Key
         ▼
┌──────────────────┐
│  Backend API     │
│  /api/chatbot/*  │ (Not public internet)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  PostgreSQL DB   │
└──────────────────┘
```

---

## 6. IMPLEMENTATION PLAN

### Phase 1: MVP (Week 1)

**Day 1-2:**
- ✅ Tạo module `chatbot`
- ✅ Implement `InternalApiKeyGuard`
- ✅ Tạo các DTOs

**Day 3-4:**
- ✅ Implement cart/add (internal)
- ✅ Implement wishlist/add (internal)
- ✅ Implement orders/cancel (internal)
- ✅ Implement size-chart API

**Day 5:**
- ✅ Testing với Postman
- ✅ Document APIs
- ✅ Setup env variables

### Phase 2: Enhancement (Week 2)

- 🔄 Implement size-advice logic
- 🔄 Implement product recommendation
- 🔄 Integrate Gemini API
- 🔄 Optimize response format

### Phase 3: Polish (Week 3)

- 📅 Performance optimization
- 📅 Caching layer (Redis)
- 📅 Monitoring & logging
- 📅 Load testing

---

## 7. TESTING CHECKLIST

### Unit Tests

- [ ] ChatbotService methods
- [ ] InternalApiKeyGuard
- [ ] Size advice logic
- [ ] DTO validation

### Integration Tests

- [ ] POST /api/chatbot/cart/add with valid customer_id
- [ ] POST /api/chatbot/cart/add with invalid customer_id → 404
- [ ] POST /api/chatbot/cart/add without API key → 401
- [ ] GET /api/chatbot/size-chart/ao → Returns image URL
- [ ] POST /api/chatbot/orders/:id/cancel (valid) → Success
- [ ] POST /api/chatbot/orders/:id/cancel (wrong customer) → 403

### End-to-End với Rasa

- [ ] Rasa action_search_products → Backend → Return products
- [ ] Rasa action_add_to_cart → Backend → Cart updated
- [ ] Rasa action_create_ticket → Backend → Ticket created

---

## 8. ENVIRONMENT VARIABLES CẦN THÊM

```env
# Chatbot Internal API
INTERNAL_API_KEY=your-super-secret-key-123456

# Rasa Server
RASA_SERVER_URL=http://localhost:5005

# Gemini API (Phase 2)
GEMINI_API_KEY=your-gemini-api-key

# Size Chart URLs (hoặc lưu DB)
SIZE_CHART_AO_URL=https://cdn.example.com/size-chart-ao.png
SIZE_CHART_QUAN_URL=https://cdn.example.com/size-chart-quan.png
SIZE_CHART_GIAY_URL=https://cdn.example.com/size-chart-giay.png
```

---

## 9. KẾT LUẬN

### ✅ Điểm mạnh Backend hiện tại

1. **Đã có ~70% APIs cần thiết:**
   - Products search ✓
   - Stock check ✓
   - Orders tracking ✓
   - Promotions ✓
   - Chat sessions ✓
   - Support tickets ✓

2. **Database schema đầy đủ:**
   - Không cần migration mới
   - Hỗ trợ tốt cho chatbot

3. **Code quality tốt:**
   - Có DTOs validation
   - Có decorators/guards
   - Có Swagger documentation

### ⚠️ Việc cần làm

1. **Tạo module chatbot mới** với internal APIs
2. **Implement 3 APIs HIGH priority:**
   - cart/add
   - orders/cancel
   - size-chart

3. **Security:** Internal API key guard

### 📊 Estimate Timeline

- **MVP (Week 1):** 3-4 APIs HIGH priority
- **Phase 2 (Week 2):** 4 APIs MEDIUM priority
- **Phase 3 (Week 3):** Polish & optimization

**Total: ~3 weeks** để hoàn thiện backend cho chatbot.

---

**Ngày tạo:** 2024-12-07  
**Version:** 1.0  
**Tổng số APIs cần tạo:** 8 (3 HIGH + 4 MEDIUM + 1 LOW)
