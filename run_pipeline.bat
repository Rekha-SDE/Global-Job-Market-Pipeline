@echo off
REM Runs the whole pipeline. Used by the Windows Task Scheduler (see README).
REM %~dp0 = the folder of this file, so it works wherever the project is.
cd /d "%~dp0"
call venv\Scripts\activate.bat
python src\run_pipeline.py