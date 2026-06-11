param(
    [Parameter(Mandatory = $true)]
    [string]$ImageRepo,

    [string]$Tag = "latest",

    [switch]$AlsoLatest
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "fastApiProject"

if (-not (Test-Path $backendDir)) {
    throw "未找到后端目录: $backendDir"
}

$primaryImage = "${ImageRepo}:${Tag}"

Write-Host "==> 构建镜像: $primaryImage" -ForegroundColor Cyan
docker build -t $primaryImage $backendDir
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "==> 推送镜像: $primaryImage" -ForegroundColor Cyan
docker push $primaryImage
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($AlsoLatest -and $Tag -ne "latest") {
    $latestImage = "${ImageRepo}:latest"

    Write-Host "==> 额外打标: $latestImage" -ForegroundColor Cyan
    docker tag $primaryImage $latestImage
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host "==> 推送镜像: $latestImage" -ForegroundColor Cyan
    docker push $latestImage
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "==> 完成" -ForegroundColor Green
