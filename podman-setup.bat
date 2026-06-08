@echo off
REM ISO 20022 Mapper - Podman Setup Script for Windows
REM This script sets up and runs the ISO 20022 GenAI Migration Platform using Podman

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Colors (using ANSI codes)
set "RESET=[0m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "RED=[31m"

:main
cls
echo %BLUE%========================================%RESET%
echo %BLUE%ISO 20022 Mapper - Podman Setup%RESET%
echo %BLUE%========================================%RESET%
echo.

set "action=%1"
if "%action%"=="" set "action=setup"

REM Check Podman
echo %BLUE%Checking Podman Installation...%RESET%
where podman >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: Podman is not installed%RESET%
    echo Please install Podman from https://podman.io/docs/installation
    exit /b 1
)

where podman-compose >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: podman-compose is not installed%RESET%
    echo Please install it with: pip install podman-compose
    exit /b 1
)

echo %GREEN%Podman is installed%RESET%
echo.

if "%action%"=="setup" goto setup_full
if "%action%"=="start" goto start_services
if "%action%"=="stop" goto stop_services
if "%action%"=="rebuild" goto rebuild
if "%action%"=="logs" goto show_logs
if "%action%"=="help" goto show_help
goto show_help

:setup_full
echo %BLUE%========================================%RESET%
echo %BLUE%Setting Up Environment%RESET%
echo %BLUE%========================================%RESET%

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo %GREEN%Created .env from .env.example%RESET%
        echo %YELLOW%Please update .env with your configuration%RESET%
    ) else (
        echo %RED%Error: .env.example not found%RESET%
        exit /b 1
    )
) else (
    echo %GREEN%.env file already exists%RESET%
)
echo.

echo %BLUE%========================================%RESET%
echo %BLUE%Building Container Images%RESET%
echo %BLUE%========================================%RESET%
echo %YELLOW%This may take a few minutes...%RESET%
echo.

podman-compose -f docker-compose.yml build
if errorlevel 1 (
    echo %RED%Failed to build images%RESET%
    exit /b 1
)
echo %GREEN%Container images built successfully%RESET%
echo.

echo %BLUE%========================================%RESET%
echo %BLUE%Starting Services%RESET%
echo %BLUE%========================================%RESET%

podman-compose -f docker-compose.yml up -d
if errorlevel 1 (
    echo %RED%Failed to start services%RESET%
    exit /b 1
)
echo %GREEN%Services started%RESET%
echo.

echo %YELLOW%Waiting for services to be ready...%RESET%
timeout /t 10 /nobreak

goto show_endpoints

:start_services
echo %BLUE%========================================%RESET%
echo %BLUE%Starting Services%RESET%
echo %BLUE%========================================%RESET%

podman-compose -f docker-compose.yml up -d
if errorlevel 1 (
    echo %RED%Failed to start services%RESET%
    exit /b 1
)
echo %GREEN%Services started%RESET%
echo.
goto show_endpoints

:stop_services
echo %BLUE%========================================%RESET%
echo %BLUE%Stopping Services%RESET%
echo %BLUE%========================================%RESET%

podman-compose -f docker-compose.yml down
echo %GREEN%Services stopped%RESET%
echo.
exit /b 0

:rebuild
echo %BLUE%========================================%RESET%
echo %BLUE%Rebuilding Container Images%RESET%
echo %BLUE%========================================%RESET%

podman-compose -f docker-compose.yml down -v
podman-compose -f docker-compose.yml build
podman-compose -f docker-compose.yml up -d

echo %YELLOW%Waiting for services to be ready...%RESET%
timeout /t 10 /nobreak
echo.
goto show_endpoints

:show_logs
podman-compose -f docker-compose.yml logs -f
exit /b 0

:show_endpoints
echo %BLUE%========================================%RESET%
echo %BLUE%Service Endpoints%RESET%
echo %BLUE%========================================%RESET%
echo.
echo %GREEN%Backend API:%RESET%
echo   Main:      http://localhost:8000
echo   Health:    http://localhost:8000/health
echo   Docs:      http://localhost:8000/docs
echo   ReDoc:     http://localhost:8000/redoc
echo.
echo %GREEN%Frontend:%RESET%
echo   UI:        http://localhost:5173
echo.
echo %GREEN%Services:%RESET%
echo   Database:  localhost:5432 (postgres:postgres)
echo   Redis:     localhost:6379
echo   Phoenix:   http://localhost:6006
echo.
echo %GREEN%Quick Commands:%RESET%
echo   View logs:        podman-compose logs -f
echo   Stop services:    podman-compose down
echo   Backend shell:    podman-compose exec backend cmd
echo   Database shell:   podman-compose exec postgres psql -U postgres -d iso_mapper
echo.

exit /b 0

:show_help
echo %BLUE%Usage: podman-setup.bat [action]%RESET%
echo.
echo %GREEN%Actions:%RESET%
echo   setup        - Initial setup, build images, and start services (default)
echo   start        - Start existing services
echo   stop         - Stop running services
echo   rebuild      - Rebuild images from scratch
echo   logs         - View live logs from all services
echo   help         - Show this help message
echo.
exit /b 0
