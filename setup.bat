@echo off
setlocal enabledelayedexpansion

set "PYTHON_CMD="
set "PIP_CMD="

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
)

if "%PYTHON_CMD%"=="" (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

where pip >nul 2>&1
if not errorlevel 1 (
    set "PIP_CMD=pip"
)

echo ========================================
echo   affect-wave Setup Script
echo ========================================
echo.

:: Check Python
if "%PYTHON_CMD%"=="" (
    echo ERROR: Python is required but not found.
    echo Please install Python 3.10 or later.
    exit /b 1
)

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python launcher is present but could not start Python.
    exit /b 1
)

if "%PIP_CMD%"=="" (
    set "PIP_CMD=%PYTHON_CMD% -m pip"
)

:: Create directories
echo Creating directories...
if not exist logs mkdir logs
if not exist models mkdir models
if not exist data\prototypes mkdir data\prototypes

:: Check .env file
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo.
    echo IMPORTANT: Edit .env and configure:
    echo   - EMBEDDING_MODEL
    echo   - API_PORT (default: 8081)
    echo.
) else (
    echo .env already exists.
)

:: Install dependencies
echo.
echo Installing Python dependencies...
%PIP_CMD% install -e . --quiet

if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

:: Install llama-cpp-python for model download
echo.
echo Checking llama-cpp-python...
%PIP_CMD% show llama-cpp-python >nul 2>&1
if errorlevel 1 (
    echo Installing llama-cpp-python...
    %PIP_CMD% install llama-cpp-python --quiet
)

:: Download embedding model
echo.
echo ========================================
echo   Embedding Model Setup
echo ========================================
echo.

set MODEL_PATH=models\Qwen3-Embedding-0.6B-Q8_0.gguf

if exist %MODEL_PATH% (
    echo Model already exists: %MODEL_PATH%
) else (
    echo Downloading Qwen3-Embedding-0.6B-Q8_0...
    echo.

    %PYTHON_CMD% -c "from llama_cpp import Llama; Llama.from_pretrained(repo_id='Qwen/Qwen3-Embedding-0.6B-GGUF', filename='Qwen3-Embedding-0.6B-Q8_0.gguf', cache_dir='models', verbose=False)"
    if errorlevel 1 (
        echo.
        echo WARNING: Model download failed.
        echo You can download manually from:
        echo https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF
    ) else (
        echo.
        echo Model downloaded successfully!
    )
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Start llama.cpp embeddings server:
echo.
echo    llama-server -m models\Qwen3-Embedding-0.6B-Q8_0.gguf --embeddings --pooling mean -c 8192 --port 8080
echo.
echo 2. Start affect-wave API server:
echo.
echo    affect-wave serve --port 8081
echo.
echo 3. Test API:
echo.
echo    curl -X POST http://127.0.0.1:8081/analyze -H "Content-Type: application/json" -d "{\"user_message\":\"hello\",\"agent_message\":\"hi there\"}"
echo.
echo Documentation: README.md, docs/specification.md
echo.

endlocal
