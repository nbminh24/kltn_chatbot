# 📊 Rasa Chatbot Evaluation Reports

Hệ thống tự động tạo báo cáo đánh giá chatbot Rasa với 6 loại metrics chuyên nghiệp cho KLTN.

## 🎯 Các Báo Cáo

### 1️⃣ Dataset Statistics
- Thống kê tổng quan dataset NLU
- Số lượng intents, utterances
- Phân bố examples theo intent
- **File output**: `1_dataset_stats.png`, `dataset_stats.csv`

### 2️⃣ Intent Classification Metrics  
- Precision, Recall, F1-score per intent
- Macro/Weighted/Micro averages
- Top 15 intents performance
- **File output**: `2_intent_metrics.png`

### 3️⃣ Confusion Matrix
- Ma trận nhầm lẫn giữa các intents
- Phát hiện intents hay bị nhầm
- **File output**: `3_confusion_matrix.png`

### 4️⃣ Confidence Distribution
- Phân bố confidence score
- Correct vs Incorrect predictions
- Threshold analysis (default: 0.7)
- **File output**: `4_confidence_distribution.png`

### 5️⃣ Fallback Analysis (Rasa + Gemini)
- Tỷ lệ fallback cases
- LLM usage percentage
- Chứng minh hybrid approach
- **File output**: `5_fallback_analysis.png`

### 6️⃣ End-to-End Dialogue Accuracy
- Story flow accuracy
- Action prediction accuracy
- Overall E2E performance
- **File output**: `6_dialogue_accuracy.png`

## 🚀 Cài Đặt

```bash
cd evaluation
pip install -r requirements.txt
```

## 📝 Cách Sử Dụng

### Option 1: Chỉ tạo báo cáo (sử dụng kết quả có sẵn)

```bash
cd evaluation
python generate_all_reports.py
```

**Lưu ý**: Nếu chưa có kết quả test, sẽ tạo placeholder reports.

### Option 2: Chạy test + tạo báo cáo (KHUYẾN NGHỊ)

```bash
# Bước 1: Train model trước
cd ..
rasa train

# Bước 2: Chạy script với --run-tests
cd evaluation
python generate_all_reports.py --run-tests
```

**Thời gian**: 10-20 phút (tùy dataset size)

### Option 3: Chạy từng báo cáo riêng lẻ

```bash
# Report 1: Dataset Statistics
python dataset_statistics.py

# Report 2 & 3: Intent Metrics & Confusion Matrix
python confusion_matrix_analysis.py

# Report 4: Confidence Distribution
python confidence_distribution.py

# Report 5: Fallback Analysis
python fallback_analysis.py

# Report 6: Dialogue Accuracy
python dialogue_accuracy.py
```

## 📦 Output

Tất cả báo cáo được lưu trong: `evaluation/reports/`

```
evaluation/reports/
├── 1_dataset_stats.png
├── 2_intent_metrics.png
├── 3_confusion_matrix.png
├── 4_confidence_distribution.png
├── 5_fallback_analysis.png
├── 6_dialogue_accuracy.png
├── dataset_stats.csv
└── CHATBOT_EVALUATION_REPORT.pdf  (nếu có fpdf)
```

## 🔧 Tùy Chỉnh

### Thay đổi Confidence Threshold

Mặc định threshold = 0.7. Để thay đổi:

```python
# Trong generate_all_reports.py
cd = ConfidenceDistribution(threshold=0.75)  # Thay 0.7 → 0.75
fa = FallbackAnalysis(threshold=0.75)
```

### Thay đổi số lượng Cross-validation Folds

```python
# Trong generate_all_reports.py, method run_rasa_tests()
["rasa", "test", "nlu", "--cross-validation", "--folds", "5"]  # 5 → 10
```

## 📊 Dữ Liệu Cần Thiết

### Để có báo cáo thực tế (không phải placeholder):

1. **Report 1**: Chỉ cần `data/nlu.yml` ✅
2. **Report 2-5**: Cần chạy `rasa test nlu --cross-validation`
   - Output: `results/intent_report.json`, `results/intent_errors.json`
3. **Report 6**: Cần chạy `rasa test core`
   - Output: `results/story_report.json`

## 🎓 Sử Dụng Cho KLTN

### Các điểm quan trọng cần trình bày:

1. **Dataset Statistics** → Chứng minh data đủ lớn, balanced
2. **Intent Metrics** → F1-score cao (>0.85) cho các intent chính
3. **Confusion Matrix** → Phân tích intent nào hay nhầm, tại sao
4. **Confidence Distribution** → Giải thích threshold selection
5. **Fallback Analysis** → Chứng minh LLM chỉ là bổ trợ (~5-10%)
6. **Dialogue Accuracy** → E2E performance >80%

### Ví dụ Trích Dẫn:

> "Hệ thống đạt F1-score trung bình 0.92 trên 53 intents với 1000+ training examples. 
> Confidence threshold được chọn là 0.7 dựa trên phân tích distribution, cho phép 85% 
> cases được xử lý trực tiếp bởi Rasa NLU, trong khi LLM (Gemini) chỉ hỗ trợ 10% cases 
> mở rộng như tư vấn phong cách."

## ⚠️ Troubleshooting

### Lỗi: Module not found
```bash
pip install -r requirements.txt
```

### Lỗi: rasa command not found
```bash
# Đảm bảo virtual environment được activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Hoặc cài rasa
pip install rasa
```

### Placeholder reports xuất hiện
- Nguyên nhân: Chưa chạy `rasa test`
- Giải pháp: Chạy với `--run-tests` hoặc manual:
  ```bash
  rasa train
  rasa test nlu --cross-validation
  rasa test core
  python generate_all_reports.py
  ```

### PDF không được tạo
- Nguyên nhân: Thiếu fpdf hoặc Pillow
- Giải pháp: 
  ```bash
  pip install fpdf pillow
  ```
- Lưu ý: PNG reports vẫn có đầy đủ, PDF chỉ là tổng hợp

## 📞 Hỗ Trợ

Nếu gặp vấn đề, kiểm tra:
1. Virtual environment đã activate chưa
2. Rasa đã được train chưa (`models/` có model không)
3. Dependencies đã cài đầy đủ chưa
4. Python version >= 3.8

## 📄 License

MIT License - Tự do sử dụng cho KLTN và nghiên cứu.
