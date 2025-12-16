# 🐛 BUG REPORT: Backend Order Tracking API - 404 Not Found

## Issue ID: BE-ORDER-002
**Severity:** HIGH  
**Component:** Backend API - Order Tracking Endpoint  
**Status:** OPEN  
**Date:** 2025-12-16

---

## 📋 Summary
Backend API endpoint `/orders/track` returns **404 Not Found** when chatbot attempts to retrieve order details with a valid order ID (`0933613058`) that exists in the database.

User is authenticated (customer_id: 1, JWT token present), but the order lookup fails with:
```json
{"message":"Không tìm thấy đơn hàng","error":"Not Found","statusCode":404}
```

---

## 🔍 Problem Analysis

### Chatbot Logs (Correct ✅)
```
2025-12-16 10:24:50 INFO  - 🔢 Order number extracted: 0933613058
2025-12-16 10:24:50 INFO  - ✅ Got customer_id from metadata: 1
2025-12-16 10:24:50 INFO  - 🔐 User authenticated - customer_id: 1
2025-12-16 10:24:50 INFO  - Tracking order by number: 0933613058
2025-12-16 10:24:50 INFO  - Fetching order details for order: 0933613058
2025-12-16 10:24:51 ERROR - HTTP Error: 404 - {"message":"Không tìm thấy đơn hàng","error":"Not Found","statusCode":404}
```

### API Request Details
**Endpoint:** `GET http://localhost:3001/orders/track?order_id=0933613058`  
**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```
**Response:**
```json
{
  "message": "Không tìm thấy đơn hàng",
  "error": "Not Found",
  "statusCode": 404
}
```

### Expected vs Actual

**Expected:**
```json
{
  "success": true,
  "data": {
    "order_id": "0933613058",
    "customer_id": 1,
    "status": "pending",
    "created_at": "2025-12-16T...",
    "total": 500000,
    "items": [...]
  }
}
```

**Actual:** 404 Not Found ❌

---

## 🔎 Root Cause Analysis

**Possible Causes:**

### 1. Missing API Endpoint ❌
Endpoint `/orders/track` chưa được implement trong backend.

**Check:**
```bash
# Backend routing files
ls backend/src/routes/order*.ts
cat backend/src/routes/orders.routes.ts
```

Look for:
```typescript
router.get('/track', ...);  // ← This route might be missing
```

### 2. Incorrect Query Parameter Format ❌
Endpoint expects different parameter name or format.

**Chatbot sends:** `?order_id=0933613058`  
**Backend expects:** `?orderId=0933613058` hoặc `?order_number=0933613058`

### 3. Database Order ID Mismatch ❌
Order ID trong database có format khác:
- Database: `"#0933613058"` (với # prefix)
- Chatbot gửi: `"0933613058"` (không có #)

### 4. Missing Authentication Check ❌
Endpoint không verify customer_id trong JWT match với order's customer_id.

### 5. Wrong HTTP Method ❌
Endpoint implemented với POST thay vì GET.

---

## ✅ Required Implementation

### **Backend File:** `backend/src/routes/orders.routes.ts`

```typescript
import { Router } from 'express';
import { authenticate } from '../middleware/auth.middleware';
import { OrderController } from '../controllers/order.controller';

const router = Router();
const orderController = new OrderController();

/**
 * GET /orders/track
 * Track order by order_id (public) or customer's orders (authenticated)
 * 
 * Query params:
 *   - order_id: string (required) - Order number or ID
 * 
 * Headers:
 *   - Authorization: Bearer <JWT> (optional)
 * 
 * Returns:
 *   - Order details if found
 *   - 404 if order not found
 *   - 403 if order belongs to different customer (when authenticated)
 */
router.get('/track', orderController.trackOrder);

export default router;
```

### **Backend File:** `backend/src/controllers/order.controller.ts`

```typescript
import { Request, Response } from 'express';
import { OrderService } from '../services/order.service';

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

      // Clean order_id - remove # if present
      const cleanOrderId = order_id.replace(/^#/, '');

      // Get customer_id from JWT if authenticated
      const customerId = req.user?.id; // Assuming auth middleware sets req.user

      // Find order by ID
      const order = await this.orderService.findByOrderNumber(cleanOrderId);

      if (!order) {
        return res.status(404).json({
          success: false,
          message: 'Không tìm thấy đơn hàng',
          error: 'Not Found'
        });
      }

      // Security: If user is authenticated, verify ownership
      if (customerId && order.customer_id !== customerId) {
        return res.status(403).json({
          success: false,
          message: 'Bạn không có quyền xem đơn hàng này',
          error: 'Forbidden'
        });
      }

      // Return order details
      return res.status(200).json({
        success: true,
        data: {
          order_id: order.order_number,
          customer_id: order.customer_id,
          status: order.status,
          created_at: order.created_at,
          updated_at: order.updated_at,
          total: order.total,
          shipping_address: order.shipping_address,
          items: order.items.map(item => ({
            product_id: item.product_id,
            product_name: item.product_name,
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

### **Backend File:** `backend/src/services/order.service.ts`

```typescript
import { Order } from '../models/order.model';

export class OrderService {
  /**
   * Find order by order number
   * Handles both formats: "0933613058" and "#0933613058"
   */
  async findByOrderNumber(orderNumber: string): Promise<Order | null> {
    // Try exact match first
    let order = await Order.findOne({
      where: { order_number: orderNumber }
    });

    // If not found, try with # prefix
    if (!order) {
      order = await Order.findOne({
        where: { order_number: `#${orderNumber}` }
      });
    }

    // If not found, try without # prefix
    if (!order && orderNumber.startsWith('#')) {
      order = await Order.findOne({
        where: { order_number: orderNumber.substring(1) }
      });
    }

    return order;
  }
}
```

---

## 🧪 Testing Steps

### **1. Create Test Order in Database**
```sql
INSERT INTO orders (order_number, customer_id, status, total, created_at)
VALUES ('0933613058', 1, 'pending', 500000, NOW());
```

### **2. Test API Directly**
```bash
# Without auth (public tracking)
curl -X GET "http://localhost:3001/orders/track?order_id=0933613058"

# With auth (customer verification)
curl -X GET "http://localhost:3001/orders/track?order_id=0933613058" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "order_id": "0933613058",
    "customer_id": 1,
    "status": "pending",
    "created_at": "2025-12-16T...",
    "total": 500000,
    "items": []
  }
}
```

### **3. Test via Chatbot**
```
User: "can i view my order?"
Bot: "Please provide your order number..."
User: "my order number is 0933613058"
Bot: "📦 Order #0933613058 - Status: pending - Total: 500,000₫"
```

---

## 📊 Impact

**Affected Features:**
- ❌ Order tracking via chatbot
- ❌ Order status inquiry
- ❌ Order cancellation (requires order details first)
- ❌ Return/Exchange requests (requires order lookup)
- ❌ Quality issue reporting (requires order verification)

**User Experience:**
- Users cannot track orders despite providing valid order numbers
- Chatbot appears broken: "Sorry, I couldn't find order..."
- Major blocker for customer service automation

**Business Impact:**
- Increased customer support workload (manual order tracking)
- Reduced chatbot utility
- Poor user experience

---

## 🔧 Chatbot Side - Already Correct ✅

**Chatbot API client implementation:**
```python
# actions/api_client.py:204-223
def get_order_details(self, order_id: str, auth_token: str = None):
    """Get order details for a specific order"""
    logger.info(f"Fetching order details for order: {order_id}")
    params = {"order_id": order_id}
    return self._make_request(
        "GET", 
        "/orders/track",  # ✅ Correct endpoint
        params=params,
        auth_token=auth_token  # ✅ JWT included
    )
```

**Chatbot is ready** - waiting for backend endpoint implementation.

---

## 📌 Priority Justification

**HIGH Priority** because:
1. Core e-commerce feature completely broken
2. Affects multiple user flows (tracking, cancellation, returns)
3. Authentication is working, NLU is working - only API missing
4. Straightforward implementation (single endpoint)
5. Blocking production deployment

---

## 🔗 Alternative Endpoint (If /orders/track doesn't exist)

**Check if backend has different endpoint:**

### Option 1: GET /orders/:orderId
```typescript
router.get('/:orderId', authenticate, orderController.getOrderById);
```

**Chatbot needs to change to:**
```python
def get_order_details(self, order_id: str, auth_token: str):
    return self._make_request(
        "GET", 
        f"/orders/{order_id}",  # Path param instead of query
        auth_token=auth_token
    )
```

### Option 2: GET /orders (list all user orders)
```typescript
router.get('/', authenticate, orderController.getUserOrders);
```

**Chatbot needs to filter client-side:**
```python
def get_order_details(self, order_id: str, auth_token: str):
    result = self._make_request("GET", "/orders", auth_token=auth_token)
    orders = result.get("data", [])
    order = next((o for o in orders if o["order_number"] == order_id), None)
    if not order:
        return {"error": "Order not found"}
    return {"data": order}
```

---

## 👨‍💻 Assigned To
**Backend Team** - Orders API Module

## ✅ Acceptance Criteria
- [ ] `/orders/track?order_id=<ID>` endpoint exists and returns 200
- [ ] Endpoint accepts both `0933613058` and `#0933613058` formats
- [ ] Returns order details when order exists
- [ ] Returns 404 with clear message when order not found
- [ ] Verifies customer ownership when JWT provided
- [ ] Chatbot successfully retrieves and displays order info
- [ ] Order tracking works end-to-end in production

---

## 📎 Additional Context

**Database Schema Check:**
```sql
-- Check how order_number is stored in DB
SELECT order_number, customer_id, status, total, created_at 
FROM orders 
WHERE customer_id = 1
LIMIT 5;

-- Check if order exists with different format
SELECT order_number FROM orders 
WHERE order_number LIKE '%0933613058%';
```

**Expected Output:**
```
order_number  | customer_id | status   | total  | created_at
0933613058    | 1           | pending  | 500000 | 2025-12-16 10:00:00
```

---

**END OF BUG REPORT**
