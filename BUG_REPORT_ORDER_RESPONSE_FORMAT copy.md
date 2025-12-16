# 🐛 BUG REPORT: Order Details Response - Incorrect Field Names

## Issue ID: BE-ORDER-003
**Severity:** HIGH  
**Component:** Backend API - Order Tracking Response Format  
**Status:** OPEN  
**Date:** 2025-12-16

---

## 📋 Summary
Backend endpoint `/orders/track` returns order data with field names that don't match the expected API contract. The chatbot expects `status`, `created_at`, `total` but the backend returns `fulfillment_status`, `created_at`, `total_amount`, causing the chatbot to display "Unknown" and "N/A" values.

**Impact:** Users see incomplete order information despite the data existing in the backend.

---

## 🔍 Problem Analysis

### **Chatbot Expectation (Current Code)**
```python
# actions/actions.py:1530-1533
order = result.get("data", {})
status = order.get("status", "Unknown")        # ❌ Looking for "status"
created_at = order.get("created_at", "N/A")    # ✅ Correct
total = order.get("total", "N/A")              # ❌ Looking for "total"
```

### **Backend Response (Actual)**
Based on the backend implementation mentioned in previous context:
```json
{
  "success": true,
  "data": {
    "order_id": 1,
    "order_number": "0000000001",
    "customer_id": 1,
    "fulfillment_status": "pending",     // ← Not "status"
    "payment_status": "unpaid",
    "created_at": "2025-12-16T...",      // ✅ Correct
    "updated_at": "2025-12-16T...",
    "total_amount": 500000,              // ← Not "total"
    "shipping_address": {...},
    "tracking_number": null,
    "items": [...]
  }
}
```

### **Result**
```
📦 Order #0000000001
📊 Status: Unknown          // Should be "pending"
📅 Placed on: N/A          // Should show the date
💰 Total: $N/A             // Should be "500000"
```

---

## 🎯 Expected vs Actual

| Field Chatbot Expects | Field Backend Returns | Value Example | Status |
|----------------------|----------------------|---------------|---------|
| `status` | `fulfillment_status` | "pending" | ❌ Mismatch |
| `created_at` | `created_at` | "2025-12-16T10:50:24Z" | ✅ Match |
| `total` | `total_amount` | 500000 | ❌ Mismatch |
| N/A | `payment_status` | "unpaid" | Missing from chatbot |
| `tracking_number` | `tracking_number` | null | ✅ Match |

---

## 🔧 Solution Options

### **Option 1: Backend Standardizes Response (Recommended)**
**Modify backend to return fields matching the original API contract:**

```typescript
// backend/src/controllers/order.controller.ts
return res.status(200).json({
  success: true,
  data: {
    order_id: order.id,
    order_number: order.order_number,
    customer_id: order.customer_id,
    
    // ✅ Add standardized fields for chatbot compatibility
    status: order.fulfillment_status,        // Map fulfillment_status → status
    total: order.total_amount,               // Map total_amount → total
    
    // Keep detailed fields for other consumers
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
```

**Benefits:**
- ✅ Backward compatible (includes both old and new field names)
- ✅ Chatbot works without code changes
- ✅ Frontend/other consumers can use either field name

---

### **Option 2: Chatbot Adapts to Backend (Temporary Fix)**
**Modify chatbot to read backend's current field names:**

```python
# actions/actions.py
order = result.get("data", {})

# Try new field names first, fallback to old names
status = order.get("fulfillment_status") or order.get("status", "Unknown")
total = order.get("total_amount") or order.get("total", "N/A")
created_at = order.get("created_at", "N/A")

# Additional info
payment_status = order.get("payment_status", "Unknown")
```

**Benefits:**
- ✅ Quick fix for chatbot
- ✅ Works with current backend

**Drawbacks:**
- ❌ Every API consumer must adapt
- ❌ API contract inconsistency

---

## 📝 Recommended Implementation

### **Backend Change (Preferred)**

**File:** `backend/src/controllers/order.controller.ts`

```typescript
async trackOrder(req: Request, res: Response) {
  try {
    const { order_id } = req.query;
    const authenticatedCustomerId = req.user?.id;

    // ... validation & ownership check ...

    const order = await this.orderService.findByOrderNumber(cleanOrderId);

    if (!order) {
      return res.status(404).json({
        success: false,
        message: 'Không tìm thấy đơn hàng',
        error: 'Not Found'
      });
    }

    if (order.customer_id !== authenticatedCustomerId) {
      return res.status(403).json({
        success: false,
        message: 'Bạn không có quyền xem đơn hàng này',
        error: 'Forbidden'
      });
    }

    // ✅ Return with BOTH standardized and detailed fields
    return res.status(200).json({
      success: true,
      data: {
        order_id: order.id,
        order_number: order.order_number,
        customer_id: order.customer_id,
        
        // Standardized fields for chatbot/simple consumers
        status: order.fulfillment_status,           // ← Add this
        total: order.total_amount,                  // ← Add this
        date: order.created_at,                     // ← Optional alias
        
        // Detailed fields for advanced consumers
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
  } catch (error) {
    console.error('[OrderController] Track order error:', error);
    return res.status(500).json({
      success: false,
      message: 'Lỗi server',
      error: 'Internal Server Error'
    });
  }
}
```

---

## 🧪 Testing

### **Test API Response Structure**
```bash
curl -X GET "http://localhost:3001/orders/track?order_id=0000000032" \
  -H "Authorization: Bearer <JWT>"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "order_id": 32,
    "order_number": "0000000032",
    "customer_id": 1,
    
    "status": "pending",              // ✅ Chatbot can read this
    "total": 500000,                  // ✅ Chatbot can read this
    
    "fulfillment_status": "pending",  // ✅ Frontend can read this
    "payment_status": "unpaid",
    "total_amount": 500000,
    
    "created_at": "2025-12-16T03:50:00.000Z",
    "updated_at": "2025-12-16T03:50:00.000Z",
    "tracking_number": null,
    "items": [...]
  }
}
```

### **Test Chatbot Display**
```
User: "my order number is 0000000032"

Expected Bot Response:
📦 Order #0000000032
📊 Status: pending
📅 Placed on: 2025-12-16T03:50:00.000Z
💰 Total: $500000
```

---

## 📊 Impact

### **Before Fix**
```
📦 Order #0000000032
📊 Status: Unknown        ❌
📅 Placed on: N/A         ❌
💰 Total: $N/A            ❌
```

### **After Fix**
```
📦 Order #0000000032
📊 Status: pending        ✅
📅 Placed on: 2025-12-16  ✅
💰 Total: 500,000₫        ✅
```

---

## 🔗 Related Issues
- **BE-ORDER-SECURITY-001:** Customer ownership verification (CRITICAL)
- **BE-ORDER-002:** Order tracking endpoint implementation (RESOLVED)

---

## ✅ Acceptance Criteria
- [ ] Backend returns both `status` and `fulfillment_status` fields
- [ ] Backend returns both `total` and `total_amount` fields
- [ ] Chatbot displays correct order status
- [ ] Chatbot displays correct order total
- [ ] Chatbot displays formatted date
- [ ] Response structure is backward compatible

---

## 📌 Priority
**HIGH Priority** because:
1. Chatbot displays incomplete information to customers
2. Poor user experience (shows "Unknown" and "N/A")
3. Simple fix (add field aliases)
4. Blocks production deployment

---

## 👨‍💻 Assigned To
**Backend Team** - Orders API Module

---

**END OF BUG REPORT**
