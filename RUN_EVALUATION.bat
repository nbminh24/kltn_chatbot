@echo off
echo ========================================
echo   RASA CHATBOT EVALUATION REPORTS
echo ========================================
echo.

echo [1/3] Kich hoat virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/3] Cai dat dependencies...
pip install -q -r evaluation\requirements.txt

echo.
echo [3/3] Tao bao cao...
echo.
echo CHON MOT TUY CHON:
echo.
echo [1] Chi tao bao cao (khong chay test) - NHANH (1 phut)
echo [2] Chay test + tao bao cao - DAY DU (15-20 phut)
echo.

set /p choice="Nhap lua chon (1 hoac 2): "

if "%choice%"=="1" (
    echo.
    echo Dang tao bao cao...
    python evaluation\generate_all_reports.py
) else if "%choice%"=="2" (
    echo.
    echo Dang chay Rasa tests va tao bao cao...
    echo Qua trinh nay mat 15-20 phut, vui long cho...
    python evaluation\generate_all_reports.py --run-tests
) else (
    echo Lua chon khong hop le!
    pause
    exit /b
)

echo.
echo ========================================
echo   HOAN THANH!
echo ========================================
echo.
echo Bao cao da duoc tao tai: evaluation\reports\
echo.
pause
