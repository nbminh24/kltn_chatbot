# YÊU CẦU FRONTEND: Order Tracking UI Component

**Ngày yêu cầu:** 06/01/2026  
**Yêu cầu từ:** Team Chatbot AI  
**Độ ưu tiên:** Medium  

---

## 1. TỔNG QUAN

Chatbot cần hiển thị thông tin đơn hàng một cách **trực quan** thay vì chỉ text thuần. Yêu cầu frontend implement:

1. **Order Card Component** - Hiển thị thông tin đơn hàng dạng card
2. **Link to Order Detail** - Nút/link dẫn đến trang chi tiết đơn hàng
3. **Currency Conversion** - Chuyển đổi từ USD sang VND (nghìn đồng)

---

## 2. CHATBOT MESSAGE FORMAT HIỆN TẠI

### Backend trả về cho chatbot:
```json
{
  "order_id": 32,
  "order_number": "0000000032",
  "fulfillment_status": "shipping",
  "payment_status": "paid",
  "total_amount": 13.52,  // USD
  "created_at": "2025-12-16T03:50:00.000Z",
  "tracking_number": "VN123456789",
  "items": [
    {
      "product_id": 5,
      "product_name": "Relaxed Fit Sweet Pastry Meow Meow Bead",
      "quantity": 2,
      "price": 13.52
    }
  ]
}
```

### Chatbot gửi message:
```json
{
  "type": "order_card",
  "order": {
    "order_number": "0000000032",
    "fulfillment_status": "shipping",
    "created_at": "December 16, 2025",
    "tracking_number": "VN123456789",
    "total_amount_usd": 13.52,
    "total_amount_vnd": 13520  // ← Converted (USD * 1000)
  }
}
```

---

## 3. YÊU CẦU UI COMPONENT

### 3.1. Order Card Component

**Component Name:** `OrderCard` hoặc `ChatbotOrderCard`

**Props:**
```typescript
interface OrderCardProps {
  orderNumber: string;          // e.g., "0000000032"
  fulfillmentStatus: string;    // e.g., "shipping", "delivered", "pending"
  createdAt: string;            // e.g., "December 16, 2025"
  trackingNumber?: string;      // Optional
  totalAmountUsd?: number;      // Optional (để backup)
  totalAmountVnd: number;       // VND amount (required)
}
```

**Design Requirements:**

```
┌─────────────────────────────────────────────┐
│  📦 Đơn hàng #0000000032                    │
├─────────────────────────────────────────────┤
│  🚚 Trạng thái: Đang giao hàng              │
│  📅 Ngày đặt: 16/12/2025                    │
│  📦 Mã vận đơn: VN123456789                 │
│  💰 Tổng tiền: 13.520đ                      │
├─────────────────────────────────────────────┤
│         [Xem chi tiết đơn hàng] →           │
└─────────────────────────────────────────────┘
```

**Style Guidelines:**
- **Card**: Border radius 8-12px, shadow nhẹ
- **Status badge**: Màu sắc theo trạng thái (xanh/vàng/xám)
- **Button**: Primary color, hover effect
- **Spacing**: Padding 16-20px, line-height thoáng

---

### 3.2. Status Badge Colors

| Status | Badge Color | Vietnamese Label |
|--------|-------------|------------------|
| `pending` | 🟡 Yellow (#FFC107) | Chờ xác nhận |
| `confirmed` / `pending_fulfillment` | 🔵 Blue (#2196F3) | Đã xác nhận |
| `shipping` / `in_transit` | 🟣 Purple (#9C27B0) | Đang giao |
| `delivered` / `completed` | 🟢 Green (#4CAF50) | Đã giao |
| `cancelled` | 🔴 Red (#F44336) | Đã hủy |

---

### 3.3. Link to Order Detail

**Button/Link Format:**
```html
<a href="/orders/{order_number}" class="order-detail-link">
  Xem chi tiết đơn hàng →
</a>
```

**URL Pattern:**
- `/orders/0000000032`
- hoặc `/account/orders/0000000032`
- hoặc `/profile/orders/0000000032`

*(Tùy theo routing hiện tại của frontend)*

**Action:**
- Click → Mở trang chi tiết đơn hàng
- Có thể mở trong **tab mới** hoặc **same tab** (tùy UX preference)

---

## 4. CURRENCY CONVERSION

### 4.1. Logic chuyển đổi

**Input:** `total_amount` từ backend (USD)  
**Output:** `total_amount_vnd` (VND - nghìn đồng)

**Công thức:**
```javascript
// Chatbot backend sẽ convert và gửi sẵn
total_amount_vnd = total_amount_usd * 1000
```

**Ví dụ:**
- `$13.52` → `13.520đ` (13,520 VND)
- `$25.00` → `25.000đ` (25,000 VND)
- `$99.99` → `99.990đ` (99,990 VND)

### 4.2. Display Format

**Format VND:**
```javascript
// JavaScript example
const formatVND = (amount) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    minimumFractionDigits: 0
  }).format(amount);
};

// Output: "13.520 ₫" hoặc "13.520đ"
```

**Hoặc custom format:**
```javascript
const formatVND = (amount) => {
  return amount.toLocaleString('vi-VN') + 'đ';
};

// Output: "13.520đ"
```

---

## 5. INTEGRATION FLOW

### Chatbot → Frontend Message Flow

**Step 1:** User hỏi "đơn hàng của tôi"

**Step 2:** Chatbot gọi backend API

**Step 3:** Chatbot xử lý và gửi message:
```json
{
  "sender": "bot",
  "type": "text",
  "text": "Đơn hàng #0000000032 của bạn hiện đang trên đường giao đến bạn 🚚"
}
```

**Step 4:** Chatbot gửi custom component:
```json
{
  "sender": "bot",
  "type": "order_card",
  "order": {
    "order_number": "0000000032",
    "fulfillment_status": "shipping",
    "created_at": "December 16, 2025",
    "tracking_number": "VN123456789",
    "total_amount_vnd": 13520
  }
}
```

**Step 5:** Frontend nhận message `type: "order_card"` → render `<OrderCard />`

---

## 6. RESPONSIVE DESIGN

### Desktop (>768px)
- Card width: 400-500px
- Font size: 14-16px
- Padding: 20px

### Mobile (<768px)
- Card width: 100% (với margin 16px)
- Font size: 13-15px
- Padding: 16px
- Button full-width

---

## 7. MOCK DATA ĐỂ TEST

```javascript
// Test case 1: Shipping order
const mockOrder1 = {
  orderNumber: "0000000032",
  fulfillmentStatus: "shipping",
  createdAt: "December 16, 2025",
  trackingNumber: "VN123456789",
  totalAmountVnd: 13520
};

// Test case 2: Delivered order
const mockOrder2 = {
  orderNumber: "0000000045",
  fulfillmentStatus: "delivered",
  createdAt: "December 10, 2025",
  trackingNumber: "VN987654321",
  totalAmountVnd: 25000
};

// Test case 3: Pending payment
const mockOrder3 = {
  orderNumber: "0000000050",
  fulfillmentStatus: "pending",
  createdAt: "December 18, 2025",
  trackingNumber: null,
  totalAmountVnd: 99990
};
```

---

## 8. IMPLEMENTATION CHECKLIST

### Frontend Tasks
- [ ] Tạo `OrderCard` component
- [ ] Implement status badge với màu sắc đúng
- [ ] Format VND currency với dấu phân cách nghìn
- [ ] Thêm link "Xem chi tiết đơn hàng" với routing đúng
- [ ] Responsive design (desktop + mobile)
- [ ] Handle case không có tracking number
- [ ] Handle case không có total amount

### Chatbot Tasks (đã hoàn thành)
- [x] Bỏ thông tin tiền khỏi text message
- [x] Convert USD → VND trong backend
- [x] Gửi `json_message` với type `order_card`

---

## 9. EXAMPLE CODE (React + TypeScript)

```typescript
interface OrderCardProps {
  orderNumber: string;
  fulfillmentStatus: string;
  createdAt: string;
  trackingNumber?: string;
  totalAmountVnd: number;
}

const OrderCard: React.FC<OrderCardProps> = ({
  orderNumber,
  fulfillmentStatus,
  createdAt,
  trackingNumber,
  totalAmountVnd
}) => {
  const getStatusBadge = (status: string) => {
    const statusMap = {
      pending: { label: 'Chờ xác nhận', color: '#FFC107' },
      confirmed: { label: 'Đã xác nhận', color: '#2196F3' },
      shipping: { label: 'Đang giao', color: '#9C27B0' },
      delivered: { label: 'Đã giao', color: '#4CAF50' },
      cancelled: { label: 'Đã hủy', color: '#F44336' }
    };
    return statusMap[status] || { label: status, color: '#757575' };
  };

  const formatVND = (amount: number) => {
    return amount.toLocaleString('vi-VN') + 'đ';
  };

  const statusBadge = getStatusBadge(fulfillmentStatus);

  return (
    <div className="order-card">
      <div className="order-header">
        <h3>📦 Đơn hàng #{orderNumber}</h3>
      </div>
      
      <div className="order-body">
        <div className="order-info">
          <span 
            className="status-badge" 
            style={{ backgroundColor: statusBadge.color }}
          >
            🚚 {statusBadge.label}
          </span>
          <p>📅 Ngày đặt: {createdAt}</p>
          {trackingNumber && (
            <p>📦 Mã vận đơn: {trackingNumber}</p>
          )}
          <p>💰 Tổng tiền: {formatVND(totalAmountVnd)}</p>
        </div>
      </div>
      
      <div className="order-footer">
        <a 
          href={`/orders/${orderNumber}`} 
          className="order-detail-link"
        >
          Xem chi tiết đơn hàng →
        </a>
      </div>
    </div>
  );
};
```

---

## 10. LIÊN HỆ

Nếu có thắc mắc về:
- **Message format**: Liên hệ team Chatbot AI
- **UI/UX design**: Tham khảo designer
- **Routing URL**: Xác nhận với team Frontend

---

**END OF DOCUMENT**
