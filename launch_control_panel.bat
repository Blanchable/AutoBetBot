@echo off
setlocal

if not exist .venv (
  echo [AutoBetBot] Creating virtual environment...
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install -r requirements.txt

echo [AutoBetBot] Launching control panel...
python -m ui.control_panel
