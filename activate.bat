@echo off
echo Market Sentiment Analysis Tool - Quick Environment Activation
echo ============================================================
echo.

if exist "market_sentiment\Scripts\activate.bat" (
    echo Activating market_sentiment environment...
    call market_sentiment\Scripts\activate.bat
    echo Environment activated successfully!
    echo.
    echo Ready for development! 
    echo - Backend: cd backend ^&^& python -m uvicorn main:app --reload
    echo - Frontend: cd frontend ^&^& npm run dev
) else (
    echo Environment not found. Please run: uv venv market_sentiment
)

echo. 