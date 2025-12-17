# 🚨 Backend API Request: Order Cancellation Endpoint

**Priority:** HIGH  
**Type:** NEW FEATURE  
**Module:** Orders Service  
**Reporter:** Chatbot Team  
**Date:** December 16, 2025

---

## 📋 Summary

Request for a new backend API endpoint to handle order cancellation requests with business rule validation and reason tracking. The chatbot needs to cancel orders only when they are in "pending" status, collect structured cancellation reasons, and provide appropriate responses for non-cancellable orders.

---

## 🎯 Business Requirements

### **Cancellation Rules**
1. **Only allow cancellation when `fulfillment_status = 'pending'`**
2. **Reject cancellation for:** `confirmed`, `shipping`, `delivered`, `cancelled`
3. **Track cancellation reason** for analytics and UX improvement
4. **Validate customer ownership** (authenticated user can only cancel their own orders)
5. **Return clear error messages** for each rejection scenario

### **User Stories**

**As a customer, I want to:**
- Cancel my order if it hasn't been processed yet
- Understand why I can't cancel if it's too late
- Get suggestions for alternative actions (return, refuse delivery)

**As a business, I want to:**
- Track why customers cancel orders
- Only allow cancellation before fulfillment starts
- Maintain data integrity and order state consistency

---

## 🔌 Requested API Endpoint

### **Endpoint**
```
POST /orders/{order_id}/cancel
```

### **Request Headers**
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
x-api-key: {internal_api_key}
```

### **Request Body**
```json
{
  "cancel_reason": "wrong_size_color"
}
```

### **Cancellation Reason Enum**
```typescript
enum CancelReason {
  CHANGED_MIND = 'changed_mind',
  ORDERED_WRONG_ITEM = 'ordered_wrong_item',
  WRONG_SIZE_COLOR = 'wrong_size_color',
  FOUND_BETTER_PRICE = 'found_better_price',
  DELIVERY_TOO_SLOW = 'delivery_too_slow',
  PAYMENT_ISSUE = 'payment_issue',
  DUPLICATE_ORDER = 'duplicate_order',
  OTHER = 'other'
}
```

---

## ✅ Success Response (200 OK)

**When order is successfully cancelled:**

```json
{
  "success": true,
  "message": "Order cancelled successfully",
  "order": {
    "order_id": 32,
    "order_number": "0000000032",
    "fulfillment_status": "cancelled",
    "cancelled_at": "2025-12-16T09:30:00.000Z",
    "cancel_reason": "wrong_size_color",
    "refund_status": "pending",
    "refund_amount": 26.24
  }
}
```

---

## ❌ Error Responses

### **1. Order Not Found (404)**
```json
{
  "success": false,
  "error": "ORDER_NOT_FOUND",
  "message": "Order #0000000032 not found",
  "suggestion": null
}
```

### **2. Unauthorized (403)**
```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "You are not authorized to cancel this order",
  "suggestion": "Please sign in or verify order ownership"
}
```

### **3. Order Already Confirmed (400)**
```json
{
  "success": false,
  "error": "CANNOT_CANCEL_CONFIRMED",
  "message": "This order has been confirmed and is waiting for delivery",
  "current_status": "confirmed",
  "suggestion": "You can refuse the package upon delivery or request a return after receiving it, according to our return policy"
}
```

### **4. Order Being Shipped (400)**
```json
{
  "success": false,
  "error": "CANNOT_CANCEL_SHIPPING",
  "message": "This order is currently being shipped",
  "current_status": "shipping",
  "tracking_number": "VN123456789",
  "carrier": "GHTK",
  "suggestion": "A common option is to refuse the delivery when the courier arrives, or initiate a return after the package is delivered"
}
```

### **5. Order Already Delivered (400)**
```json
{
  "success": false,
  "error": "CANNOT_CANCEL_DELIVERED",
  "message": "This order has already been delivered",
  "current_status": "delivered",
  "delivered_at": "2025-12-15T14:30:00.000Z",
  "suggestion": "You may request a return or refund according to our return policy if the product meets the conditions"
}
```

### **6. Order Already Cancelled (400)**
```json
{
  "success": false,
  "error": "ALREADY_CANCELLED",
  "message": "This order has already been cancelled",
  "current_status": "cancelled",
  "cancelled_at": "2025-12-14T10:00:00.000Z",
  "suggestion": null
}
```

### **7. Invalid Cancel Reason (400)**
```json
{
  "success": false,
  "error": "INVALID_CANCEL_REASON",
  "message": "Invalid cancellation reason provided",
  "valid_reasons": [
    "changed_mind",
    "ordered_wrong_item",
    "wrong_size_color",
    "found_better_price",
    "delivery_too_slow",
    "payment_issue",
    "duplicate_order",
    "other"
  ]
}
```

---

## 🗄️ Database Schema Updates

### **Orders Table - Add Columns**
```sql
ALTER TABLE orders ADD COLUMN cancelled_at TIMESTAMP NULL;
ALTER TABLE orders ADD COLUMN cancel_reason VARCHAR(50) NULL;
ALTER TABLE orders ADD COLUMN cancelled_by_customer_id INTEGER NULL;
ALTER TABLE orders ADD COLUMN refund_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN refund_amount DECIMAL(10,2) NULL;

-- Add foreign key for cancelled_by
ALTER TABLE orders 
ADD CONSTRAINT fk_cancelled_by_customer 
FOREIGN KEY (cancelled_by_customer_id) 
REFERENCES customers(id);

-- Add index for analytics queries
CREATE INDEX idx_orders_cancel_reason ON orders(cancel_reason);
CREATE INDEX idx_orders_cancelled_at ON orders(cancelled_at);
```

---

## 🔐 Backend Validation Logic

### **Step-by-step validation:**

```typescript
async cancelOrder(orderId: string, customerId: number, cancelReason: string) {
  // 1. Verify order exists
  const order = await this.findOrderById(orderId);
  if (!order) {
    throw new NotFoundException('Order not found');
  }

  // 2. Verify customer ownership
  if (order.customer_id !== customerId) {
    throw new ForbiddenException('Unauthorized to cancel this order');
  }

  // 3. Validate cancel reason
  const validReasons = ['changed_mind', 'ordered_wrong_item', 'wrong_size_color', 
                        'found_better_price', 'delivery_too_slow', 'payment_issue', 
                        'duplicate_order', 'other'];
  if (!validReasons.includes(cancelReason)) {
    throw new BadRequestException('Invalid cancellation reason');
  }

  // 4. Check if cancellable (ONLY pending)
  if (order.fulfillment_status !== 'pending') {
    const suggestions = {
      'confirmed': 'You can refuse the package upon delivery or request a return after receiving it',
      'shipping': 'You can refuse delivery when the courier arrives, or initiate a return after delivery',
      'delivered': 'You may request a return or refund according to our return policy',
      'cancelled': null
    };
    
    throw new BadRequestException({
      error: `CANNOT_CANCEL_${order.fulfillment_status.toUpperCase()}`,
      message: `Order cannot be cancelled in ${order.fulfillment_status} status`,
      current_status: order.fulfillment_status,
      suggestion: suggestions[order.fulfillment_status]
    });
  }

  // 5. Update order status
  order.fulfillment_status = 'cancelled';
  order.cancelled_at = new Date();
  order.cancel_reason = cancelReason;
  order.cancelled_by_customer_id = customerId;
  order.refund_status = 'pending';
  order.refund_amount = order.total_amount;

  await this.ordersRepository.save(order);

  // 6. Trigger refund process (if payment was made)
  if (order.payment_status === 'paid') {
    await this.refundService.initiateRefund(order.order_id, order.total_amount);
  }

  // 7. Send cancellation email
  await this.emailService.sendCancellationConfirmation(order);

  return {
    success: true,
    message: 'Order cancelled successfully',
    order: this.formatOrderResponse(order)
  };
}
```

---

## 📊 Analytics Requirements

### **Track these metrics:**
1. **Cancellation rate by reason** (pie chart)
2. **Time to cancel** (order created → cancelled)
3. **Most cancelled products/categories**
4. **Cancellation patterns** (time of day, day of week)

### **Sample Analytics Query**
```sql
SELECT 
  cancel_reason,
  COUNT(*) as total_cancellations,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders WHERE fulfillment_status = 'cancelled'), 2) as percentage
FROM orders
WHERE fulfillment_status = 'cancelled'
  AND cancelled_at >= NOW() - INTERVAL '30 days'
GROUP BY cancel_reason
ORDER BY total_cancellations DESC;
```

**Expected output:**
```
cancel_reason          | total_cancellations | percentage
-----------------------|---------------------|------------
changed_mind           | 45                  | 32.14%
wrong_size_color       | 38                  | 27.14%
found_better_price     | 25                  | 17.86%
delivery_too_slow      | 18                  | 12.86%
ordered_wrong_item     | 10                  | 7.14%
payment_issue          | 4                   | 2.86%
duplicate_order        | 0                   | 0.00%
other                  | 0                   | 0.00%
```

---

## 🧪 Test Cases

### **Test 1: Successful Cancellation (Pending Order)**
```bash
POST /orders/32/cancel
Authorization: Bearer {valid_jwt}
Body: { "cancel_reason": "wrong_size_color" }

Expected: 200 OK
Response: { "success": true, "order": { "fulfillment_status": "cancelled" } }
```

### **Test 2: Cannot Cancel (Confirmed Order)**
```bash
POST /orders/35/cancel
Body: { "cancel_reason": "changed_mind" }

Expected: 400 Bad Request
Response: { "error": "CANNOT_CANCEL_CONFIRMED", "suggestion": "refuse delivery or return" }
```

### **Test 3: Cannot Cancel (Shipping Order)**
```bash
POST /orders/40/cancel
Body: { "cancel_reason": "delivery_too_slow" }

Expected: 400 Bad Request
Response: { "error": "CANNOT_CANCEL_SHIPPING", "tracking_number": "VN123456" }
```

### **Test 4: Order Not Found**
```bash
POST /orders/99999/cancel

Expected: 404 Not Found
Response: { "error": "ORDER_NOT_FOUND" }
```

### **Test 5: Unauthorized (Different Customer)**
```bash
POST /orders/50/cancel
Authorization: Bearer {customer_2_jwt}  # Order belongs to customer_1

Expected: 403 Forbidden
Response: { "error": "UNAUTHORIZED" }
```

### **Test 6: Invalid Cancel Reason**
```bash
POST /orders/32/cancel
Body: { "cancel_reason": "invalid_reason_xyz" }

Expected: 400 Bad Request
Response: { "error": "INVALID_CANCEL_REASON", "valid_reasons": [...] }
```

### **Test 7: Already Cancelled Order**
```bash
POST /orders/32/cancel  # Already cancelled
Body: { "cancel_reason": "changed_mind" }

Expected: 400 Bad Request
Response: { "error": "ALREADY_CANCELLED" }
```

---

## 🎓 Academic Justification

**For KLTN Report:**

> The order cancellation feature implements strict business rule validation to ensure data consistency and prevent invalid state transitions. Cancellation is only permitted when the order status is "pending", verified through backend services rather than client-side logic. For orders that cannot be cancelled, the system provides contextual suggestions aligned with common e-commerce practices (package refusal, post-delivery returns).
>
> The collection of structured cancellation reasons enables data-driven analysis of customer behavior patterns, supporting continuous UX improvement. This approach balances user autonomy with business constraints, ensuring both customer satisfaction and operational integrity.

---

## 📝 Implementation Checklist

- [ ] Create `POST /orders/{id}/cancel` endpoint
- [ ] Add cancellation reason enum validation
- [ ] Implement status-based business logic
- [ ] Add database columns: `cancelled_at`, `cancel_reason`, `refund_status`, `refund_amount`
- [ ] Create database migration script
- [ ] Add customer ownership verification
- [ ] Implement refund trigger logic
- [ ] Add email notification for cancellation
- [ ] Write unit tests for all status scenarios
- [ ] Write integration tests for full flow
- [ ] Add analytics queries for cancellation tracking
- [ ] Update API documentation (Swagger)
- [ ] Test with chatbot integration

---

## 🔗 Related Endpoints

- `GET /orders/track?order_id={id}` - Get order details
- `POST /orders/{id}/return` - (Future) Return after delivery
- `GET /policies/return` - Return policy details

---

## 📞 Contact

**Questions?** Contact chatbot team or orders service maintainer.

**API Ready Date:** TBD  
**Chatbot Integration Date:** After API completion

---

## ✅ Acceptance Criteria

1. ✅ Cancellation succeeds ONLY when `fulfillment_status = 'pending'`
2. ✅ All other statuses return appropriate error with suggestion
3. ✅ Cancel reason is validated and stored
4. ✅ Customer ownership is verified
5. ✅ Refund is triggered for paid orders
6. ✅ Cancellation email is sent
7. ✅ Analytics queries work correctly
8. ✅ All test cases pass
9. ✅ API documentation is updated
10. ✅ Chatbot can successfully integrate and handle all scenarios

---

**End of Bug Report**
