# Backend API Requirements - Chatbot Bug Fixes

**Ngày:** 12/12/2024  
**Từ:** Chatbot Development Team  
**Đến:** Backend Development Team  
**Priority:** HIGH

---

## 📋 Tổng Quan

Sau khi fix bugs cho chatbot, phát hiện **3 vấn đề cần backend hỗ trợ** để chatbot hoạt động đầy đủ:

1. ✅ **MISSING API:** Endpoint lấy giỏ hàng của customer
2. ⚠️ **INCOMPLETE DATA:** Product API thiếu thông tin variants/colors đầy đủ
3. ⚠️ **MISSING FIELD:** customer_id slot không được set khi user đăng nhập

---

## 🚨 Issue #1: MISSING API - Get Cart by Customer ID

### Mô Tả
Chatbot cần API để lấy giỏ hàng của customer khi user yêu cầu "Xem giỏ hàng" hoặc "View cart".

### Endpoint Cần Thiết
```
GET /api/chatbot/cart/:customer_id
hoặc
GET /api/chatbot/cart?customer_id={id}
```

### Request Headers
```
X-Internal-Api-Key: {INTERNAL_API_KEY}
```

### Response Format Mong Đợi
```json
{
  "success": true,
  "data": {
    "customer_id": 123,
    "items": [
      {
        "id": 1,
        "product_id": 456,
        "product_name": "Basic White T-Shirt",
        "variant_id": 789,
        "size": "M",
        "color": "White",
        "quantity": 2,
        "price": 150000,
        "image_url": "https://..."
      }
    ],
    "total_items": 2,
    "subtotal": 300000,
    "total": 300000
  }
}
```

### Response Khi Cart Rỗng
```json
{
  "success": true,
  "data": {
    "customer_id": 123,
    "items": [],
    "total_items": 0,
    "subtotal": 0,
    "total": 0
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Customer not found",
  "message": "Customer with ID 123 does not exist"
}
```

### File Cần Update
- Backend: Tạo endpoint mới trong cart controller
- Chatbot: `actions/api_client.py` - Thêm method `get_cart(customer_id: int)`

### Code Reference (Chatbot đang gọi)
```python
# File: actions/actions.py:1745
result = api_client.get_cart()
# Cần truyền customer_id từ slot
```

---

## ⚠️ Issue #2: INCOMPLETE DATA - Product Variants/Colors

### Mô Tả
Các endpoint hiện tại trả về product nhưng **thiếu thông tin đầy đủ về variants** (size, color combinations). Chatbot cần data này để:
1. Hiển thị màu sắc có sẵn cho user
2. Tìm đúng `variant_id` khi add to cart

### Endpoint Cần Cải Thiện

#### 2.1. Search Products API
```
Endpoint: GET /internal/products?search={query}
```

**Response Hiện Tại (thiếu variants):**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Basic T-Shirt",
      "selling_price": 150000,
      "total_stock": 50
      // ❌ Thiếu: variants, colors
    }
  ]
}
```

**Response Cần Có:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Basic T-Shirt",
      "selling_price": 150000,
      "total_stock": 50,
      "variants": [
        {
          "id": 101,
          "variant_id": 101,
          "size": "S",
          "color": "White",
          "stock": 10
        },
        {
          "id": 102,
          "variant_id": 102,
          "size": "M",
          "color": "White",
          "stock": 15
        },
        {
          "id": 103,
          "variant_id": 103,
          "size": "M",
          "color": "Black",
          "stock": 12
        }
      ],
      "colors": ["White", "Black"]  // ✅ Array unique colors
    }
  ]
}
```

#### 2.2. Get Product By ID API
```
Endpoint: GET /products/id/:product_id
```

**Yêu Cầu Tương Tự:**
- Phải bao gồm `variants[]` array đầy đủ
- Phải bao gồm `colors[]` array (unique colors)

### Tại Sao Cần?
Chatbot logic hiện tại (sau fix):
```python
# File: actions/actions.py:1648-1660
variants = product_data.get("variants", [])

# Tìm variant_id dựa trên size + color user chọn
for v in variants:
    v_size = str(v.get("size", "")).upper()
    v_color = str(v.get("color", "")).lower()
    
    if v_size == size.upper() and v_color == color.lower():
        variant_id = v.get("id") or v.get("variant_id")
        break
```

**Nếu không có variants → chatbot không tìm được variant_id → add to cart fail!**

---

## 🔐 Issue #3: Customer ID Not Available

### Mô Tả
Chatbot cần `customer_id` để:
1. Add to cart: `add_to_cart(customer_id, variant_id, quantity)`
2. View cart: `get_cart(customer_id)`
3. Track orders, cancel orders

**Hiện tại:** Slot `customer_id` luôn = `None` trong tracker

### Giải Pháp Đề Xuất

#### Option A: Frontend gửi customer_id qua metadata (RECOMMENDED)
Khi user đã đăng nhập, frontend gửi message kèm metadata:

```javascript
// Frontend code
rasa.sendMessage({
  text: "Thêm vào giỏ hàng",
  metadata: {
    customer_id: 123,
    user_jwt_token: "eyJhbGc..."
  }
})
```

Chatbot sẽ extract:
```python
customer_id = tracker.latest_message.get("metadata", {}).get("customer_id")
```

#### Option B: Chatbot gọi API verify JWT token
Backend cung cấp endpoint:
```
POST /api/chatbot/auth/verify
Headers: X-Internal-Api-Key
Body: { "jwt_token": "..." }

Response: {
  "success": true,
  "data": {
    "customer_id": 123,
    "email": "user@example.com"
  }
}
```

#### Option C: Backend tự động inject customer_id vào request (BEST)
Backend middleware intercept Rasa webhook, extract JWT từ header, inject `customer_id` vào message metadata.

---

## 📊 Testing Requirements

### Test Case 1: View Cart
```
User logged in (customer_id = 123)
User: "Xem giỏ hàng"

Expected:
- Chatbot gọi GET /api/chatbot/cart/123
- Hiển thị items trong cart hoặc "Cart is empty"
```

### Test Case 2: Add to Cart with Variants
```
User: "Tìm áo thun"
Bot: Shows product with colors: "White, Black, Red"
User: "Thêm vào giỏ size M màu đen"

Expected:
- Chatbot gọi GET /products/id/{id}
- Nhận được variants array
- Tìm variant có size="M", color="Black"
- Gọi POST /api/chatbot/cart/add với variant_id đúng
```

### Test Case 3: Product Search Shows Colors
```
User: "Tìm áo sơ mi"

Expected Response:
"Found 5 products:
1. **Oxford Shirt** - White, Blue, Pink - 350,000₫ ✅
2. **Linen Shirt** - Beige, Navy - 280,000₫ ✅"
```

---

## 🔧 Implementation Checklist

### Backend Tasks
- [ ] **[HIGH]** Tạo endpoint `GET /api/chatbot/cart/:customer_id`
- [ ] **[HIGH]** Update `GET /internal/products` - thêm `variants[]` và `colors[]`
- [ ] **[HIGH]** Update `GET /products/id/:id` - thêm `variants[]` và `colors[]`
- [ ] **[MEDIUM]** Implement customer_id injection (Option A, B, hoặc C)
- [ ] **[LOW]** Test với Postman/Insomnia
- [ ] **[LOW]** Update API documentation

### Chatbot Tasks (Sẽ làm sau khi backend ready)
- [ ] Thêm method `get_cart(customer_id)` vào `api_client.py`
- [ ] Update `ActionViewCart` để lấy customer_id từ slot/metadata
- [ ] Test integration với backend mới
- [ ] Update domain.yml nếu cần thêm slots

---

## 📞 Contact

Nếu có thắc mắc về requirements, vui lòng liên hệ:
- Chatbot Team Lead
- Slack: #chatbot-backend-integration
- Email: dev@company.com

---

## 📝 Notes

1. **Security:** Tất cả chatbot endpoints phải require `X-Internal-Api-Key` header
2. **Performance:** Cache product variants nếu có thể (variants ít thay đổi)
3. **Error Handling:** Luôn trả về format nhất quán `{ success, data/error, message }`
4. **Logging:** Log tất cả chatbot API calls để debug

---

**Status:** 🟡 WAITING FOR BACKEND IMPLEMENTATION  
**ETA:** TBD  
**Blocker:** Add to Cart và View Cart features không hoạt động 100% cho đến khi có đủ 3 APIs
