# 🚀 QUICK START - TẠO BÁO CÁO ĐÁNH GIÁ

## ⚡ CÁCH NHANH NHẤT (1 lệnh duy nhất)

```powershell
# Bước 1: Mở PowerShell tại ROOT folder của project
cd c:\Users\USER\Downloads\kltn_chatbot

# Bước 2: Activate virtual environment
venv\Scripts\activate

# Bước 3: Chạy lệnh này (chọn 1 trong 2)

# Option A: Chạy test + tạo báo cáo (KHUYẾN NGHỊ - 15-20 phút)
python generate_reports.py --run-tests

# Option B: Chỉ tạo báo cáo (dùng data có sẵn - 1 phút)
python generate_reports.py
```

**XONG!** Báo cáo sẽ có tại: `evaluation/reports/`

---

## 📋 CHECKLIST TRƯỚC KHI CHẠY

✅ **Đúng folder**: Phải ở `c:\Users\USER\Downloads\kltn_chatbot` (root folder)
✅ **Virtual env**: Đã activate `venv\Scripts\activate`
✅ **Model trained**: Đã chạy `rasa train` thành công

---

## 🎯 KẾT QUẢ

Sau khi chạy xong, bạn sẽ có:

```
evaluation/reports/
├── 1_dataset_stats.png          ← 53 intents statistics
├── 2_intent_metrics.png         ← TẤT CẢ 53 intents metrics
├── 3_confusion_matrix.png       ← Ma trận 53x53
├── 4_confidence_distribution.png
├── 5_fallback_analysis.png
├── 6_dialogue_accuracy.png
└── CHATBOT_EVALUATION_REPORT.pdf ← PDF tổng hợp
```

---

## ⚠️ NẾU GẶP LỖI

### Lỗi: "No such file or directory: 'data/nlu.yml'"

**Nguyên nhân**: Đang chạy sai folder

**Giải pháp**:
```powershell
# Quay về root folder
cd c:\Users\USER\Downloads\kltn_chatbot

# Kiểm tra có thư mục data/ không
dir data

# Nếu có → chạy lại
python generate_reports.py --run-tests
```

---

### Lỗi: "ModuleNotFoundError: No module named 'pandas'"

**Giải pháp**:
```powershell
pip install -r evaluation/requirements.txt
```

---

### Lỗi: scikit-learn version conflict

**Giải pháp**:
```powershell
pip install --force-reinstall "scikit-learn>=0.22,<1.2"
```

---

## 💡 TÓM TẮT

1️⃣ **Mở terminal tại ROOT folder** (`c:\Users\USER\Downloads\kltn_chatbot`)
2️⃣ **Activate venv**: `venv\Scripts\activate`
3️⃣ **Chạy**: `python generate_reports.py --run-tests`
4️⃣ **Chờ 15-20 phút** ☕
5️⃣ **Xem báo cáo** tại `evaluation/reports/`

---

## 📞 CẦN TRỢ GIÚP?

Kiểm tra:
- ✅ Có file `data/nlu.yml` không? → Phải ở root folder
- ✅ Có folder `models/` với model đã train không?
- ✅ Virtual environment đã activate chưa?

Nếu tất cả đều OK → Chạy: `python generate_reports.py --run-tests`
