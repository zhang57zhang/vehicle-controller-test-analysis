@echo off
chcp 936 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0启动前端服务.ps1"
