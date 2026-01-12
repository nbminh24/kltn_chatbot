#!/usr/bin/env python3
"""
Script chạy từ ROOT folder để tạo báo cáo evaluation.
Sử dụng: python generate_reports.py [--run-tests]
"""
import os
import sys
from pathlib import Path

def main():
    current_dir = Path.cwd()
    print(f"📂 Current directory: {current_dir}")
    
    # Kiểm tra có đang ở root folder không
    if not (current_dir / "data").exists():
        print("\n❌ CHẠY SAI FOLDER!")
        print("📍 Bạn phải chạy script này từ ROOT folder của project")
        print("\nChạy lệnh này:")
        print("   cd c:\\Users\\USER\\Downloads\\kltn_chatbot")
        print("   python generate_reports.py --run-tests")
        sys.exit(1)
    
    print("✅ Đúng folder rồi!")
    
    # Import và chạy
    sys.path.insert(0, str(current_dir / "evaluation"))
    
    from evaluation.generate_all_reports import ReportGenerator
    
    run_tests = "--run-tests" in sys.argv
    
    print(f"\n🚀 Bắt đầu tạo báo cáo...")
    if run_tests:
        print("⏱️ Sẽ chạy Rasa tests trước (15-20 phút)")
    else:
        print("ℹ️ Sử dụng kết quả test có sẵn (hoặc placeholder)")
        print("💡 Để có báo cáo đầy đủ, chạy: python generate_reports.py --run-tests")
    
    generator = ReportGenerator(run_tests=run_tests)
    generator.run_all()

if __name__ == "__main__":
    main()
