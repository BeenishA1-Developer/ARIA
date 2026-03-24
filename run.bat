@echo off
echo Starting ARIA...
call aria_env\Scripts\activate
python main.py %*
