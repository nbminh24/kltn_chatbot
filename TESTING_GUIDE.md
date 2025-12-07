# 🧪 HƯỚNG DẪN TEST CHATBOT

**Ngày:** 07/12/2024  
**Trạng thái:** Sẵn sàng test integration

---

## ✅ ĐÃ HOÀN THÀNH

### 1. API Client ✅
- Fixed endpoints và headers
- Thêm 7 methods mới cho chatbot internal APIs
- File: `actions/api_client.py`

### 2. Domain.yml ✅
- 29 intents theo specification
- Updated entities & slots
- 18 custom actions khai báo
- File: `domain.yml` (backup: `domain.yml.backup`)

### 3. Actions ✅
- File cũ: `actions/actions.py` (giữ nguyên)
- File mới: `actions/actions_chatbot.py` (14 actions mới)
- Hỗ trợ: Vietnamese, slot filling, error handling

### 4. Config ✅
- Language: Vietnamese (vi)
- Bilingual support
- File: `config.yml`

---

## 🚀 CÁCH CHẠY TEST

### Bước 1: Chuẩn Bị Môi Trường

```bash
# Activate virtual environment (nếu chưa)
cd c:\Users\USER\Downloads\kltn_chatbot
.\venv\Scripts\activate

# Cài đặt dependencies (nếu chưa)
pip install -r requirements.txt
```

### Bước 2: Kiểm Tra Backend

```bash
# Đảm bảo backend đang chạy
# Backend URL: http://localhost:3001
# Test bằng cách mở browser hoặc curl
```

Kiểm tra endpoints:
- ✅ GET http://localhost:3001/products
- ✅ POST http://localhost:3001/api/chatbot/cart/add (với X-Internal-Api-Key header)

### Bước 3: Train Rasa Model

```bash
# Train model lần đầu
rasa train

# Nếu có lỗi, xem log để debug
# Model sẽ được lưu trong thư mục models/
```

### Bước 4: Chạy Action Server

**Terminal 1 - Action Server:**
```bash
rasa run actions --debug
```

Kết quả mong đợi:
```
✓ Action endpoint is up and running on http://localhost:5055
✓ Actions:
  - action_search_products
  - action_add_to_cart
  - action_add_to_wishlist
  - action_cancel_order
  - ...
```

### Bước 5: Chạy Rasa Server

**Terminal 2 - Rasa Server:**
```bash
rasa run --enable-api --debug
```

Kết quả mong đợi:
```
✓ Rasa server is up and running on http://localhost:5005
```

### Bước 6: Test với Rasa Shell

**Terminal 3 - Interactive Test:**
```bash
rasa shell --debug
```

---

## 🧪 TEST CASES

### Test Case 1: Chào Hỏi
**User:** Hi  
**Expected:** Chào hỏi thân thiện  
**Intent:** greet

### Test Case 2: Tìm Sản Phẩm
**User:** Tìm áo thun đen  
**Expected:** Danh sách sản phẩm áo thun đen  
**Intent:** product_search_text  
**API Called:** GET /products?search=áo%20thun&color=đen

### Test Case 3: Kiểm Tra Size Chart
**User:** Cho xem bảng size áo  
**Expected:** Link/image bảng size áo  
**Intent:** consult_size_chart  
**API Called:** GET /api/chatbot/size-chart/shirt

### Test Case 4: Tư Vấn Size
**User:** Mình cao 1m7, nặng 65kg nên mặc size gì?  
**Expected:** Gợi ý size M hoặc L  
**Intent:** consult_size_advice  
**API Called:** POST /api/chatbot/size-advice

### Test Case 5: Thêm Vào Giỏ (Slot Filling)
**User:** Thêm vào giỏ hàng  
**Bot:** Bạn muốn size nào nhỉ?  
**User:** Size M  
**Bot:** Màu nào bạn nhỉ?  
**User:** Màu đen  
**Expected:** Đã thêm vào giỏ hàng!  
**Intent:** action_add_cart  
**API Called:** POST /api/chatbot/cart/add

### Test Case 6: Hủy Đơn Hàng
**User:** Hủy đơn hàng #123  
**Expected:** Xác nhận hủy đơn thành công  
**Intent:** order_cancel_request  
**API Called:** POST /api/chatbot/orders/123/cancel

### Test Case 7: Gợi Ý Theo Ngữ Cảnh
**User:** Đi đám cưới mặc gì?  
**Expected:** Gợi ý outfit cho đám cưới  
**Intent:** product_recommend_context  
**API Called:** GET /api/chatbot/products/recommend?context=wedding

### Test Case 8: Hỏi Gemini (Fallback)
**User:** Thời tiết hôm nay thế nào?  
**Expected:** Trả lời từ Gemini AI  
**Intent:** out_of_scope_gemini  
**API Called:** POST /api/chatbot/gemini/ask

### Test Case 9: Kiểm Tra Tồn Kho
**User:** Còn size M màu đen không?  
**Expected:** Thông báo còn/hết hàng  
**Intent:** product_check_stock  
**API Called:** GET /products/availability?size=M&color=đen

### Test Case 10: Tạo Support Ticket
**User:** Tôi muốn gặp nhân viên  
**Expected:** Ticket đã được tạo  
**Intent:** faq_contact_human  
**API Called:** POST /support-tickets

---

## 🐛 DEBUG CHECKLIST

### Nếu Action Server Không Chạy:
- [ ] Check Python version (>= 3.8)
- [ ] Check dependencies đã cài đủ chưa
- [ ] Check file `actions/__init__.py` có import đúng không
- [ ] Xem logs trong terminal

### Nếu API Calls Lỗi:
- [ ] Check Backend đang chạy
- [ ] Check INTERNAL_API_KEY đúng chưa (trong .env)
- [ ] Check URL endpoints
- [ ] Check logs của backend

### Nếu Intent Không Nhận Diện:
- [ ] Cần train lại model: `rasa train nlu`
- [ ] Check NLU training data có đủ examples chưa
- [ ] Test với `rasa shell nlu` để xem intent confidence

### Nếu Entities Không Extract:
- [ ] Check NLU training data có mark entities
- [ ] Train lại model
- [ ] Xem debug logs

---

## 📊 METRICS CẦN THEO DÕI

### Performance:
- [ ] API response time < 2s
- [ ] Action execution time < 3s
- [ ] Overall response time < 5s

### Accuracy:
- [ ] Intent recognition > 85%
- [ ] Entity extraction > 80%
- [ ] Fallback rate < 20%

### Integration:
- [ ] Backend API success rate > 95%
- [ ] Error handling works properly
- [ ] Slot filling completes successfully

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 1. Slot Filling
- `action_add_to_cart` cần có size và color
- Bot sẽ hỏi lại nếu thiếu thông tin
- Slots sẽ được reset sau khi hoàn thành

### 2. Customer ID
- Một số actions cần customer_id (login required)
- Frontend phải set slot `customer_id` khi user login
- Guest users sẽ nhận thông báo cần đăng nhập

### 3. API Keys
- INTERNAL_API_KEY phải match với backend
- Không expose key ra public
- Check file `.env` có đầy đủ keys

### 4. Backend Dependencies
- Backend phải đã implement đầy đủ 7 APIs
- Database phải có sample data để test
- Promotions, products phải có trong DB

---

## 📝 NEXT STEPS SAU KHI TEST

### Nếu Test OK:
1. ✅ Update NLU training data với more examples
2. ✅ Add more stories and rules
3. ✅ Optimize responses
4. ✅ Add more error handling
5. ✅ Performance tuning

### Nếu Có Lỗi:
1. 📝 Ghi lại lỗi cụ thể
2. 🔍 Check logs (backend + rasa + actions)
3. 🐛 Debug từng component riêng lẻ
4. 🔧 Fix và test lại
5. 📊 Verify fix hoạt động

---

**Ready to test!** 🚀

Chạy theo thứ tự:
1. Backend server
2. `rasa run actions --debug`
3. `rasa run --enable-api --debug`
4. `rasa shell --debug` (hoặc test qua API)

Good luck! 🍀
