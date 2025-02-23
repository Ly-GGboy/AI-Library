# 激活Python虚拟环境
.\py310\Scripts\Activate.ps1

# 设置环境变量
$env:PYTHONPATH = "D:\work\AI-Library-main\server"

Write-Host "Starting backend service..."
# 启动后端服务
Start-Process -FilePath "python" -ArgumentList "server\run.py" -NoNewWindow

Write-Host "Starting frontend service..."
# 启动前端服务
Push-Location -Path "client"
Start-Process -FilePath "npm" -ArgumentList "run preview" -NoNewWindow
Pop-Location

Write-Host "Starting Cloudflare tunnel..."
# 启动Cloudflare隧道
Start-Service -Name Cloudflared

Write-Host "All services started!"
Write-Host "Frontend: https://localhost:4173"
Write-Host "Backend: https://localhost:8000" 