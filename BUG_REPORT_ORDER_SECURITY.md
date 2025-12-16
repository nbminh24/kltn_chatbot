# 🚨 CRITICAL BUG: Order Tracking Security Vulnerability

## Issue ID: BE-ORDER-SECURITY-001
**Severity:** CRITICAL 🔴  
**Component:** Backend API - Order Tracking Endpoint  
**Status:** OPEN  
**Date:** 2025-12-16  
**Security Impact:** HIGH - Customer can view other customers' orders

---

## 📋 Summary
Backend endpoint `/orders/track` **does not verify customer ownership** before returning order details. Any authenticated user can view ANY order by providing the order number, regardless of who placed the order.

**Example:**
- Customer ID 1 (nbminh24@gmail.com) successfully retrieved Order #0000000001
- Order #0000000001 belongs to a DIFFERENT customer
- No authorization check was performed

This is a **critical privacy/security violation** allowing customers to access other customers' personal data (orders, addresses, purchase history).

---

## 🔍 Proof of Vulnerability

### Test Case
**Logged-in User:** Customer ID 1 (nbminh24@gmail.com)  
**Requested Order:** #0000000001 (belongs to another customer)  
**Expected:** 403 Forbidden - "This order belongs to another account"  
**Actual:** ✅ 200 OK - Order details returned successfully ❌

### Frontend Logs
```
[ChatStore] Session: customer_id: 1
[ChatStore] Send message: "my order number is 0000000001"

Bot Response:
📦 Order #0000000001
📊 Status: Unknown
📅 Placed on: N/A
💰 Total: $N/A
Is there anything else you'd like to know about your order?
```

**Status:** Order was found and returned (no 404 or 403 error)

### Backend API Request
```http
GET /orders/track?order_id=0000000001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5ibWluaDI0QGdtYWlsLmNvbSIsInN1YiI6MSwiaWF0IjoxNzY1ODU2NTk0LCJleHAiOjE3NjU4NTc0OTR9.Lx-41ki56S8rg5ni3KnVJJHDE3wM86sR7gJZZYXTQIE

JWT Payload:
{
  "email": "nbminh24@gmail.com",
  "sub": 1,  // customer_id = 1
  "iat": 1765856594,
  "exp": 1765857494
}
```

**Backend Response:** 200 OK (should be 403 Forbidden)

---

## ⚠️ Security Impact

### **Data Exposure Risk**
Malicious users can:
1. Enumerate order IDs (0000000001, 0000000002, ...)
2. Access other customers' order details:
   - Full name & shipping address
   - Phone number
   - Products purchased
   - Order total & payment status
   - Order history & purchase patterns

### **Attack Scenario**
```bash
# Attacker script to scrape all orders
for order_id in {1..10000}; do
  padded_id=$(printf "%010d" $order_id)
  curl "http://localhost:3001/orders/track?order_id=$padded_id" \
    -H "Authorization: Bearer <ANY_VALID_JWT>"
done
```

Result: Attacker downloads **entire order database** with customer PII.

### **Compliance Violations**
- **GDPR:** Unauthorized disclosure of personal data
- **PDPA (Vietnam):** Personal data breach
- **PCI-DSS:** Exposure of payment-related information

---

## 🐛 Root Cause

**Backend File:** `backend/src/services/orders.service.ts`  
**Method:** `trackOrder` or `findByOrderNumber`

**Current Implementation (Incorrect):**
```typescript
async trackOrder(order_id: string): Promise<Order> {
  const orderIdStr = order_id.toString().replace(/^#/, '');
  
  // ❌ NO CUSTOMER_ID VERIFICATION
  const order = await this.orderRepository.findOne({
    where: { order_number: orderIdStr },
    relations: ['items', 'items.variant', 'items.variant.product'],
  });
  
  if (!order) {
    throw new NotFoundException('Không tìm thấy đơn hàng');
  }
  
  // ❌ Returns order WITHOUT checking if it belongs to the requester
  return order;
}
```

**Missing:** Authorization check to verify `order.customer_id === authenticatedUser.customer_id`

---

## ✅ Required Fix

### **Backend File:** `backend/src/controllers/order.controller.ts`

```typescript
import { Request, Response } from 'express';
import { OrderService } from '../services/order.service';
import { UnauthorizedException, NotFoundException } from '@nestjs/common';

export class OrderController {
  private orderService: OrderService;

  constructor() {
    this.orderService = new OrderService();
  }

  async trackOrder(req: Request, res: Response) {
    try {
      const { order_id } = req.query;
      
      if (!order_id || typeof order_id !== 'string') {
        return res.status(400).json({
          success: false,
          error: 'Order ID is required'
        });
      }

      // Get authenticated customer_id from JWT
      const authenticatedCustomerId = req.user?.id; // From auth middleware
      
      if (!authenticatedCustomerId) {
        return res.status(401).json({
          success: false,
          message: 'Authentication required',
          error: 'Unauthorized'
        });
      }

      const cleanOrderId = order_id.replace(/^#/, '');
      
      // Find order
      const order = await this.orderService.findByOrderNumber(cleanOrderId);
      
      if (!order) {
        return res.status(404).json({
          success: false,
          message: 'Không tìm thấy đơn hàng',
          error: 'Not Found'
        });
      }

      // ✅ CRITICAL: Verify customer ownership
      if (order.customer_id !== authenticatedCustomerId) {
        console.warn(
          `[SECURITY] Customer ${authenticatedCustomerId} attempted to access order ${order.order_number} belonging to customer ${order.customer_id}`
        );
        
        return res.status(403).json({
          success: false,
          message: 'Bạn không có quyền xem đơn hàng này',
          error: 'Forbidden'
        });
      }

      // Return order details only if ownership verified
      return res.status(200).json({
        success: true,
        data: {
          order_id: order.id,
          order_number: order.order_number,
          customer_id: order.customer_id,
          fulfillment_status: order.fulfillment_status,
          payment_status: order.payment_status,
          created_at: order.created_at,
          updated_at: order.updated_at,
          total_amount: order.total_amount,
          shipping_address: order.shipping_address,
          tracking_number: order.tracking_number,
          items: order.items.map(item => ({
            product_id: item.product_id,
            product_name: item.variant?.product?.name,
            variant_id: item.variant_id,
            quantity: item.quantity,
            price: item.price
          }))
        }
      });
    } catch (error) {
      console.error('[OrderController] Track order error:', error);
      return res.status(500).json({
        success: false,
        message: 'Lỗi server',
        error: 'Internal Server Error'
      });
    }
  }
}
```

### **Key Changes:**
1. ✅ Extract `authenticatedCustomerId` from JWT (`req.user.id`)
2. ✅ Find order by order_number
3. ✅ **Verify `order.customer_id === authenticatedCustomerId`**
4. ✅ Return 403 Forbidden if ownership verification fails
5. ✅ Log security violations for monitoring

---

## 🧪 Testing Steps

### **1. Prepare Test Data**
```sql
-- Create test customers
INSERT INTO customers (id, name, email) VALUES
  (1, 'Customer One', 'customer1@test.com'),
  (2, 'Customer Two', 'customer2@test.com');

-- Create orders for different customers
INSERT INTO orders (id, order_number, customer_id, total_amount, fulfillment_status, created_at)
VALUES
  (1, '0000000001', 2, 500000, 'pending', NOW()),  -- Belongs to Customer 2
  (2, '0000000002', 1, 750000, 'shipped', NOW());  -- Belongs to Customer 1
```

### **2. Test Legitimate Access (Should Succeed)**
```bash
# Login as Customer 1
TOKEN_CUSTOMER_1="<JWT for customer 1>"

# Customer 1 accessing their own order
curl -X GET "http://localhost:3001/orders/track?order_id=0000000002" \
  -H "Authorization: Bearer $TOKEN_CUSTOMER_1"

# Expected: 200 OK with order details
```

### **3. Test Unauthorized Access (Should Fail)**
```bash
# Customer 1 trying to access Customer 2's order
curl -X GET "http://localhost:3001/orders/track?order_id=0000000001" \
  -H "Authorization: Bearer $TOKEN_CUSTOMER_1"

# Expected Response:
{
  "success": false,
  "message": "Bạn không có quyền xem đơn hàng này",
  "error": "Forbidden"
}
# Expected Status: 403 Forbidden
```

### **4. Test via Chatbot**
```
User (Customer 1): "my order number is 0000000001"
Bot: "Sorry, I couldn't find that order. Please verify the order number."

User (Customer 1): "my order number is 0000000002"
Bot: "📦 Order #0000000002 - Status: shipped - Total: 750,000₫"
```

---

## 📊 Impact Assessment

### **Before Fix (Current State)**
| Test Case | Customer ID | Order Number | Order Owner | Result | Expected |
|-----------|-------------|--------------|-------------|---------|----------|
| Own order | 1 | 0000000002 | Customer 1 | ✅ 200 OK | ✅ 200 OK |
| **Other's order** | **1** | **0000000001** | **Customer 2** | **✅ 200 OK** ❌ | **🚫 403 Forbidden** |

### **After Fix**
| Test Case | Customer ID | Order Number | Order Owner | Result | Expected |
|-----------|-------------|--------------|-------------|---------|----------|
| Own order | 1 | 0000000002 | Customer 1 | ✅ 200 OK | ✅ 200 OK |
| **Other's order** | **1** | **0000000001** | **Customer 2** | **🚫 403 Forbidden** | **🚫 403 Forbidden** ✅ |

---

## 🔒 Additional Security Recommendations

### **1. Rate Limiting**
```typescript
// Prevent order enumeration attacks
import rateLimit from 'express-rate-limit';

const orderTrackingLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20, // Max 20 requests per 15 min
  message: 'Too many order tracking requests, please try again later'
});

router.get('/orders/track', orderTrackingLimiter, orderController.trackOrder);
```

### **2. Audit Logging**
```typescript
// Log all order access attempts
await auditLogger.log({
  action: 'ORDER_ACCESS',
  customer_id: authenticatedCustomerId,
  order_id: order.order_number,
  timestamp: new Date(),
  success: order.customer_id === authenticatedCustomerId
});
```

### **3. Security Monitoring**
```typescript
// Alert on suspicious patterns
if (failedAttempts > 5) {
  securityAlert.notify({
    severity: 'HIGH',
    message: `Customer ${customerId} attempted to access ${failedAttempts} unauthorized orders`,
    action: 'Consider account suspension'
  });
}
```

---

## 📌 Priority Justification

**CRITICAL Priority** because:
1. **Active security vulnerability** exposing customer PII
2. **GDPR/PDPA compliance violation** - potential legal liability
3. **Easy to exploit** - no special tools required
4. **High impact** - affects all customers and all orders
5. **Immediate fix required** - single authorization check

---

## ✅ Acceptance Criteria
- [ ] Backend verifies `order.customer_id === req.user.id` before returning data
- [ ] Unauthorized access returns 403 Forbidden with clear error message
- [ ] Security violations are logged for monitoring
- [ ] Customers can only access their own orders
- [ ] Chatbot correctly handles 403 responses
- [ ] Penetration testing confirms vulnerability is fixed
- [ ] Rate limiting implemented to prevent enumeration

---

## 👨‍💻 Assigned To
**Backend Team - URGENT**  
**Requires:** Code review + security audit before deployment

---

**END OF SECURITY BUG REPORT**
