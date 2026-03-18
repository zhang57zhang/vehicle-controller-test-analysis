@echo off
chcp 936 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0测试前端连接.ps1"
