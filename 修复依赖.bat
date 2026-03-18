@echo off
chcp 936 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0修复依赖.ps1"
