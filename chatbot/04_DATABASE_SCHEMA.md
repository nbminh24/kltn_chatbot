# 🗄️ DATABASE SCHEMA - CHATBOT E-COMMERCE

## TỔNG QUAN

Database sử dụng **PostgreSQL** với các bảng liên quan đến chatbot:

**Nhóm Chat:**
- `chat_sessions` - Quản lý phiên chat
- `chat_messages` - Lưu tin nhắn

**Nhóm Support:**
- `support_tickets` - Tickets cần admin xử lý
- `support_ticket_replies` - Lịch sử trả lời

**Nhóm E-commerce Core:**
- `products`, `product_variants` - Sản phẩm
- `categories` - Danh mục
- `orders`, `order_items` - Đơn hàng
- `carts`, `cart_items` - Giỏ hàng
- `wishlist_items` - Yêu thích
- `promotions` - Khuyến mãi

---

## 1. CHAT MANAGEMENT TABLES

### 1.1. chat_sessions

**Mục đích:** Quản lý phiên chat của customer (logged-in) hoặc visitor (guest)

```sql
CREATE TABLE chat_sessions (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id BIGINT NULL,                              -- FK -> customers.id
  visitor_id VARCHAR NULL,                              -- UUID cho guest
  status VARCHAR DEFAULT 'active',                      -- active, closed
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT chat_sessions_customer_fkey 
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Indexes
CREATE INDEX idx_chat_sessions_customer_id ON chat_sessions(customer_id);
CREATE INDEX idx_chat_sessions_visitor_id ON chat_sessions(visitor_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);
```

**Business Rules:**
- Mỗi `customer_id` có 1 session active tại 1 thời điểm
- Mỗi `visitor_id` có 1 session active
- Khi user login → merge sessions (visitor → customer)
- `updated_at` tự động cập nhật khi có message mới

**Example Data:**
```sql
INSERT INTO chat_sessions VALUES
  (1, 123, NULL, 'active', '2024-12-07 10:00:00', '2024-12-07 10:30:00'),  -- Logged-in user
  (2, NULL, 'abc-uuid-123', 'active', '2024-12-07 11:00:00', '2024-12-07 11:05:00');  -- Guest
```

---

### 1.2. chat_messages

**Mục đích:** Lưu toàn bộ tin nhắn trong conversation

```sql
CREATE TABLE chat_messages (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id BIGINT NOT NULL,                           -- FK -> chat_sessions.id
  sender VARCHAR NOT NULL,                              -- 'customer' | 'bot'
  message TEXT NOT NULL,
  image_url TEXT NULL,                                  -- URL ảnh (nếu có)
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT chat_messages_session_fkey 
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX idx_chat_messages_sender ON chat_messages(sender);
```

**Business Rules:**
- `sender` = 'customer': Tin nhắn từ user
- `sender` = 'bot': Tin nhắn từ chatbot
- `is_read`: Admin đã đọc chưa (dùng cho admin dashboard)
- Cascade delete khi xóa session

**Example Data:**
```sql
INSERT INTO chat_messages VALUES
  (1, 1, 'customer', 'Tìm áo thun đen', NULL, FALSE, '2024-12-07 10:00:01'),
  (2, 1, 'bot', 'Mình tìm thấy 5 sản phẩm áo thun đen...', NULL, FALSE, '2024-12-07 10:00:02'),
  (3, 1, 'customer', 'Còn size M không?', NULL, FALSE, '2024-12-07 10:01:00'),
  (4, 1, 'bot', 'Còn 10 sản phẩm size M', NULL, FALSE, '2024-12-07 10:01:01');
```

---

## 2. SUPPORT SYSTEM TABLES

### 2.1. support_tickets

**Mục đích:** Lưu các yêu cầu hỗ trợ cần admin xử lý

```sql
CREATE TABLE support_tickets (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ticket_code VARCHAR NOT NULL UNIQUE,                  -- TK001234
  customer_id BIGINT NULL,                              -- FK -> customers.id
  customer_email VARCHAR NULL,
  subject VARCHAR NOT NULL,
  message TEXT NULL,
  status VARCHAR DEFAULT 'pending',                     -- pending, in_progress, replied, resolved, closed
  priority VARCHAR DEFAULT 'medium',                    -- low, medium, high
  source VARCHAR DEFAULT 'contact_form',                -- contact_form, chatbot, email
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT support_tickets_customer_fkey 
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

-- Indexes
CREATE UNIQUE INDEX idx_support_tickets_code ON support_tickets(ticket_code);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX idx_support_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX idx_support_tickets_created_at ON support_tickets(created_at DESC);
```

**Business Rules:**
- `ticket_code` auto-generate: TK + 6 digits
- `source = 'chatbot'`: Ticket tạo từ chatbot
- `priority = 'high'`: Khiếu nại nghiêm trọng (hàng hỏng, feedback negative)
- Status flow: pending → in_progress → replied → resolved → closed

**Example Data:**
```sql
INSERT INTO support_tickets VALUES
  (1, 'TK001234', 123, 'user@example.com', 'Yêu cầu hỗ trợ từ chatbot', 
   'Khách hàng muốn gặp nhân viên', 'pending', 'normal', 'chatbot', 
   '2024-12-07 10:30:00', '2024-12-07 10:30:00'),
  
  (2, 'TK001235', 456, 'angry@example.com', 'Hàng bị rách', 
   'Khách hàng nhận được hàng bị rách, yêu cầu đổi trả', 'pending', 'high', 'chatbot', 
   '2024-12-07 11:00:00', '2024-12-07 11:00:00');
```

---

### 2.2. support_ticket_replies

**Mục đích:** Lưu lịch sử trả lời ticket (admin hoặc customer)

```sql
CREATE TABLE support_ticket_replies (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ticket_id BIGINT NOT NULL,                            -- FK -> support_tickets.id
  admin_id BIGINT NULL,                                 -- FK -> admins.id (NULL nếu customer reply)
  body TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT support_ticket_replies_ticket_fkey 
    FOREIGN KEY (ticket_id) REFERENCES support_tickets(id) ON DELETE CASCADE,
  CONSTRAINT support_ticket_replies_admin_fkey 
    FOREIGN KEY (admin_id) REFERENCES admins(id)
);

-- Indexes
CREATE INDEX idx_support_ticket_replies_ticket_id ON support_ticket_replies(ticket_id);
CREATE INDEX idx_support_ticket_replies_created_at ON support_ticket_replies(created_at);
```

**Business Rules:**
- `admin_id = NULL`: Customer reply
- `admin_id != NULL`: Admin reply
- Cascade delete khi xóa ticket

---

## 3. E-COMMERCE CORE TABLES

### 3.1. products

```sql
CREATE TABLE products (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  category_id BIGINT NULL,                              -- FK -> categories.id
  name VARCHAR NOT NULL,
  slug VARCHAR NOT NULL UNIQUE,
  description TEXT NULL,
  full_description TEXT NULL,
  cost_price NUMERIC NULL,
  selling_price NUMERIC NOT NULL,
  status VARCHAR DEFAULT 'active',                      -- active, inactive
  thumbnail_url TEXT NULL,
  average_rating NUMERIC DEFAULT 0.00,
  total_reviews INT DEFAULT 0,
  attributes JSONB DEFAULT '{}',                        -- Flexible metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE NULL,
  
  CONSTRAINT products_category_fkey 
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Indexes
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_deleted_at ON products(deleted_at);
CREATE INDEX idx_products_selling_price ON products(selling_price);
```

**attributes JSON Example:**
```json
{
  "material": "Cotton 100%",
  "origin": "Vietnam",
  "brand": "Local Brand",
  "collection": "Summer 2024",
  "tags": ["casual", "beach", "wedding"]
}
```

---

### 3.2. product_variants

**Mục đích:** Variants theo size + color (critical cho inventory)

```sql
CREATE TABLE product_variants (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  product_id BIGINT NOT NULL,                           -- FK -> products.id
  size_id BIGINT NULL,                                  -- FK -> sizes.id
  color_id BIGINT NULL,                                 -- FK -> colors.id
  name VARCHAR NULL,                                    -- "Áo thun đen - Size M"
  sku VARCHAR NOT NULL UNIQUE,                          -- AT001-M-BLACK
  total_stock INT DEFAULT 0,                            -- Tổng số lượng
  reserved_stock INT DEFAULT 0,                         -- Đã đặt chưa thanh toán
  reorder_point INT DEFAULT 0,                          -- Ngưỡng cảnh báo hết hàng
  status VARCHAR DEFAULT 'active',
  version INT DEFAULT 1,                                -- Optimistic locking
  deleted_at TIMESTAMP WITH TIME ZONE NULL,
  
  CONSTRAINT product_variants_product_fkey 
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  CONSTRAINT product_variants_size_fkey 
    FOREIGN KEY (size_id) REFERENCES sizes(id),
  CONSTRAINT product_variants_color_fkey 
    FOREIGN KEY (color_id) REFERENCES colors(id)
);

-- Indexes
CREATE UNIQUE INDEX idx_product_variants_sku ON product_variants(sku);
CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_product_variants_status ON product_variants(status);
CREATE INDEX idx_product_variants_stock ON product_variants(total_stock);
```

**Business Rules:**
- `available_stock = total_stock - reserved_stock`
- Chatbot check stock: `WHERE status='active' AND (total_stock - reserved_stock) > 0`

---

### 3.3. sizes & colors

```sql
CREATE TABLE sizes (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR NOT NULL,                                -- S, M, L, XL, XXL
  sort_order INT DEFAULT 0
);

CREATE TABLE colors (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR NOT NULL,                                -- Đen, Trắng, Đỏ
  hex_code VARCHAR NULL                                 -- #000000, #FFFFFF
);
```

---

### 3.4. categories

```sql
CREATE TABLE categories (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR NOT NULL,
  slug VARCHAR NOT NULL UNIQUE,
  status VARCHAR DEFAULT 'active',
  deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Example data
INSERT INTO categories VALUES
  (1, 'Áo thun', 'ao-thun', 'active', NULL),
  (2, 'Áo sơ mi', 'ao-so-mi', 'active', NULL),
  (3, 'Quần jeans', 'quan-jeans', 'active', NULL),
  (4, 'Giày sneaker', 'giay-sneaker', 'active', NULL);
```

---

### 3.5. orders & order_items

```sql
CREATE TABLE orders (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id BIGINT NULL,
  customer_email VARCHAR NULL,
  shipping_address TEXT NOT NULL,
  shipping_phone VARCHAR NOT NULL,
  shipping_city VARCHAR NULL,
  shipping_district VARCHAR NULL,
  shipping_ward VARCHAR NULL,
  fulfillment_status VARCHAR DEFAULT 'pending',         -- pending, processing, shipping, delivered, cancelled
  payment_status VARCHAR DEFAULT 'unpaid',              -- unpaid, paid, refunded
  payment_method VARCHAR DEFAULT 'cod',                 -- cod, bank_transfer, momo, vnpay
  shipping_fee NUMERIC DEFAULT 0,
  total_amount NUMERIC NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT orders_customer_fkey 
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id BIGINT NOT NULL,
  variant_id BIGINT NOT NULL,
  quantity INT NOT NULL,
  price_at_purchase NUMERIC NOT NULL,                   -- Giá tại thời điểm mua
  
  CONSTRAINT order_items_order_fkey 
    FOREIGN KEY (order_id) REFERENCES orders(id),
  CONSTRAINT order_items_variant_fkey 
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);
```

**Chatbot Queries:**
- Get orders: `WHERE customer_id = X ORDER BY created_at DESC LIMIT 5`
- Check status: `WHERE id = Y AND customer_id = X`

---

### 3.6. carts & cart_items

```sql
CREATE TABLE carts (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id BIGINT NULL UNIQUE,                       -- FK -> customers.id
  session_id VARCHAR NULL UNIQUE,                       -- Guest cart (UUID)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT carts_customer_fkey 
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE cart_items (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cart_id BIGINT NOT NULL,
  variant_id BIGINT NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  
  CONSTRAINT cart_items_cart_fkey 
    FOREIGN KEY (cart_id) REFERENCES carts(id),
  CONSTRAINT cart_items_variant_fkey 
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);
```

**Chatbot Action:**
```sql
-- Add to cart
INSERT INTO cart_items (cart_id, variant_id, quantity)
VALUES (X, Y, 1)
ON CONFLICT (cart_id, variant_id) DO UPDATE 
SET quantity = cart_items.quantity + 1;
```

---

### 3.7. wishlist_items

```sql
CREATE TABLE wishlist_items (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  customer_id BIGINT NOT NULL,
  variant_id BIGINT NOT NULL,
  
  CONSTRAINT wishlist_items_customer_fkey 
    FOREIGN KEY (customer_id) REFERENCES customers(id),
  CONSTRAINT wishlist_items_variant_fkey 
    FOREIGN KEY (variant_id) REFERENCES product_variants(id),
  
  UNIQUE (customer_id, variant_id)
);
```

---

### 3.8. promotions

```sql
CREATE TABLE promotions (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR NOT NULL,
  type VARCHAR NOT NULL,                                -- voucher, flash_sale, bundle
  discount_value NUMERIC NOT NULL,
  discount_type VARCHAR NOT NULL,                       -- percentage, fixed_amount
  number_limited INT NULL,                              -- Số lượng giới hạn
  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  end_date TIMESTAMP WITH TIME ZONE NOT NULL,
  status VARCHAR DEFAULT 'scheduled'                    -- scheduled, active, expired
);

CREATE TABLE promotion_products (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  promotion_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  flash_sale_price NUMERIC NOT NULL,
  
  CONSTRAINT promotion_products_promotion_fkey 
    FOREIGN KEY (promotion_id) REFERENCES promotions(id),
  CONSTRAINT promotion_products_product_fkey 
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Chatbot Query:**
```sql
-- Get active promotions
SELECT p.*, pp.product_id, pp.flash_sale_price
FROM promotions p
LEFT JOIN promotion_products pp ON p.id = pp.promotion_id
WHERE p.status = 'active'
  AND NOW() BETWEEN p.start_date AND p.end_date;
```

---

## 4. QUERY EXAMPLES FOR CHATBOT

### 4.1. Search Products

```sql
-- Text search với filters
SELECT 
  p.id, p.name, p.selling_price, p.thumbnail_url,
  c.name as category_name,
  COUNT(DISTINCT pv.id) as variants_count,
  SUM(pv.total_stock - pv.reserved_stock) as total_available
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN product_variants pv ON p.id = pv.product_id
WHERE p.status = 'active'
  AND p.deleted_at IS NULL
  AND (
    p.name ILIKE '%áo thun%'
    OR c.slug = 'ao-thun'
  )
  AND EXISTS (
    SELECT 1 FROM product_variants pv2
    LEFT JOIN colors co ON pv2.color_id = co.id
    WHERE pv2.product_id = p.id
      AND co.name ILIKE '%đen%'
  )
GROUP BY p.id, c.name
HAVING SUM(pv.total_stock - pv.reserved_stock) > 0
ORDER BY p.created_at DESC
LIMIT 10;
```

### 4.2. Check Stock

```sql
-- Check specific variant stock
SELECT 
  pv.id as variant_id,
  pv.sku,
  pv.total_stock,
  pv.reserved_stock,
  (pv.total_stock - pv.reserved_stock) as available_stock,
  s.name as size,
  c.name as color
FROM product_variants pv
LEFT JOIN sizes s ON pv.size_id = s.id
LEFT JOIN colors c ON pv.color_id = c.id
WHERE pv.product_id = 123
  AND s.name = 'M'
  AND c.name = 'Đen'
  AND pv.status = 'active';
```

### 4.3. Get Customer Orders

```sql
-- Get recent orders with status
SELECT 
  o.id,
  o.fulfillment_status,
  o.payment_status,
  o.total_amount,
  o.created_at,
  JSON_AGG(
    JSON_BUILD_OBJECT(
      'variant_id', oi.variant_id,
      'quantity', oi.quantity,
      'price', oi.price_at_purchase,
      'product_name', p.name
    )
  ) as items
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN product_variants pv ON oi.variant_id = pv.id
LEFT JOIN products p ON pv.product_id = p.id
WHERE o.customer_id = 123
GROUP BY o.id
ORDER BY o.created_at DESC
LIMIT 5;
```

---

## 5. DATABASE OPTIMIZATION

### Indexes hiện có (quan trọng cho performance)

```sql
-- Chat tables
CREATE INDEX idx_chat_sessions_customer_id ON chat_sessions(customer_id);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);

-- Product search
CREATE INDEX idx_products_name_gin ON products USING GIN (to_tsvector('english', name));
CREATE INDEX idx_products_category_status ON products(category_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_product_variants_product_stock ON product_variants(product_id, total_stock, reserved_stock);

-- Orders
CREATE INDEX idx_orders_customer_created ON orders(customer_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(fulfillment_status);
```

---

## 6. MIGRATION NOTES

**Đã có trong database hiện tại:**
- ✅ All chat tables
- ✅ All support tables
- ✅ All e-commerce core tables

**Có thể cần thêm:**
- ⚠️ `pgvector` extension cho image search
- ⚠️ Full-text search indexes nếu dùng ElasticSearch

---

**Ngày tạo:** 2024-12-07  
**Version:** 1.0
