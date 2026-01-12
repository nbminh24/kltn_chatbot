# CHATBOT TEST CASES - Mẫu Intent Kiểm Tra

**Ngày tạo:** 06/01/2026  
**Mục đích:** Danh sách test cases để PM kiểm tra các tính năng chatbot  

---

## 1. TÌM KIẾM SẢN PHẨM (Product Search)

### Test Case 1.1: Tìm kiếm cơ bản
**Input:**
- "tìm áo thun"
- "cho tôi xem áo meow"
- "có áo polo không"
- "shirt"
- "t-shirt relaxed"

**Expected:**
- Hiển thị message template ngẫu nhiên (1 trong 3 mẫu)
- Show danh sách sản phẩm với relevance_score
- Sản phẩm có score >= 0.3 → hiển thị như kết quả chính
- Sản phẩm có score < 0.3 → hiển thị như đề xuất (nếu không có kết quả chính)

### Test Case 1.2: Không tìm thấy sản phẩm
**Input:**
- "tìm xe máy"
- "laptop"
- "điện thoại iPhone"

**Expected:**
- Message: "Hiện tại shop chưa có sản phẩm đúng với..." (1 trong 3 mẫu)
- Có thể có đề xuất sản phẩm tương tự (nếu backend trả về)

### Test Case 1.3: Tìm kiếm với từ khóa đặc biệt
**Input:**
- "áo có hình mèo"
- "quần short"
- "jacket hoodie"
- "vintage style"

**Expected:**
- Kết quả liên quan với từ khóa
- Score cao nhất xuất hiện đầu tiên

---

## 2. XEM ĐỜN HÀNG (Order Tracking)

### Test Case 2.1: Xem đơn hàng không cung cấp mã
**Input:**
- "tôi muốn xem đơn hàng của tôi"
- "đơn hàng của tôi đâu"
- "check order"

**Expected:**
- Message: "Mình chưa hiểu lắm đơn hàng nào bạn muốn xem..."
- Yêu cầu cung cấp mã đơn hàng

### Test Case 2.2: Xem đơn hàng với mã cụ thể
**Input:**
- "xem đơn 0000000032"
- "đơn #38"
- "order 0000000045"

**Expected:**
- Hiển thị thông tin đơn hàng theo trạng thái:

**Trạng thái Confirmed:**
```
Mình đã tìm thấy đơn hàng của bạn rồi nhé 😊
Đơn #XXX hiện đang được shop xác nhận và chuẩn bị hàng.
Dự kiến sẽ được giao trong 1–2 ngày tới.

📅 Ngày đặt: ...
```

**Trạng thái Shipping:**
```
Đơn hàng #XXX của bạn hiện đang trên đường giao đến bạn 🚚
Dự kiến bạn sẽ nhận được trong hôm nay hoặc ngày mai nhé!

📦 Mã vận đơn: ... (nếu có)
```

**Trạng thái Delivered:**
```
Đơn hàng #XXX đã được giao thành công ✅
Nếu bạn cần hỗ trợ đổi trả hay thêm thông tin, cứ nhắn mình nhé!

📅 Ngày đặt: ...
```

**Trạng thái Pending:**
```
Mình đã tìm thấy đơn #XXX của bạn.
Hiện đơn đang chờ shop xác nhận và chuẩn bị hàng.
Mình sẽ cập nhật cho bạn khi có thông tin giao hàng nhé!

📅 Ngày đặt: ...
```

**Trạng thái Cancelled:**
```
Đơn hàng #XXX đã được hủy.

📅 Ngày đặt: ...
Nếu bạn cần đặt lại hoặc cần hỗ trợ, cứ nhắn mình nhé!
```

### Test Case 2.3: Xem đơn hàng khi chưa đăng nhập
**Input:**
- "xem đơn hàng"

**Expected:**
- Message yêu cầu đăng nhập trước

---

## 3. CHI TIẾT SẢN PHẨM (Product Details)

### Test Case 3.1: Xem chi tiết sản phẩm
**Input:**
- "cho tôi xem chi tiết sản phẩm relaxed-fit-sweet-pastry-meow-meow-bead"
- "thông tin về sản phẩm [slug]"
- "tell me about [product name]"

**Expected:**
- Hiển thị thông tin chi tiết: tên, giá, mô tả, rating, reviews
- Variants (size, color) nếu có
- Stock status

### Test Case 3.2: Sản phẩm không tồn tại
**Input:**
- "chi tiết sản phẩm xyz-abc-123"

**Expected:**
- Message lỗi "Sản phẩm không tồn tại"

---

## 4. KIỂM TRA TỒN KHO (Stock Availability)

### Test Case 4.1: Kiểm tra tồn kho cơ bản
**Input:**
- "áo meow còn hàng không"
- "có sẵn áo polo size M không"
- "in stock"

**Expected:**
- Thông tin tồn kho của sản phẩm
- Variants available (nếu có)

---

## 5. FAQ & CHÍNH SÁCH (FAQ & Policies)

### Test Case 5.1: Hỏi về chính sách
**Input:**
- "chính sách đổi trả"
- "return policy"
- "shipping policy"
- "làm sao để đổi size"
- "thời gian giao hàng"

**Expected:**
- Trả về nội dung chính sách từ CMS
- Thông tin rõ ràng, dễ hiểu

### Test Case 5.2: FAQ thường gặp
**Input:**
- "làm sao để đặt hàng"
- "phương thức thanh toán"
- "có ship COD không"
- "miễn phí vận chuyển không"

**Expected:**
- Câu trả lời từ FAQ hoặc Gemini (nếu có training data)

---

## 6. HỦY ĐƠN HÀNG (Order Cancellation)

### Test Case 6.1: Hủy đơn hàng pending
**Input:**
- "tôi muốn hủy đơn 0000000032"
- "cancel order #38"
- "hủy đơn hàng"

**Expected:**
- Kiểm tra trạng thái đơn
- Nếu pending → cho phép hủy
- Nếu confirmed/shipping/delivered → từ chối + gợi ý

### Test Case 6.2: Hủy đơn hàng không thể hủy
**Input:**
- "hủy đơn đang giao"

**Expected:**
- Message: Không thể hủy, đề xuất từ chối khi nhận hàng hoặc yêu cầu đổi trả

---

## 7. ĐỔI TRẢ & BẢO HÀNH (Return & Exchange)

### Test Case 7.1: Yêu cầu đổi size
**Input:**
- "tôi muốn đổi size áo trong đơn #38"
- "đổi size M sang L"
- "exchange size"

**Expected:**
- Thu thập thông tin: order number, sản phẩm, lý do
- Tạo yêu cầu đổi trả

### Test Case 7.2: Báo lỗi sản phẩm
**Input:**
- "sản phẩm bị lỗi"
- "áo bị rách"
- "quality issue"

**Expected:**
- Thu thập thông tin chi tiết
- Tạo ticket hỗ trợ

---

## 8. GIỎ HÀNG (Cart Management)

### Test Case 8.1: Thêm sản phẩm vào giỏ
**Input:**
- "thêm áo meow vào giỏ hàng"
- "add to cart"
- "mua sản phẩm này"

**Expected:**
- Xác nhận thêm vào giỏ thành công
- Hiển thị số lượng trong giỏ (nếu có)

### Test Case 8.2: Xem giỏ hàng
**Input:**
- "xem giỏ hàng của tôi"
- "show cart"

**Expected:**
- Danh sách sản phẩm trong giỏ
- Tổng tiền (nếu có)

---

## 9. GEMINI AI FALLBACK

### Test Case 9.1: Câu hỏi tư vấn style
**Input:**
- "áo nào phù hợp với quần jean"
- "phối đồ thế nào cho đẹp"
- "tôi nên mặc gì đi dự tiệc"

**Expected:**
- Gemini AI trả lời tư vấn
- Không hallucinate về giá cả, tồn kho, đơn hàng

### Test Case 9.2: Câu hỏi ngoài phạm vi
**Input:**
- "thời tiết hôm nay thế nào"
- "tin tức mới nhất"
- "nấu món gì ngon"

**Expected:**
- Message: "Mình là trợ lý mua sắm thời trang..."
- Gợi ý các tính năng chatbot có thể hỗ trợ

### Test Case 9.3: Low confidence intent
**Input:**
- Câu hỏi mơ hồ, không rõ ràng

**Expected:**
- Gemini AI xử lý và phản hồi phù hợp
- Không trả về "I don't understand"

---

## 10. EDGE CASES & ERROR HANDLING

### Test Case 10.1: Input rỗng
**Input:**
- "" (empty string)
- "   " (spaces only)

**Expected:**
- Message yêu cầu nhập nội dung

### Test Case 10.2: Input quá dài
**Input:**
- Câu văn 500+ ký tự

**Expected:**
- Xử lý bình thường hoặc yêu cầu rút gọn

### Test Case 10.3: Special characters
**Input:**
- "áo @#$% meow"
- "đơn hàng <script>alert('xss')</script>"

**Expected:**
- Xử lý an toàn, không lỗi
- Sanitize input

### Test Case 10.4: Backend API lỗi
**Scenario:** Backend trả về 500 error

**Expected:**
- Message: "Oops, something went wrong..."
- Không crash chatbot

---

## 11. AUTHENTICATION & AUTHORIZATION

### Test Case 11.1: Truy cập tính năng cần đăng nhập
**Input (chưa login):**
- "xem đơn hàng"
- "xem giỏ hàng"
- "hủy đơn"

**Expected:**
- Message yêu cầu đăng nhập
- Không hiển thị thông tin nhạy cảm

### Test Case 11.2: Truy cập đơn hàng người khác
**Input (đã login):**
- "xem đơn 0000000001" (của user khác)

**Expected:**
- Message: "Không tìm thấy đơn hàng" hoặc "Access denied"

---

## 12. MULTI-LANGUAGE SUPPORT (nếu có)

### Test Case 12.1: Tiếng Việt
**Input:**
- "tìm áo thun"
- "đơn hàng của tôi"

**Expected:**
- Phản hồi bằng tiếng Việt

### Test Case 12.2: Tiếng Anh
**Input:**
- "find t-shirt"
- "my order"

**Expected:**
- Phản hồi bằng tiếng Anh (nếu support)

---

## 13. CONVERSATION FLOW

### Test Case 13.1: Multi-turn conversation
**Scenario:**
```
User: "tìm áo meow"
Bot: [Hiển thị kết quả]
User: "cái thứ 2 còn size L không"
Bot: [Kiểm tra stock size L của sản phẩm thứ 2]
User: "thêm vào giỏ"
Bot: [Thêm vào giỏ]
```

**Expected:**
- Context được giữ qua nhiều turn
- Hiểu được "cái thứ 2", "thêm vào giỏ"

### Test Case 13.2: Chuyển đổi topic
**Scenario:**
```
User: "tìm áo"
Bot: [Hiển thị kết quả]
User: "đơn hàng của tôi đâu"
Bot: [Chuyển sang order tracking]
```

**Expected:**
- Chuyển topic mượt mà
- Không bị confused

---

## 14. PERFORMANCE & UX

### Test Case 14.1: Response time
**Expected:**
- Text response < 2 giây
- Product search < 3 giây
- Order tracking < 3 giây

### Test Case 14.2: Message quality
**Expected:**
- Tiếng Việt chuẩn, không lỗi chính tả
- Giọng điệu thân thiện, sale nhẹ
- Emoji phù hợp, không spam

---

## 15. REGRESSION TESTS (Sau mỗi lần update)

### Checklist:
- [ ] Product search vẫn hoạt động
- [ ] Order tracking hiển thị đúng message theo trạng thái
- [ ] Confidence score phân loại đúng (>= 0.3 chính, < 0.3 đề xuất)
- [ ] Message templates ngẫu nhiên
- [ ] Không hiển thị thông tin tiền trong order tracking
- [ ] Gemini AI không hallucinate
- [ ] Error handling hoạt động
- [ ] Authentication check đúng

---

## CÁCH SỬ DỤNG TEST CASES

1. **Manual Testing:**
   - Copy từng input vào chatbot
   - Kiểm tra output có khớp với Expected không
   - Ghi lại kết quả (Pass/Fail)

2. **Automated Testing:**
   - Sử dụng `rasa test` với file test stories
   - Tạo test scripts cho API endpoints

3. **Regression Testing:**
   - Chạy lại toàn bộ test sau mỗi lần sửa code
   - Đảm bảo không phá vỡ tính năng cũ

---

**END OF DOCUMENT**
