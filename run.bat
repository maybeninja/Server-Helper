@echo off
title Bot Updater

git pull

echo.
echo =========================
echo   Launching Bot...
echo =========================

:: Start bot in new window and close this one
start "" python main.py

exit