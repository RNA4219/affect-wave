@echo off
setlocal

echo affect-wave setup placeholder
echo.
echo This repository is currently in pre-implementation documentation setup.
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Fill OPENAI_API_KEY, OPENAI_MODEL, LLAMA_CPP_BASE_URL, EMBEDDING_MODEL
echo 3. Set DISCORD_BOT_TOKEN
echo 4. Optionally set DISCORD_WEBHOOK_URL when using webhook transport
echo 5. Start llama.cpp embeddings server manually
echo.
echo See README.md and requirements.md for the current canonical guidance.

if not exist logs mkdir logs
if not exist docs mkdir docs

endlocal
