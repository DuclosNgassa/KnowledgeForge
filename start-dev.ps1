$api = Start-Process powershell -PassThru -ArgumentList `
    "-NoExit", "-Command", "uv run uvicorn app.main:app --reload"

$worker = Start-Process powershell -PassThru -ArgumentList `
    "-NoExit", "-Command", "uv run taskiq worker app.worker:broker"

Write-Host "FastAPI and Taskiq worker started."
Write-Host "API PID: $( $api.Id )"
Write-Host "Worker PID: $( $worker.Id )"