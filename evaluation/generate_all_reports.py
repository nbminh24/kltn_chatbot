import os
import sys
from pathlib import Path
import subprocess
import time

from dataset_statistics import DatasetStatistics
from confusion_matrix_analysis import ConfusionMatrixAnalysis
from confidence_distribution import ConfidenceDistribution
from fallback_analysis import FallbackAnalysis
from dialogue_accuracy import DialogueAccuracy

class ReportGenerator:
    def __init__(self, run_tests=False):
        self.run_tests = run_tests
        self.reports_dir = Path("evaluation/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def print_header(self, text):
        print("\n" + "="*80)
        print(f"  {text}")
        print("="*80)
    
    def run_rasa_tests(self):
        self.print_header("Bước 1: Chạy Rasa Tests")
        
        print("\n🔄 Đang chạy NLU testing với cross-validation...")
        print("⏱️ Quá trình này có thể mất 5-15 phút tùy dataset size...\n")
        
        try:
            result = subprocess.run(
                ["rasa", "test", "nlu", "--cross-validation", "--folds", "5"],
                capture_output=True,
                text=True,
                timeout=900
            )
            
            if result.returncode == 0:
                print("✅ NLU testing hoàn thành!")
            else:
                print(f"⚠️ NLU testing có warning: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⚠️ NLU testing timeout - có thể dataset quá lớn")
        except FileNotFoundError:
            print("❌ Không tìm thấy lệnh 'rasa'. Đảm bảo rasa đã được cài đặt.")
            print("ℹ️ Chạy: pip install rasa")
            return False
        except Exception as e:
            print(f"❌ Lỗi khi chạy NLU test: {e}")
            return False
        
        print("\n🔄 Đang chạy Core testing...")
        
        try:
            result = subprocess.run(
                ["rasa", "test", "core"],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print("✅ Core testing hoàn thành!")
            else:
                print(f"⚠️ Core testing có warning hoặc chưa có stories test")
                
        except subprocess.TimeoutExpired:
            print("⚠️ Core testing timeout")
        except Exception as e:
            print(f"⚠️ Core testing bỏ qua: {e}")
        
        return True
    
    def generate_report_1_dataset_stats(self):
        self.print_header("Report 1/6: Dataset Statistics")
        
        try:
            ds = DatasetStatistics()
            ds.generate_table()
            ds.export_to_csv()
            print("✅ Report 1 hoàn thành!\n")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo Dataset Statistics: {e}\n")
            return False
    
    def generate_report_2_intent_metrics(self):
        self.print_header("Report 2/6: Intent Classification Metrics")
        
        try:
            cma = ConfusionMatrixAnalysis()
            cma.generate_metrics_table()
            print("✅ Report 2 hoàn thành!\n")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo Intent Metrics: {e}\n")
            return False
    
    def generate_report_3_confusion_matrix(self):
        self.print_header("Report 3/6: Confusion Matrix")
        
        try:
            cma = ConfusionMatrixAnalysis()
            cma.generate_confusion_matrix()
            print("✅ Report 3 hoàn thành!\n")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo Confusion Matrix: {e}\n")
            return False
    
    def generate_report_4_confidence_dist(self):
        self.print_header("Report 4/6: Confidence Distribution")
        
        try:
            cd = ConfidenceDistribution(threshold=0.7)
            cd.generate_distribution_plot()
            print("✅ Report 4 hoàn thành!\n")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo Confidence Distribution: {e}\n")
            return False
    
    def generate_report_5_fallback(self):
        self.print_header("Report 5/6: Fallback Analysis")
        
        try:
            fa = FallbackAnalysis(threshold=0.7)
            fa.generate_fallback_analysis()
            print("✅ Report 5 hoàn thành!\n")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo Fallback Analysis: {e}\n")
            return False
    
    def generate_report_6_dialogue(self):
        self.print_header("Report 6/6: End-to-End Dialogue Accuracy")
        
        try:
            da = DialogueAccuracy()
            da.generate_dialogue_report()
            print("✅ Report 6 hoàn thành!\n")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo Dialogue Accuracy: {e}\n")
            return False
    
    def generate_pdf_summary(self):
        self.print_header("Tạo PDF Summary")
        
        try:
            from PIL import Image
            from fpdf import FPDF
            
            pdf = FPDF('P', 'mm', 'A4')
            pdf.set_auto_page_break(auto=True, margin=15)
            
            report_files = [
                "evaluation/reports/1_dataset_stats.png",
                "evaluation/reports/2_intent_metrics.png",
                "evaluation/reports/3_confusion_matrix.png",
                "evaluation/reports/4_confidence_distribution.png",
                "evaluation/reports/5_fallback_analysis.png",
                "evaluation/reports/6_dialogue_accuracy.png",
            ]
            
            titles = [
                "1. Dataset Statistics",
                "2. Intent Classification Metrics",
                "3. Confusion Matrix",
                "4. Confidence Distribution",
                "5. Fallback Analysis (Rasa + Gemini)",
                "6. End-to-End Dialogue Accuracy"
            ]
            
            pdf.add_page()
            pdf.set_font('Arial', 'B', 20)
            pdf.cell(0, 20, 'RASA CHATBOT EVALUATION REPORT', 0, 1, 'C')
            
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, 'Vietnamese E-commerce Chatbot - Men Fashion', 0, 1, 'C')
            pdf.cell(0, 10, f'Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
            
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Table of Contents', 0, 1, 'L')
            pdf.set_font('Arial', '', 11)
            
            for i, title in enumerate(titles, 1):
                pdf.cell(0, 8, f'{title}', 0, 1, 'L')
            
            for i, (img_path, title) in enumerate(zip(report_files, titles)):
                if Path(img_path).exists():
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, title, 0, 1, 'L')
                    pdf.ln(5)
                    
                    img = Image.open(img_path)
                    img_w, img_h = img.size
                    aspect = img_h / img_w
                    
                    max_width = 180
                    width = max_width
                    height = width * aspect
                    
                    if height > 250:
                        height = 250
                        width = height / aspect
                    
                    pdf.image(img_path, x=15, w=width)
            
            pdf_path = "evaluation/reports/CHATBOT_EVALUATION_REPORT.pdf"
            pdf.output(pdf_path)
            
            print(f"✅ PDF Summary đã được tạo: {pdf_path}\n")
            return True
            
        except ImportError:
            print("⚠️ Không tìm thấy thư viện fpdf hoặc Pillow")
            print("ℹ️ Cài đặt: pip install fpdf pillow")
            print("ℹ️ Các báo cáo PNG vẫn có sẵn trong evaluation/reports/\n")
            return False
        except Exception as e:
            print(f"⚠️ Không thể tạo PDF: {e}")
            print("ℹ️ Các báo cáo PNG vẫn có sẵn trong evaluation/reports/\n")
            return False
    
    def run_all(self):
        print("\n" + "🚀"*40)
        print("  RASA CHATBOT EVALUATION REPORT GENERATOR")
        print("🚀"*40 + "\n")
        
        if self.run_tests:
            if not self.run_rasa_tests():
                print("\n⚠️ Rasa tests không chạy được. Sẽ tạo placeholder reports.")
                print("ℹ️ Để có báo cáo thực tế, hãy:")
                print("   1. Train model: rasa train")
                print("   2. Chạy lại script này với --run-tests\n")
        else:
            print("\nℹ️ Bỏ qua bước chạy tests. Sử dụng kết quả có sẵn hoặc tạo placeholder.")
            print("ℹ️ Để chạy tests và có báo cáo thực tế, dùng: python generate_all_reports.py --run-tests\n")
            time.sleep(2)
        
        self.generate_report_1_dataset_stats()
        self.generate_report_2_intent_metrics()
        self.generate_report_3_confusion_matrix()
        self.generate_report_4_confidence_dist()
        self.generate_report_5_fallback()
        self.generate_report_6_dialogue()
        
        self.generate_pdf_summary()
        
        self.print_header("🎉 HOÀN THÀNH!")
        print("\n📂 Tất cả báo cáo đã được tạo tại: evaluation/reports/")
        print("\n📊 Danh sách báo cáo:")
        print("   1. 1_dataset_stats.png")
        print("   2. 2_intent_metrics.png")
        print("   3. 3_confusion_matrix.png")
        print("   4. 4_confidence_distribution.png")
        print("   5. 5_fallback_analysis.png")
        print("   6. 6_dialogue_accuracy.png")
        print("   7. CHATBOT_EVALUATION_REPORT.pdf (nếu có fpdf)")
        print("\n💡 Sử dụng các báo cáo này cho KLTN của bạn!")
        print("="*80 + "\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Rasa Chatbot Evaluation Reports')
    parser.add_argument('--run-tests', action='store_true', 
                       help='Chạy rasa test trước khi tạo báo cáo (mất 10-20 phút)')
    
    args = parser.parse_args()
    
    generator = ReportGenerator(run_tests=args.run_tests)
    generator.run_all()
