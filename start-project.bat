@echo off
echo Starting Fraud Detection System...
echo.

:: 1️⃣ Python Backend
start "Backend" cmd /k "cd /d C:\Users\chyas\Downloads\FraudTransaction && call env\Scripts\activate && py main.py"

:: 2️⃣ Zookeeper (Run from Kafka root)
start "Zookeeper" cmd /k "cd /d C:\kafka && bin\windows\zookeeper-server-start.bat config\zookeeper.properties"

:: Wait for Zookeeper
timeout /t 10 >nul

:: 3️⃣ Kafka Server
start "Kafka" cmd /k "cd /d C:\kafka && bin\windows\kafka-server-start.bat config\server.properties"

echo.
echo All services are launching...