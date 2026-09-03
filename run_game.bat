@echo off
echo ==========================================
echo   Vampire Survivors - Python Edition
echo ==========================================
echo.
echo Checking Python...
python --version 2>NUL
if errorlevel 1 (
    echo Python not found! Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo.
echo Checking Pygame...
python -c "import pygame" 2>NUL
if errorlevel 1 (
    echo Pygame not found! Installing...
    pip install pygame
)
echo.
echo Starting game...
cd /d "%~dp0vampire_survivors"
python main.py
pause
