# VocalMind overnight benchmark - sequential stages with checkpoint resume + retry
param(
    [string]$ReportDir = ""
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

if (-not $env:OLLAMA_API_KEY) {
    $EnvFile = Join-Path $Root "backend/.env"
    if (Test-Path $EnvFile) {
        Get-Content $EnvFile | ForEach-Object {
            if ($_ -match '^\s*OLLAMA_API_KEY=(.+)$') {
                $env:OLLAMA_API_KEY = $Matches[1].Trim('"')
            }
        }
    }
}
if (-not $env:OLLAMA_API_KEY) {
    Write-Error "OLLAMA_API_KEY not set and not found in backend/.env"
    exit 1
}
$KeyPreview = if ($env:OLLAMA_API_KEY.Length -gt 8) { $env:OLLAMA_API_KEY.Substring(0, 8) + "..." } else { "(short)" }

if (-not $ReportDir) {
    $ReportDir = Join-Path $Root "infra/benchmarks/reports/overnight_$(Get-Date -Format 'yyyyMMdd')"
}
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$LauncherLog = Join-Path $ReportDir "launcher.log"
"Started $(Get-Date -Format o) PID=$PID Root=$Root KeyPreview=$KeyPreview" | Out-File $LauncherLog -Encoding utf8

$PlanPath = Join-Path $ReportDir "repeat_plan.json"
python infra/scripts/estimate_benchmark_time.py --json-out $PlanPath 2>&1 | Tee-Object -FilePath (Join-Path $ReportDir "estimate.log")
$Plan = Get-Content $PlanPath -Raw | ConvertFrom-Json

$Stages = @(
    "emotion_shift",
    "process_adherence",
    "nli_policy",
    "rag_judge",
    "text_to_sql",
    "fast_classification"
)

$ModelsFlag = "kimi-k2.6:cloud,kimi-k2.5:cloud,ministral-3:14b,ministral-3:8b,qwen3.5:cloud"

foreach ($Stage in $Stages) {
    $Repeats = $Plan.repeats.$Stage
    if (-not $Repeats) { $Repeats = 1 }
    $OutJson = Join-Path $ReportDir "$Stage.json"
    $LogFile = Join-Path $ReportDir "$Stage.log"
    $Attempt = 0
    $MaxAttempts = 3
    $ExitCode = 1

    while ($Attempt -lt $MaxAttempts -and $ExitCode -ne 0) {
        $Attempt++
        "=== Stage $Stage attempt $Attempt repeats=$Repeats $(Get-Date -Format o) ===" | Tee-Object -FilePath $LogFile -Append
        python infra/scripts/benchmark_ollama_cloud.py `
            --ground-truth infra/benchmarks/ollama_cloud_ground_truth_v2.json `
            --use-model-triage `
            --models $ModelsFlag `
            --stages $Stage `
            --repeats $Repeats `
            --ollama-cloud-key $env:OLLAMA_API_KEY `
            --judge-model gemma3:12b `
            --judge-base-url https://ollama.com/v1 `
            --judge-api-key $env:OLLAMA_API_KEY `
            --output $OutJson 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($null -ne $LASTEXITCODE) { $ExitCode = $LASTEXITCODE } else { $ExitCode = 0 }
        if ($ExitCode -ne 0) {
            "Attempt $Attempt failed exit=$ExitCode - retrying (checkpoint resume)" | Tee-Object -FilePath $LogFile -Append
        }
    }
}

python infra/scripts/aggregate_overnight_results.py --report-dir $ReportDir 2>&1 | Tee-Object -FilePath (Join-Path $ReportDir "aggregate.log")
"Overnight run finished $(Get-Date -Format o)" | Out-File -FilePath (Join-Path $ReportDir "DONE.txt") -Encoding utf8
