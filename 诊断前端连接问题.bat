@echo off
chcp 936 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0诊断前端连接问题.ps1"
