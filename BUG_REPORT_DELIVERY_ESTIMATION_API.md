# Backend API Request: Order Delivery Estimation

## 📋 Feature Request Summary

**Request Type:** New API Endpoint  
**Priority:** Medium  
**Component:** Orders Module  
**Requested by:** Chatbot Team  
**Date:** 2025-12-16

---

## 🎯 Business Requirement

Enable the chatbot to provide customers with **estimated delivery dates** for their orders based on:
- Order creation date
- Shipping method (standard, express, next_day)
- Destination location
- Current order status

**Key Principle:** The chatbot should **NOT** calculate delivery dates autonomously. All date calculations must be performed by the backend to ensure accuracy and consistency.

---

## 📝 Required API Endpoint

### **Endpoint 1: Get Order Delivery Estimation**

```
GET /orders/track/delivery-estimation
```

**Query Parameters:**
- `order_id` (string, required): Order number (e.g., "0000000032")

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`
- `x-api-key: <API_KEY>`

**Success Response (200 OK):**

```json
{
  "order_id": 32,
  "order_number": "0000000032",
  "status": "shipping",
  "shipping_method": "standard",
  "destination": {
    "city": "Ho Chi Minh City",
    "district": "District 1",
    "is_major_city": true
  },
  "estimated_delivery": {
    "from": "2025-03-18",
    "to": "2025-03-20",
    "date": "2025-03-19",
    "formatted": "March 19, 2025"
  },
  "tracking_url": "https://carrier.vn/track/XYZ123",
  "delivery_status_message": "Your order is on the way"
}
```

**Alternative Response (If order not shipped yet):**

```json
{
  "order_id": 32,
  "order_number": "0000000032",
  "status": "pending",
  "estimated_delivery": null,
  "message": "Your order has not been shipped yet. Estimated delivery date will be available once the order is confirmed and shipped."
}
```

**Error Responses:**

```json
// 404 - Order Not Found
{
  "error": "ORDER_NOT_FOUND",
  "message": "Order not found or does not belong to this customer"
}

// 401 - Unauthorized
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

---

## 🧮 Delivery Estimation Logic

### **Business Days Calculation Rules**

1. **Exclude Weekends:** Do not count Sundays
2. **Business Hours:** Orders placed after 2 PM are considered next business day
3. **Optional (Advanced):** Exclude Vietnamese public holidays

### **Shipping Methods & Timeframes**

#### **Domestic Shipping (Vietnam)**

| Location Type | Standard Delivery | Express Delivery | Next Day Delivery |
|--------------|------------------|------------------|-------------------|
| Major Cities (Hanoi, HCMC, Da Nang) | 1-2 business days | 1 business day | Next business day (if ordered by 2PM) |
| Other Provinces | 3-5 business days | 2 business days | Not available |

#### **International Shipping**

| Region | Standard Delivery | Express Available |
|--------|------------------|-------------------|
| Asia (Thailand, Singapore, Malaysia, etc.) | 5-7 business days | Yes (+$15 fee) |
| Rest of World | 10-14 business days | Yes (+$25 fee) |

### **Pseudo-code for Backend Implementation**

```typescript
function estimateDeliveryDate(
  orderDate: Date,
  shippingMethod: string,
  location: Location
): DeliveryEstimate {
  let minDays: number;
  let maxDays: number;

  // Determine delivery timeframe based on method and location
  if (shippingMethod === "standard") {
    if (location.isMajorCity) {
      minDays = 1;
      maxDays = 2;
    } else {
      minDays = 3;
      maxDays = 5;
    }
  } else if (shippingMethod === "express") {
    minDays = 1;
    maxDays = location.isMajorCity ? 1 : 2;
  } else if (shippingMethod === "next_day") {
    // Check if order was placed before 2 PM
    const orderHour = orderDate.getHours();
    minDays = orderHour < 14 ? 1 : 2;
    maxDays = minDays;
  }

  // Calculate business days (excluding Sundays)
  const fromDate = addBusinessDays(orderDate, minDays);
  const toDate = addBusinessDays(orderDate, maxDays);
  const estimatedDate = addBusinessDays(orderDate, Math.ceil((minDays + maxDays) / 2));

  return {
    from: fromDate.toISOString().split('T')[0],
    to: toDate.toISOString().split('T')[0],
    date: estimatedDate.toISOString().split('T')[0],
    formatted: formatDate(estimatedDate, 'MMMM DD, YYYY')
  };
}

function addBusinessDays(startDate: Date, daysToAdd: number): Date {
  let currentDate = new Date(startDate);
  let daysAdded = 0;

  while (daysAdded < daysToAdd) {
    currentDate.setDate(currentDate.getDate() + 1);
    
    // Skip Sundays (day 0)
    if (currentDate.getDay() !== 0) {
      daysAdded++;
    }
  }

  return currentDate;
}
```

---

## 🗄️ Database Schema Updates (If Needed)

### **Option 1: Add fields to `orders` table**

```sql
ALTER TABLE orders 
ADD COLUMN shipping_method VARCHAR(50) DEFAULT 'standard',
ADD COLUMN estimated_delivery_from DATE,
ADD COLUMN estimated_delivery_to DATE,
ADD COLUMN actual_delivery_date DATE,
ADD COLUMN tracking_number VARCHAR(100),
ADD COLUMN carrier_name VARCHAR(100);
```

### **Option 2: Use existing `order_status_history` table**

Track shipping events and calculate delivery dates dynamically based on:
- `created_at` timestamp from `orders` table
- `status` from `order_status_history` where `status = 'shipping'`
- Location data from `shipping_city`, `shipping_district`, `shipping_ward`

---

## 🔒 Security Requirements

1. **Customer Ownership Verification:**
   - Verify JWT token `customer_id` matches `orders.customer_id`
   - Return 404 (not 403) if order doesn't belong to customer

2. **API Key Authentication:**
   - Require both JWT token AND API key for internal chatbot calls

3. **Rate Limiting:**
   - Implement rate limiting to prevent abuse

---

## 📊 Response Status Mapping

| Order Status | `estimated_delivery` | `message` |
|-------------|---------------------|-----------|
| `pending` | `null` | "Your order is pending confirmation. Delivery date will be available once confirmed." |
| `confirmed` | `null` | "Your order is confirmed and being prepared. Delivery estimate will be available once shipped." |
| `shipping` | `{from, to, date}` | "Your order is on the way." |
| `delivered` | `{actual_date}` | "Your order was delivered on {date}." |
| `cancelled` | `null` | "This order has been cancelled." |

---

## 🧪 Testing Scenarios

### **Test Case 1: Order Shipped - Major City**
```
Order Date: 2025-03-15 10:00 AM
Status: shipping
Method: standard
Location: Ho Chi Minh City (major city)
Expected: delivery 2025-03-16 to 2025-03-17 (1-2 business days)
```

### **Test Case 2: Order Shipped - Province**
```
Order Date: 2025-03-15 10:00 AM
Status: shipping
Method: standard
Location: Can Tho (province)
Expected: delivery 2025-03-18 to 2025-03-22 (3-5 business days)
```

### **Test Case 3: Next Day - Ordered After 2PM**
```
Order Date: 2025-03-15 03:00 PM (after cutoff)
Status: confirmed
Method: next_day
Location: Hanoi
Expected: delivery 2025-03-17 (skip to next business day)
```

### **Test Case 4: Order Not Shipped Yet**
```
Status: pending
Expected: estimated_delivery = null, message explaining order not shipped
```

### **Test Case 5: Security - Wrong Customer**
```
JWT customer_id: 1
Order customer_id: 2
Expected: 404 Not Found (not 403 Forbidden)
```

---

## 📚 Implementation Priority

**Phase 1 (Required for MVP):**
- Basic delivery estimation for domestic orders
- Support `pending`, `confirmed`, `shipping`, `delivered` statuses
- Business days calculation (exclude Sundays)

**Phase 2 (Future Enhancement):**
- International shipping estimation
- Public holiday exclusion
- Real-time carrier API integration
- SMS/Email notifications when delivery date changes

---

## 🔗 Related Endpoints

This endpoint should work alongside:
- `GET /orders/track` - Get order details
- `GET /orders` - Get user's order list

Chatbot will call both endpoints to provide comprehensive order information.

---

## 📞 Questions for Backend Team

1. Do we have `shipping_method` field in the `orders` table? If not, should we add it or infer from order data?
2. Should we store `estimated_delivery_date` in the database or calculate it dynamically on each request?
3. Do we have a list of major cities vs. provinces in the database?
4. Should we integrate with actual carrier APIs for tracking, or is this manual for now?
5. What carrier services are we currently using? (for tracking URL format)

---

## ✅ Acceptance Criteria

- [ ] API endpoint returns estimated delivery dates based on business logic
- [ ] Dates are calculated using business days (excluding Sundays)
- [ ] Customer ownership verification implemented
- [ ] Returns appropriate responses for all order statuses
- [ ] Error handling for invalid order numbers
- [ ] API documented in Swagger/OpenAPI
- [ ] Unit tests for delivery calculation logic
- [ ] Integration tests for the endpoint

---

## 📝 Notes

- This API is specifically designed for chatbot integration
- All date calculations MUST be done by backend, not by chatbot
- Chatbot will only display the dates returned by this API
- This ensures consistency, auditability, and prevents misleading customer commitments
