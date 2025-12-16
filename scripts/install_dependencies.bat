@echo off
echo ========================================
echo Installing dependencies for the project
echo ========================================
echo.

echo [1/5] Installing core packages...
pip install pandas numpy

echo.
echo [2/5] Installing NLP packages...
pip install sentence-transformers transformers

echo.
echo [3/5] Installing clustering packages...
pip install hdbscan scikit-learn

echo.
echo [4/5] Installing visualization packages...
pip install matplotlib seaborn

echo.
echo [5/5] Installing utility packages...
pip install tqdm requests beautifulsoup4

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Optional packages (for LLM features):
echo   pip install openai anthropic pytrends
echo.
pause
