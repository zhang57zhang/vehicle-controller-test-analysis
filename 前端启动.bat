@echo off
chcp 936 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0前端启动.ps1"
