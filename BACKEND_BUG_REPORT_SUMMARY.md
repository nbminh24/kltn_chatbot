# 🐛 Backend Bug Report - Order Tracking Issues

**Date:** 2025-12-16  
**Component:** Backend API - Orders Module  
**Reported By:** Chatbot Team  
**Priority:** CRITICAL (Security) + HIGH (Data Display)

---

## 📋 Executive Summary

Phát hiện **2 bugs nghiêm trọng** trong API `/orders/track`:
1. 🚨 **CRITICAL:** Security vulnerability - Không verify customer ownership
2. 🔧 **HIGH:** Response format mismatch - Field names không đúng spec

**Impact:**
- ❌ Customer có thể xem orders của người khác (privacy violation)
- ❌ Chatbot hiển thị "Unknown" và "N/A" thay vì data thực
- ❌ Blocking production deployment

---

## 🚨 BUG #1: CRITICAL SECURITY VULNERABILITY

### **Issue: No Customer Ownership Verification**

**Severity:** 🔴 CRITICAL  
**Type:** Security - Authorization Bypass  
**CVSS Score:** 7.5 (High)

### **Mô tả lỗi**
Backend endpoint `/orders/track` **không kiểm tra customer_id** trước khi trả order details. Bất kỳ authenticated user nào cũng có thể xem order của người khác bằng cách thử order_id.

### **Proof of Concept**
```http
# Customer 1 (nbminh24@gmail.com) login
POST /auth/login
{
  "email": "nbminh24@gmail.com",
  "password": "***"
}

# Response
{
  "token": "eyJ...customer_id=1...",
  "customer_id": 1
}

# Customer 1 requests Order #0000000001 (belongs to Customer 2)
GET /orders/track?order_id=0000000001
Authorization: Bearer eyJ...customer_id=1...

# Expected: 403 Forbidden
# Actual: 200 OK with full order details ❌
{
  "success": true,
  "data": {
    "order_id": 1,
    "order_number": "0000000001",
    "customer_id": 2,  // ← Belongs to different customer!
    "total_amount": 500000,
    "shipping_address": "123 Private Street...",
    "items": [...]
  }
}
```

### **Data Exposure Risk**
Attacker có thể:
- Enumerate tất cả orders: `0000000001`, `0000000002`, ..., `9999999999`
- Lấy được thông tin:
  - Tên, địa chỉ, SĐT khách hàng
  - Lịch sử mua hàng
  - Order amount & payment status
  - Product preferences

### **Exploit Script**
```bash
#!/bin/bash
TOKEN="<any_valid_jwt>"

for i in {1..10000}; do
  ORDER_ID=$(printf "%010d" $i)
  curl -s "http://localhost:3001/orders/track?order_id=$ORDER_ID" \
    -H "Authorization: Bearer $TOKEN" \
    >> stolen_orders.json
done

# Result: Toàn bộ database orders bị leak
```

### **Root Cause**
**File:** `backend/src/services/orders.service.ts` hoặc `controllers/order.controller.ts`

```typescript
// Current implementation (INCORRECT)
async trackOrder(order_id: string): Promise<Order> {
  const order = await this.orderRepository.findOne({
    where: { order_number: order_id }
  });
  
  if (!order) {
    throw new NotFoundException('Không tìm thấy đơn hàng');
  }
  
  // ❌ NO OWNERSHIP CHECK - Returns immediately
  return order;
}
```

### **Required Fix**

```typescript
// backend/src/controllers/order.controller.ts

async trackOrder(req: Request, res: Response) {
  try {
    const { order_id } = req.query;
    
    // Extract authenticated customer_id from JWT
    const authenticatedCustomerId = req.user?.id;
    
    if (!authenticatedCustomerId) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required'
      });
    }

    // Find order
    const cleanOrderId = order_id.replace(/^#/, '');
    const order = await this.orderService.findByOrderNumber(cleanOrderId);
    
    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Không tìm thấy đơn hàng'
      });
    }

    // ✅ CRITICAL: Verify ownership
    if (order.customer_id !== authenticatedCustomerId) {
      // Log security violation
      console.warn(
        `[SECURITY] Customer ${authenticatedCustomerId} ` +
        `attempted to access order ${order.order_number} ` +
        `belonging to customer ${order.customer_id}`
      );
      
      return res.status(403).json({
        success: false,
        message: 'Bạn không có quyền xem đơn hàng này',
        error: 'Forbidden'
      });
    }

    // Return order only if ownership verified
    return res.status(200).json({
      success: true,
      data: {
        order_id: order.id,
        order_number: order.order_number,
        customer_id: order.customer_id,
        
        // Standardized fields (see Bug #2)
        status: order.fulfillment_status,
        total: order.total_amount,
        
        // Detailed fields
        fulfillment_status: order.fulfillment_status,
        payment_status: order.payment_status,
        total_amount: order.total_amount,
        created_at: order.created_at,
        updated_at: order.updated_at,
        shipping_address: order.shipping_address,
        tracking_number: order.tracking_number,
        items: order.items
      }
    });
  } catch (error) {
    console.error('[OrderController] Track order error:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal Server Error'
    });
  }
}
```

### **Testing**

**Test Case 1: Own Order (Should Pass)**
```bash
# Customer 1 accessing their own order
curl "http://localhost:3001/orders/track?order_id=0000000032" \
  -H "Authorization: Bearer <customer_1_jwt>"

# Expected: 200 OK with order details
```

**Test Case 2: Other's Order (Should Fail)**
```bash
# Customer 1 trying to access Customer 2's order
curl "http://localhost:3001/orders/track?order_id=0000000001" \
  -H "Authorization: Bearer <customer_1_jwt>"

# Expected: 403 Forbidden
{
  "success": false,
  "message": "Bạn không có quyền xem đơn hàng này",
  "error": "Forbidden"
}
```

### **Additional Security Measures**

**1. Rate Limiting**
```typescript
import rateLimit from 'express-rate-limit';

const orderTrackingLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20, // Max 20 requests per 15 min per IP
  message: 'Too many order tracking requests'
});

router.get('/orders/track', orderTrackingLimiter, orderController.trackOrder);
```

**2. Audit Logging**
```typescript
await auditLog.create({
  action: 'ORDER_ACCESS',
  customer_id: authenticatedCustomerId,
  order_id: order.order_number,
  owner_id: order.customer_id,
  success: order.customer_id === authenticatedCustomerId,
  ip_address: req.ip,
  timestamp: new Date()
});
```

### **Compliance Impact**
- **GDPR:** Unauthorized personal data disclosure
- **PDPA (Vietnam):** Personal data breach
- **PCI-DSS:** Payment information exposure risk

---

## 🔧 BUG #2: HIGH PRIORITY - Response Format Mismatch

### **Issue: Incorrect Field Names in API Response**

**Severity:** 🟠 HIGH  
**Type:** API Contract Violation  
**Impact:** Data Display Failure

### **Mô tả lỗi**
Backend trả về field names không khớp với API contract:
- Backend: `fulfillment_status`, `total_amount`
- Expected: `status`, `total`

Kết quả: Chatbot hiển thị "Unknown" và "N/A" dù data có trong response.

### **Current Response**
```json
{
  "success": true,
  "data": {
    "order_id": 32,
    "order_number": "0000000032",
    "fulfillment_status": "pending",   // ← Should also have "status"
    "payment_status": "unpaid",
    "total_amount": 500000,            // ← Should also have "total"
    "created_at": "2025-12-16T03:50:00.000Z",
    "items": [...]
  }
}
```

### **Chatbot Code (Expects)**
```python
# actions/actions.py:1533-1535
status = order.get("status", "Unknown")        # ❌ Not found
total = order.get("total", "N/A")              # ❌ Not found
```

### **UI Impact**
```
📦 Order #0000000032
📊 Status: Unknown        ❌ Should be "Pending"
📅 Placed on: N/A         ❌ Should be "Dec 16, 2025"
💰 Total: $N/A            ❌ Should be "500,000₫"
```

### **Solution: Add Field Aliases**

Thêm standardized field names vào response (backward compatible):

```typescript
return res.status(200).json({
  success: true,
  data: {
    order_id: order.id,
    order_number: order.order_number,
    customer_id: order.customer_id,
    
    // ✅ Add standardized aliases for chatbot compatibility
    status: order.fulfillment_status,           // ← Add this
    total: order.total_amount,                  // ← Add this
    date: order.created_at,                     // ← Optional
    
    // Keep detailed fields for other consumers
    fulfillment_status: order.fulfillment_status,
    payment_status: order.payment_status,
    total_amount: order.total_amount,
    
    created_at: order.created_at,
    updated_at: order.updated_at,
    shipping_address: order.shipping_address,
    tracking_number: order.tracking_number,
    items: order.items.map(item => ({
      product_id: item.product_id,
      product_name: item.variant?.product?.name,
      variant_id: item.variant_id,
      size: item.variant?.size,
      color: item.variant?.color,
      quantity: item.quantity,
      price: item.price,
      subtotal: item.quantity * item.price
    }))
  }
});
```

### **Benefits**
- ✅ Backward compatible (both old and new field names)
- ✅ Chatbot works immediately without code changes
- ✅ Frontend/other consumers can use either field name
- ✅ No breaking changes

### **Testing**
```bash
curl "http://localhost:3001/orders/track?order_id=0000000032" \
  -H "Authorization: Bearer <jwt>"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "order_id": 32,
    "order_number": "0000000032",
    "status": "pending",              // ✅ New alias
    "total": 500000,                  // ✅ New alias
    "fulfillment_status": "pending",  // ✅ Still available
    "total_amount": 500000,           // ✅ Still available
    ...
  }
}
```

### **UI After Fix**
```
📦 Order #0000000032
📊 Status: Pending | Payment: Unpaid  ✅
📅 Placed on: December 16, 2025      ✅
💰 Total: 500,000₫                   ✅
```

---

## 📊 Summary Table

| Bug ID | Severity | Issue | Impact | Fix Complexity |
|--------|----------|-------|--------|----------------|
| **#1** | 🚨 CRITICAL | No ownership verification | Customer data exposure | **Easy** (add 1 if check) |
| **#2** | 🟠 HIGH | Field name mismatch | UI shows N/A | **Easy** (add field aliases) |

---

## 🧪 Complete Testing Checklist

### **Bug #1: Security**
- [ ] Customer can view their own orders (200 OK)
- [ ] Customer **cannot** view other's orders (403 Forbidden)
- [ ] Security violations are logged
- [ ] Rate limiting prevents enumeration
- [ ] Penetration test passes

### **Bug #2: Response Format**
- [ ] Response includes both `status` and `fulfillment_status`
- [ ] Response includes both `total` and `total_amount`
- [ ] Chatbot displays correct status
- [ ] Chatbot displays correct total
- [ ] Chatbot displays formatted date

---

## 🚀 Deployment Priority

### **Phase 1: URGENT (Must Deploy Before Production)**
1. ✅ Fix Bug #1 (Security) - **CRITICAL - Deploy immediately**
2. ✅ Add rate limiting
3. ✅ Add audit logging

### **Phase 2: HIGH (Same Release)**
1. ✅ Fix Bug #2 (Field aliases)
2. ✅ Test chatbot integration
3. ✅ Verify all API consumers

### **Phase 3: Nice to Have**
1. Security monitoring dashboard
2. Automated security tests in CI/CD
3. API documentation update

---

## 📝 Files to Modify

| File | Changes Required | Priority |
|------|------------------|----------|
| `backend/src/controllers/order.controller.ts` | Add ownership check + field aliases | 🚨 CRITICAL |
| `backend/src/middleware/rateLimiter.ts` | Add order tracking rate limit | 🟠 HIGH |
| `backend/src/services/audit.service.ts` | Add order access logging | 🟠 HIGH |
| `backend/tests/orders.spec.ts` | Add security tests | 🟠 HIGH |

---

## 🔗 Related Documents
- **Detailed Security Report:** `BUG_REPORT_ORDER_SECURITY.md`
- **Detailed Format Report:** `BUG_REPORT_ORDER_RESPONSE_FORMAT.md`
- **Chatbot Fixes:** `actions/actions.py` (đã fix để handle cả 2 field names)

---

## ✅ Acceptance Criteria

### **Bug #1 Fixed When:**
- [ ] Customer chỉ xem được orders của mình
- [ ] Attempt xem order người khác → 403 Forbidden
- [ ] Security logs ghi lại violations
- [ ] Chatbot test: "0000000001" (của người khác) → "Order not found"

### **Bug #2 Fixed When:**
- [ ] Response có cả `status` và `fulfillment_status`
- [ ] Response có cả `total` và `total_amount`
- [ ] Chatbot test: "0000000032" → Hiển thị đầy đủ status, date, total
- [ ] Không có "Unknown" hoặc "N/A"

---

## 👨‍💻 Assigned To
**Backend Team - Orders Module**

**Estimated Effort:**
- Bug #1: 2-3 hours (code + test + review)
- Bug #2: 1 hour (add aliases + test)
- **Total:** 0.5 days

**Required Reviews:**
- Code review (security-focused)
- Security team approval
- QA regression testing

---

**🚨 URGENT: Bug #1 là security vulnerability nghiêm trọng. Cần fix và deploy ASAP!**

---

**END OF BUG REPORT**
