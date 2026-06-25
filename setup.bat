@echo off
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -e .
echo.
echo ✅ CLI CivilEng installed. Activate with: venv\Scripts\activate.bat
echo    Then run: cli-civileng --help
