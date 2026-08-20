@echo off
title Garga - Sistema de Analise
cd /d "%~dp0"

echo Subindo a API do Supervisor...
start cmd /k "C:\Users\celso\AppData\Local\Python\pythoncore-3.14-64\python.exe -m uvicorn api_supervisor:app --reload"

timeout /t 3 >nul

echo Iniciando o Painel Garga...
C:\Users\celso\AppData\Local\Python\pythoncore-3.14-64\python.exe -m streamlit run garga.py
pause