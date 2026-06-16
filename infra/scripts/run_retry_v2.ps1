# VocalMind benchmark retry v2 - rate-limited, error-row only where applicable
# DO NOT launch until Ollama Cloud quota has reset (see FULL_REPORT / probe result).
param(
    [string]$ReportDir = "infra/benchmarks/reports/overnight_20260614",
    [double]$MaxRequestsPerMinute = 20,
    [switch]$SerialModels
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

$ReportDir = Join-Path $Root $ReportDir
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$LauncherLog = Join-Path $ReportDir "retry_v2_launcher.log"
"Retry v2 started $(Get-Date -Format o) PID=$PID rpm=$MaxRequestsPerMinute" | Out-File $LauncherLog -Encoding utf8

$CommonArgs = @(
    "--ground-truth", "infra/benchmarks/ollama_cloud_ground_truth_v2.json",
    "--use-model-triage",
    "--ollama-cloud-key", $env:OLLAMA_API_KEY,
    "--judge-model", "gemma3:12b",
    "--judge-base-url", "https://ollama.com/v1",
    "--judge-api-key", $env:OLLAMA_API_KEY,
    "--max-requests-per-minute", "$MaxRequestsPerMinute",
    "--max-retries", "5"
)
if ($SerialModels) {
    $CommonArgs += "--serial-models"
}

function Invoke-Stage {
    param(
        [string]$Stage,
        [int]$Repeats = 1,
        [string]$RetryFrom = "",
        [string]$Models = ""
    )
    $OutJson = Join-Path $ReportDir "$Stage.json"
    $LogFile = Join-Path $ReportDir "${Stage}_retry_v2.log"
    $Args = $CommonArgs + @("--stages", $Stage, "--repeats", "$Repeats", "--output", $OutJson)
    if ($RetryFrom) {
        $Args += @("--retry-errors-from", $RetryFrom)
    }
    if ($Models) {
        $Args += @("--models", $Models)
    }
    "=== Retry v2 $Stage repeats=$Repeats $(Get-Date -Format o) ===" | Tee-Object -FilePath $LogFile -Append
    python infra/scripts/benchmark_ollama_cloud.py @Args 2>&1 | Tee-Object -FilePath $LogFile -Append
    return $LASTEXITCODE
}

# 1) emotion_shift: resume checkpoint (456 remaining of 510)
$EsExit = Invoke-Stage -Stage "emotion_shift" -Repeats 1
if ($EsExit -ne 0) { "emotion_shift failed exit=$EsExit" | Tee-Object -FilePath $LauncherLog -Append }

# 2) process_adherence: retry 2 error rows only, preserve 763 good rows
$PaJson = Join-Path $ReportDir "process_adherence.json"
if (Test-Path $PaJson) {
    Invoke-Stage -Stage "process_adherence" -Repeats 1 -RetryFrom $PaJson | Out-Null
}

# 3) stages with 429 errors - retry error rows only
foreach ($Stage in @("nli_policy", "rag_judge", "text_to_sql", "fast_classification")) {
    $StageJson = Join-Path $ReportDir "$Stage.json"
    if (-not (Test-Path $StageJson)) {
        "Skip $Stage - no prior JSON" | Tee-Object -FilePath $LauncherLog -Append
        continue
    }
    $Repeats = 1
    if ($Stage -eq "nli_policy") { $Repeats = 2 }
    Invoke-Stage -Stage $Stage -Repeats $Repeats -RetryFrom $StageJson | Out-Null
}

python infra/scripts/aggregate_overnight_results.py --report-dir $ReportDir 2>&1 | Tee-Object -FilePath (Join-Path $ReportDir "aggregate_retry_v2.log")
"Retry v2 finished $(Get-Date -Format o)" | Out-File -FilePath (Join-Path $ReportDir "RETRY_V2_DONE.txt") -Encoding utf8
