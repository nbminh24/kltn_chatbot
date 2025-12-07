# 📊 BẢNG LOGIC INTENT & XỬ LÝ - E-COMMERCE CHATBOT

## MỤC LỤC
- [1. Nhóm Chào Hỏi & Giao Tiếp Cơ Bản](#1-nhóm-chào-hỏi--giao-tiếp-cơ-bản)
- [2. Nhóm Tìm Kiếm & Sản Phẩm](#2-nhóm-tìm-kiếm--sản-phẩm)
- [3. Nhóm Size & Tư Vấn](#3-nhóm-size--tư-vấn)
- [4. Nhóm Hành Động Mua Hàng](#4-nhóm-hành-động-mua-hàng)
- [5. Nhóm Đơn Hàng & Hậu Mãi](#5-nhóm-đơn-hàng--hậu-mãi)
- [6. Nhóm Chính Sách & FAQ](#6-nhóm-chính-sách--faq)
- [7. Nhóm Hệ Thống & Fallback](#7-nhóm-hệ-thống--fallback)

---

## 1. NHÓM CHÀO HỎI & GIAO TIẾP CƠ BẢN

**Mục tiêu:** Tạo thiện cảm, giữ chân khách hàng

### 1.1. greet - Chào hỏi

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `greet` |
| **Ví dụ User** | "Hi", "Chào shop", "Hello", "Có ai không" |
| **Entities** | - |
| **Logic** | Random chọn 1 trong các câu chào có sẵn |
| **Backend API** | Không cần |
| **Response Template** | "Xin chào! Mình là trợ lý ảo của shop. Bạn cần tìm gì hôm nay? 😊" |
| **UI Component** | Text bubble + Sticker "Xin chào" |
| **Notes** | First impression, phải friendly |

---

### 1.2. goodbye - Tạm biệt

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `goodbye` |
| **Ví dụ User** | "Bye nhé", "Thôi mình đi đây", "Hẹn gặp lại" |
| **Entities** | - |
| **Logic** | Reset context hội thoại. Lưu session history vào DB. |
| **Backend API** | Không cần |
| **Response Template** | "Tạm biệt bạn! Hẹn gặp lại nhé 👋" |
| **UI Component** | Text bubble + Sticker "Tạm biệt" |
| **Notes** | Clean up conversation state |

---

### 1.3. thanks - Cảm ơn

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `thanks` |
| **Ví dụ User** | "Cảm ơn", "Thanks shop", "Ok được rồi" |
| **Entities** | - |
| **Logic** | Trả lời lịch sự + Khuyến khích mua hàng |
| **Backend API** | Không cần |
| **Response Template** | "Không có gì ạ! Mong bạn ủng hộ shop nha 💙" |
| **UI Component** | Text bubble + Sticker "Cảm ơn" |
| **Notes** | - |

---

### 1.4. bot_identity - Hỏi về bot

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `bot_identity` |
| **Ví dụ User** | "Bạn là ai?", "Người máy à?", "Bot à?" |
| **Entities** | - |
| **Logic** | Giới thiệu về bot, tính năng có thể làm gì |
| **Backend API** | Không cần |
| **Response Template** | "Mình là trợ lý ảo của shop! Mình có thể giúp bạn tìm sản phẩm, tư vấn size, tra đơn hàng và nhiều thứ khác nữa 🤖" |
| **UI Component** | Text bubble |
| **Notes** | - |

---

## 2. NHÓM TÌM KIẾM & SẢN PHẨM

**Mục tiêu:** Giúp khách tìm thấy món đồ ưng ý

### 2.1. product_search_text - Tìm sản phẩm theo text

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `product_search_text` |
| **Ví dụ User** | "Tìm váy trắng", "Giày nike nam", "Có áo khoác không" |
| **Entities** | `category` (váy), `color` (trắng), `brand` (nike), `gender` (nam) |
| **Logic** | Extract entities → Call Backend API search |
| **Backend API** | `GET /api/chatbot/products/search?category={}&color={}&brand={}` |
| **Response Template** | "Mình tìm thấy {count} sản phẩm {category} {color} cho bạn:" + Product cards |
| **UI Component** | Text + Product Carousel (max 10 items) |
| **Notes** | - Nếu không tìm thấy: Gợi ý sản phẩm tương tự<br>- Có pagination nếu >10 results |

---

### 2.2. product_search_image - Tìm sản phẩm bằng ảnh

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `product_search_image` |
| **Ví dụ User** | (User gửi ảnh) "Tìm cái này", "Mẫu này còn không" |
| **Entities** | `image` (file) |
| **Logic** | Frontend upload ảnh → Backend AI service (pgvector) → Return similar products |
| **Backend API** | `POST /api/chatbot/ai/image-search` (multipart/form-data) |
| **Response Template** | - Nếu tìm thấy: "Đây là những sản phẩm tương tự:" + Cards<br>- Nếu không: "Xin lỗi, shop chưa có sản phẩm này. Bạn có thể xem:" + Gợi ý |
| **UI Component** | Product Carousel |
| **Notes** | **Quan trọng:** Nếu phát hiện đồ nữ hoặc không phải thời trang → Thông báo "Shop chỉ bán thời trang nam" |

---

### 2.3. product_ask_info - Hỏi chi tiết sản phẩm

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `product_ask_info` |
| **Ví dụ User** | "Chất vải gì?", "Xuất xứ đâu?", "Giá bao nhiêu?" |
| **Entities** | `info_type` (material/price/origin), `product_id` (from context) |
| **Logic** | **Context Check:** Lấy `current_product_id` từ session context → Query thông tin field tương ứng |
| **Backend API** | `GET /api/chatbot/products/:id` |
| **Response Template** | - Material: "Sản phẩm này làm từ {material}"<br>- Price: "Giá: {price}đ"<br>- Origin: "Xuất xứ: {origin}" |
| **UI Component** | Text bubble |
| **Notes** | - Nếu chưa có context product → Hỏi lại "Bạn muốn hỏi về sản phẩm nào?"<br>- Parse `attributes` JSON field |

---

### 2.4. product_check_stock - Kiểm tra tồn kho

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `product_check_stock` |
| **Ví dụ User** | "Còn hàng không?", "Size M còn không?", "Màu đen còn không?" |
| **Entities** | `product_id`, `size`, `color` |
| **Logic** | **Slot Filling:** Nếu thiếu size/color → Hỏi lại. Nếu đủ → Query inventory |
| **Backend API** | `GET /api/chatbot/products/:id/stock?size={}&color={}` |
| **Response Template** | - Còn: "Còn {quantity} sản phẩm size {size} màu {color}"<br>- Hết: "Size này đã hết hàng. Bạn có muốn đăng ký thông báo khi có hàng?" |
| **UI Component** | Text + Button "Thông báo khi có hàng" (nếu hết) |
| **Notes** | **Real-time check** từ `product_variants.total_stock - reserved_stock` |

---

### 2.5. ask_promotion - Hỏi về khuyến mãi

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `ask_promotion` |
| **Ví dụ User** | "Có mã giảm giá không?", "Đang sale gì không?", "Flash sale hôm nay" |
| **Entities** | - |
| **Logic** | Query danh sách promotions active (start_date <= now <= end_date) |
| **Backend API** | `GET /api/chatbot/promotions/active` |
| **Response Template** | "Hiện shop đang có {count} chương trình khuyến mãi:" + List promotions + Product cards |
| **UI Component** | Promo banner + Product carousel (flash sale products) |
| **Notes** | Group theo loại: Voucher, Flash Sale, Bundle Deal |

---

### 2.6. product_recommend_context - Gợi ý sản phẩm theo ngữ cảnh

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `product_recommend_context` |
| **Ví dụ User** | "Đi đám cưới mặc gì?", "Tư vấn đồ đi biển", "Outfit đi làm" |
| **Entities** | `context` (đám cưới, đi biển, đi làm) |
| **Logic** | Map keyword với `collection_tag` trong DB hoặc AI recommendation |
| **Backend API** | `GET /api/chatbot/products/recommend?context={}` |
| **Response Template** | "Với {context}, mình gợi ý bạn những món này:" + Cards |
| **UI Component** | Product carousel với nút action |
| **Notes** | **Future:** Sử dụng AI recommendation engine |

---

## 3. NHÓM SIZE & TƯ VẤN

**Mục tiêu:** Giảm tỷ lệ đổi trả do sai size

### 3.1. consult_size_chart - Xem bảng size

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `consult_size_chart` |
| **Ví dụ User** | "Cho xem bảng size", "Size tính thế nào", "Bảng size áo" |
| **Entities** | `category` (áo/quần/giày - optional) |
| **Logic** | Lấy ảnh bảng size từ static resources hoặc DB |
| **Backend API** | `GET /api/chatbot/size-chart/:category` hoặc static URL |
| **Response Template** | "Đây là bảng size {category} của shop:" + Image |
| **UI Component** | Image viewer (zoomable) |
| **Notes** | Có thể lưu URL ảnh trong config hoặc `pages` table |

---

### 3.2. consult_size_advice - Tư vấn size cá nhân

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `consult_size_advice` |
| **Ví dụ User** | "1m6 50kg mặc size gì?", "60kg vừa size L không?" |
| **Entities** | `height` (1m6), `weight` (50kg), `size` (L - optional) |
| **Logic** | **Slot Filling:** Hỏi thiếu height/weight → So sánh với range size trong logic rules |
| **Backend API** | `POST /api/chatbot/size-advice` (body: {height, weight}) |
| **Response Template** | "Với chiều cao {height} và cân nặng {weight}, bạn mặc size {recommended_size} là vừa đẹp ạ" |
| **UI Component** | Text bubble |
| **Notes** | **Logic rules:** <br>- 1m6-1m7, 50-60kg → Size M<br>- Custom theo product category |

---

## 4. NHÓM HÀNH ĐỘNG MUA HÀNG

**Mục tiêu:** Chốt đơn nhanh (Conversion)

### 4.1. action_add_cart - Thêm vào giỏ hàng

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `action_add_cart` |
| **Ví dụ User** | "Thêm vào giỏ", "Lấy cái này màu đỏ", "Cho vào cart" |
| **Entities** | `product_id`, `size`, `color`, `quantity` |
| **Logic** | **Slot Filling (Quan trọng):**<br>1. Check xem đã có Size/Màu chưa?<br>2. Thiếu → Response hỏi lại<br>3. Đủ → Gọi API thêm vào cart |
| **Backend API** | `POST /api/chatbot/cart/add` (body: {customer_id, variant_id, quantity}) |
| **Response Template** | - Thiếu slot: "Bạn muốn size nào nhỉ?" + Size chips<br>- Thành công: "Đã thêm vào giỏ hàng! 🛒" |
| **UI Component** | - Thiếu: Size/Color selection chips<br>- Thành công: Toast notification + Cart badge tăng |
| **Notes** | **Quan trọng:** Phải có đủ variant info (size + color) mới add được |

---

### 4.2. action_buy_now - Mua ngay

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `action_buy_now` |
| **Ví dụ User** | "Mua luôn", "Thanh toán cái này", "Chốt đơn" |
| **Entities** | `product_id`, `size`, `color`, `quantity` |
| **Logic** | Tương tự `action_add_cart` nhưng redirect sang checkout |
| **Backend API** | `POST /api/chatbot/checkout/create` (tạo checkout session tạm) |
| **Response Template** | "OK! Mình chuyển bạn sang trang thanh toán nhé..." |
| **UI Component** | **Redirect:** Mở tab mới sang `/checkout?variant_id={}&quantity={}` |
| **Notes** | **Luồng tự động:** Open checkout page với pre-filled product |

---

### 4.3. action_add_wishlist - Lưu yêu thích

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `action_add_wishlist` |
| **Ví dụ User** | "Thêm vào wishlist", "Lưu lại nhé", "Like sản phẩm này" |
| **Entities** | `product_id` |
| **Logic** | Check login → Nếu chưa login yêu cầu login → Add to wishlist |
| **Backend API** | `POST /api/chatbot/wishlist/add` (body: {customer_id, variant_id}) |
| **Response Template** | - Chưa login: "Bạn cần đăng nhập để lưu sản phẩm yêu thích nhé" + Login button<br>- Thành công: "Đã lưu vào wishlist ❤️" |
| **UI Component** | Heart icon animation (fill red) |
| **Notes** | Require authentication |

---

## 5. NHÓM ĐƠN HÀNG & HẬU MÃI

**Mục tiêu:** CSKH tự động, giảm tải cho nhân viên

### 5.1. order_status_check - Tra cứu đơn hàng

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `order_status_check` |
| **Ví dụ User** | "Đơn của tôi đâu rồi?", "Bao giờ giao?", "Check đơn hàng" |
| **Entities** | `order_id` (optional) |
| **Logic** | Lấy `customer_id` từ session → Query đơn hàng gần nhất (hoặc theo order_id) |
| **Backend API** | `GET /api/chatbot/orders/customer/:customer_id` |
| **Response Template** | "Đơn hàng #{order_id} của bạn:<br>- Trạng thái: {status}<br>- Dự kiến giao: {estimated_delivery}" |
| **UI Component** | Order status card với timeline (Pending → Processing → Shipping → Delivered) |
| **Notes** | - Yêu cầu login<br>- Hiển thị tracking number nếu có |

---

### 5.2. order_cancel_request - Yêu cầu hủy đơn

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `order_cancel_request` |
| **Ví dụ User** | "Tôi muốn hủy đơn", "Đặt nhầm hủy giúp mình", "Cancel order" |
| **Entities** | `order_id` (optional) |
| **Logic** | **Check status:**<br>- "pending" / "processing": Cho phép hủy → Update status<br>- "shipping" / "delivered": Từ chối hủy → Tạo ticket |
| **Backend API** | `POST /api/chatbot/orders/:id/cancel` |
| **Response Template** | - Thành công: "Đã hủy đơn hàng #{order_id} thành công"<br>- Thất bại: "Đơn hàng đang giao, không thể hủy. Bạn có thể từ chối nhận hàng hoặc liên hệ admin" + Button "Tạo ticket" |
| **UI Component** | Text + Action button |
| **Notes** | Auto create support ticket nếu không hủy được |

---

### 5.3. order_feedback - Gửi phản hồi/khiếu nại

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `order_feedback` |
| **Ví dụ User** | "Hàng rách rồi", "Giao sai mẫu", "Shipper thái độ", "Đơn hàng có vấn đề" |
| **Entities** | `order_id`, `issue_type` (damaged/wrong_item/attitude) |
| **Logic** | **Sentiment Analysis:** Detect negative<br>→ Thu thập thông tin chi tiết<br>→ Tạo support ticket với priority HIGH |
| **Backend API** | `POST /api/chatbot/support-tickets` (body: {subject, message, priority: "high"}) |
| **Response Template** | "Mình rất xin lỗi về sự cố này 😔. Đã ghi nhận phản hồi của bạn. Ticket #{ticket_code}. Admin sẽ liên hệ trong 24h." |
| **UI Component** | Sticker "Xin lỗi" + Text thông báo |
| **Notes** | **Keywords nghiêm trọng:** rách, hỏng, sai, giận, thất vọng → Auto priority HIGH |

---

## 6. NHÓM CHÍNH SÁCH & FAQ

**Mục tiêu:** Trả lời chính xác thắc mắc cụ thể

### 6.1. faq_store_info - Thông tin cửa hàng

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_store_info` |
| **Ví dụ User** | "Shop ở đâu?", "Mấy giờ đóng cửa?", "Có cửa hàng HN không?" |
| **Entities** | - |
| **Logic** | Trả về thông tin static từ config/database |
| **Backend API** | `GET /api/chatbot/store-info` hoặc static response |
| **Response Template** | "Thông tin cửa hàng:<br>📍 Địa chỉ: {address}<br>⏰ Giờ làm việc: {hours}<br>📞 Hotline: {phone}" |
| **UI Component** | Text + Google Maps link button |
| **Notes** | Lưu trong `pages` table hoặc config file |

---

### 6.2. faq_contact_human - Gặp nhân viên

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_contact_human` |
| **Ví dụ User** | "Cho sđt hotline", "Muốn gặp người tư vấn", "Chat với admin" |
| **Entities** | - |
| **Logic** | **Check giờ làm việc:**<br>- Trong giờ: Tạo ticket priority normal<br>- Ngoài giờ: Thông báo để lại tin nhắn |
| **Backend API** | `POST /api/chatbot/support-tickets` |
| **Response Template** | "Mình đã ghi nhận yêu cầu. Admin sẽ liên hệ bạn qua email trong vòng 2-4h làm việc. Ticket #{ticket_code}" |
| **UI Component** | Button "Gọi Hotline" + Button "Zalo" |
| **Notes** | **Không có realtime chat** - Chỉ tạo ticket |

---

### 6.3. faq_payment_method - Phương thức thanh toán

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_payment_method` |
| **Ví dụ User** | "Có thanh toán thẻ không?", "Thanh toán qua Momo được không?" |
| **Entities** | - |
| **Logic** | List các phương thức active |
| **Backend API** | Static response hoặc `GET /api/chatbot/payment-methods` |
| **Response Template** | "Shop hỗ trợ các hình thức:<br>✅ COD (Tiền mặt)<br>✅ Chuyển khoản<br>✅ Momo/ZaloPay<br>✅ Visa/Mastercard" |
| **UI Component** | Text + Icons các cổng thanh toán |
| **Notes** | - |

---

### 6.4. faq_payment_cod - Hỏi về Ship COD

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_payment_cod` |
| **Ví dụ User** | "Có ship COD không?", "Nhận hàng trả tiền được không?" |
| **Entities** | - |
| **Logic** | Trả lời chính sách COD |
| **Backend API** | Không cần |
| **Response Template** | "Có ạ! Shop hỗ trợ COD toàn quốc. Đơn >2 triệu cần đặt cọc trước 30%." |
| **UI Component** | Text |
| **Notes** | Configurable policy |

---

### 6.5. faq_shipping_fee - Hỏi phí ship

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_shipping_fee` |
| **Ví dụ User** | "Ship về Đà Nẵng nhiêu?", "Phí ship nội thành?" |
| **Entities** | `city` (optional) |
| **Logic** | Trả về thông tin phí ship chung hoặc theo vùng |
| **Backend API** | `GET /api/chatbot/shipping-fee?city={}` |
| **Response Template** | "Phí ship:<br>- Nội thành HN/HCM: 30k<br>- Tỉnh: 35-50k<br>- Miễn phí đơn >500k" |
| **UI Component** | Text |
| **Notes** | - |

---

### 6.6. faq_shipping_time - Thời gian giao hàng

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_shipping_time` |
| **Ví dụ User** | "Về Cần Thơ mất mấy ngày?", "Bao lâu nhận được?" |
| **Entities** | `city` (optional) |
| **Logic** | Trả về ước tính thời gian |
| **Backend API** | Không cần |
| **Response Template** | "Thời gian giao hàng:<br>- Nội thành: 1-2 ngày<br>- Tỉnh: 2-4 ngày<br>- Vùng xa: 4-7 ngày" |
| **UI Component** | Text |
| **Notes** | - |

---

### 6.7. faq_shipping_check - Cho xem hàng trước (Đồng kiểm)

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_shipping_check` |
| **Ví dụ User** | "Được xem hàng trước không?", "Cho thử không?" |
| **Entities** | - |
| **Logic** | Trả lời chính sách |
| **Backend API** | Không cần |
| **Response Template** | "Shop cho phép đồng kiểm (xem hàng trước khi thanh toán). Không cho thử." |
| **UI Component** | Text |
| **Notes** | - |

---

### 6.8. faq_return_policy - Chính sách đổi trả

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_return_policy` |
| **Ví dụ User** | "Đổi trả thế nào?", "Được đổi size không?", "Trả hàng trong bao lâu" |
| **Entities** | - |
| **Logic** | Trả về quy định đổi trả |
| **Backend API** | Static hoặc `GET /api/chatbot/policies/return` |
| **Response Template** | "Chính sách đổi trả:<br>✅ Trong 7 ngày<br>✅ Còn nguyên tem<br>✅ Chưa qua sử dụng<br>❌ Không đổi đồ sale >50%" |
| **UI Component** | Text |
| **Notes** | - |

---

### 6.9. faq_product_auth - Hỏi hàng chính hãng

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `faq_product_auth` |
| **Ví dụ User** | "Hàng auth hay fake?", "Có bảo hành không?" |
| **Entities** | - |
| **Logic** | Trả lời cam kết |
| **Backend API** | Không cần |
| **Response Template** | "Shop cam kết 100% hàng chính hãng. Có bảo hành 6 tháng với sản phẩm lỗi do nhà sản xuất." |
| **UI Component** | Text + Sticker "Uy tín" |
| **Notes** | - |

---

## 7. NHÓM HỆ THỐNG & FALLBACK

**Mục tiêu:** Xử lý ngoại lệ

### 7.1. out_of_scope_gemini - Hỏi chuyện ngoài lề

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `out_of_scope_gemini` |
| **Ví dụ User** | "Thời tiết hôm nay?", "Kể chuyện cười", "Ai thắng bóng đá?" |
| **Entities** | - |
| **Logic** | Gọi Gemini API với prompt: "Trả lời ngắn gọn, thân thiện và cố gắng lái câu chuyện về việc mua sắm thời trang" |
| **Backend API** | `POST /api/chatbot/gemini/ask` (body: {message}) |
| **Response Template** | [Gemini response] + "Nhân tiện bạn có cần tìm đồ gì không?" |
| **UI Component** | Text |
| **Notes** | **Rate limit:** Tối đa 5 calls/session để tránh abuse |

---

### 7.2. fallback - Không hiểu

| **Thông tin** | **Chi tiết** |
|--------------|-------------|
| **Intent** | `fallback` |
| **Ví dụ User** | (Câu vô nghĩa/Lỗi) |
| **Entities** | - |
| **Logic** | **Đếm số lần fallback liên tiếp:**<br>- Lần 1: Xin lỗi + Gợi ý lại menu<br>- Lần 2+: Auto hiển thị "Gặp nhân viên hỗ trợ" |
| **Backend API** | Không cần (hoặc tạo ticket sau 2 lần) |
| **Response Template** | - Lần 1: "Xin lỗi mình chưa hiểu. Bạn có thể hỏi mình về sản phẩm, đơn hàng, hoặc chính sách nhé!"<br>- Lần 2: "Có vẻ mình không giúp được. Bạn muốn gặp nhân viên không?" + Button |
| **UI Component** | Sticker "Bối rối" + Quick reply menu |
| **Notes** | **Metric:** Track fallback rate để cải thiện training data |

---

## 📊 INTENT SUMMARY TABLE

| **Nhóm** | **Số lượng Intent** | **Backend API Required** |
|---------|-------------------|------------------------|
| Chào hỏi & Giao tiếp | 4 | 0 (Static responses) |
| Tìm kiếm & Sản phẩm | 6 | 5 (Search, Detail, Stock, Promo, Recommend) |
| Size & Tư vấn | 2 | 2 (Size chart, Size advice) |
| Hành động mua hàng | 3 | 3 (Cart, Checkout, Wishlist) |
| Đơn hàng & Hậu mãi | 3 | 2 (Order query, Cancel) |
| Chính sách & FAQ | 9 | 0-2 (Mostly static) |
| Fallback | 2 | 1 (Gemini API) |
| **TOTAL** | **29** | **~15 APIs** |

---

## 🎯 PRIORITY IMPLEMENTATION

### Phase 1 (MVP)
1. ✅ product_search_text
2. ✅ product_ask_info
3. ✅ product_check_stock
4. ✅ action_add_cart
5. ✅ order_status_check
6. ✅ faq_contact_human (create ticket)
7. ✅ All FAQ static responses

### Phase 2
1. 🔄 product_search_image
2. 🔄 product_recommend_context
3. 🔄 consult_size_advice
4. 🔄 action_buy_now
5. 🔄 order_cancel_request

### Phase 3
1. 📅 out_of_scope_gemini
2. 📅 Advanced recommendations

---

**Ngày tạo:** 2024-12-07  
**Version:** 1.0  
**Tổng số Intent:** 29
