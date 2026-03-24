@echo off
echo ============================================
echo ARIA - Setup Script (Windows)
echo ============================================
echo.

echo [1/4] Python check kar rahe hain...
python --version
if errorlevel 1 (
    echo ERROR: Python install nahi hai!
    echo python.org se download karo
    pause
    exit /b 1
)

echo.
echo [2/4] Virtual environment bana rahe hain...
python -m venv aria_env
call aria_env\Scripts\activate

echo.
echo [3/4] Dependencies install kar rahe hain...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/4] .env file setup kar rahe hain...
if not exist .env (
    copy .env.example .env
    echo .env file bana di! Isme Gemini API key daalo.
) else (
    echo .env already exist karti hai.
)

echo.
echo ============================================
echo SETUP COMPLETE!
echo ============================================
echo.
echo Agle steps:
echo 1. .env file mein GEMINI_API_KEY daalo
echo 2. aria_env\Scripts\activate chalao
echo 3. python main.py chalao
echo.
pause
