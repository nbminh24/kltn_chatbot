# YÊU CẦU BỔ SUNG: Confidence Score cho Product Search API

**Ngày yêu cầu:** 06/01/2026  
**Yêu cầu từ:** Team Chatbot AI  
**Độ ưu tiên:** Medium  

---

## 1. ENDPOINT CẦN SỬA ĐỔI

**Endpoint hiện tại:**
```
GET /api/chatbot/products/search
```

**Query Parameters:**
- `query` (string): Search query
- `limit` (integer): Maximum số sản phẩm trả về

---

## 2. YÊU CẦU THAY ĐỔI RESPONSE

### Response Format hiện tại (dự đoán):
```json
{
  "success": true,
  "data": [
    {
      "slug": "relaxed-fit-sweet-pastry-meow-meow-bead",
      "name": "Relaxed Fit Sweet Pastry Meow Meow Bead",
      "price": 13.52,
      "thumbnail": "...",
      "rating": 0,
      "reviews": 0,
      "in_stock": true
    }
  ]
}
```

### Response Format mong muốn (BỔ SUNG):
```json
{
  "success": true,
  "data": [
    {
      "slug": "relaxed-fit-sweet-pastry-meow-meow-bead",
      "name": "Relaxed Fit Sweet Pastry Meow Meow Bead",
      "price": 13.52,
      "thumbnail": "...",
      "rating": 0,
      "reviews": 0,
      "in_stock": true,
      "relevance_score": 0.95  // ← FIELD MỚI
    }
  ]
}
```

---

## 3. YÊU CẦU CHI TIẾT

### 3.1. Field mới: `relevance_score`

- **Tên field:** `relevance_score`
- **Kiểu dữ liệu:** `float` (0.0 - 1.0)
- **Mô tả:** Điểm số đo độ liên quan giữa sản phẩm và search query
- **Giá trị:**
  - `1.0` = Hoàn toàn khớp (exact match)
  - `0.8 - 0.99` = Rất liên quan
  - `0.5 - 0.79` = Khá liên quan
  - `< 0.5` = Ít liên quan (có thể không trả về)

### 3.2. Sắp xếp kết quả

- Kết quả **BẮT BUỘC** được sắp xếp theo `relevance_score` giảm dần
- Sản phẩm có score cao nhất → xuất hiện đầu tiên

---

## 4. LOGIC TÍNH RELEVANCE SCORE (ĐỀ XUẤT)

Backend có thể tham khảo các yếu tố sau để tính score:

### 4.1. Text Matching (trọng số cao nhất)
- **Exact match** (query == product name): score = 1.0
- **Partial match** (query nằm trong name): score = 0.8 - 0.95
- **Word match** (các từ trong query xuất hiện trong name/description): score = 0.6 - 0.8
- **Fuzzy match** (tương tự nhưng có lỗi chính tả): score = 0.4 - 0.6

### 4.2. Các yếu tố phụ (fine-tuning)
- Sản phẩm có `in_stock = true`: +0.05
- Sản phẩm có rating cao (>= 4.0): +0.03
- Sản phẩm có nhiều reviews (>= 50): +0.02

### 4.3. Công cụ gợi ý
- Nếu đang dùng **PostgreSQL full-text search**: sử dụng `ts_rank()` hoặc `ts_rank_cd()`
- Nếu đang dùng **Elasticsearch**: sử dụng `_score` có sẵn
- Nếu đang dùng **LIKE/ILIKE**: tự tính dựa trên độ khớp chuỗi

---

## 5. CASE TEST MẪU

### Input:
```
GET /api/chatbot/products/search?query=áo meow&limit=10
```

### Output mong đợi:
```json
{
  "success": true,
  "data": [
    {
      "slug": "relaxed-fit-sweet-pastry-meow-meow-bead",
      "name": "Relaxed Fit Sweet Pastry Meow Meow Bead",
      "price": 13.52,
      "relevance_score": 0.95  // "meow meow" xuất hiện 2 lần
    },
    {
      "slug": "relaxed-fit-animal-mood-funny-meow",
      "name": "Relaxed Fit Animal Mood Funny Meow",
      "price": 13.52,
      "relevance_score": 0.92  // "meow" xuất hiện 1 lần
    },
    {
      "slug": "relaxed-fit-vitamin-meow",
      "name": "Relaxed Fit Vitamin Meow",
      "price": 13.52,
      "relevance_score": 0.90  // tên ngắn gọn, khớp "meow"
    }
  ]
}
```

**Lưu ý:** Kết quả đã được sắp xếp theo `relevance_score` giảm dần

---

## 6. BACKWARD COMPATIBILITY

- **Không bắt buộc:** Field `relevance_score` nên là **optional** trong response
- Nếu client cũ không cần dùng, họ có thể bỏ qua field này
- Chatbot sẽ tự động đọc và sử dụng nếu field tồn tại

---

## 7. TIMELINE ĐỀ XUẤT

- **Estimate:** 2-4 giờ development + testing
- **Priority:** Medium (không block, nhưng cải thiện UX)

---

## 8. LIÊN HỆ

Nếu có thắc mắc hoặc cần thảo luận thêm về logic tính score, vui lòng liên hệ team Chatbot AI.

---

**END OF DOCUMENT**
