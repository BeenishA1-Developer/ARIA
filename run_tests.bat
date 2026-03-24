@echo off
echo Running ARIA Phase 1 + Phase 2 Tests...
call aria_env\Scripts\activate
echo.
echo === Phase 1 Tests ===
pytest tests/test_phase1.py -v --tb=short
echo.
echo === Phase 2 Tests ===
pytest tests/test_phase2.py -v --tb=short
pause
