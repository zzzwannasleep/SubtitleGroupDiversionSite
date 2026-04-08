Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $repoRoot 'frontend'

if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
  throw "未找到 frontend/package.json，请确认当前脚本位于仓库根目录。"
}

Push-Location $frontendDir

try {
  if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host '未检测到 node_modules，正在安装前端依赖...' -ForegroundColor Cyan
    npm install

    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
  }

  Write-Host '正在构建并启动前端预览服务...' -ForegroundColor Green
  Write-Host '浏览器会自动打开 http://127.0.0.1:4173/' -ForegroundColor DarkGray

  npm run preview:local

  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}

