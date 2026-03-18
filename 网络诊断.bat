@echo off
chcp 936 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0网络诊断.ps1"
