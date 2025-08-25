@echo off

set PYTHONPATH=%PYTHONPATH%;C:\Users\User\Desktop\Freelance\OwnYourAI\SiteAI-Backend\app

:loop
    uvicorn "app.main:app" --host 127.0.0.1 --port 8214 --log-level debug
    if not %errorlevel% == 0 (
        echo Server crashed with exit code %errorlevel%. Respawning...
        timeout /t 1 >nul
        goto loop
    )
