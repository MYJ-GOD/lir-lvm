Param(
  [string]$SerialPort = "COM5",
  [int]$Repeat = 100,
  [double]$DisturbProb = 0.30,
  [int]$Seed = 20260218,
  [int]$SettleMs = 10,
  [int]$MaxRetry = 3,
  [switch]$OpenLoopOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$outDir = Join-Path $repoRoot "论文分区\ccfc\result\E4_json_real"
$benchScript = Join-Path $repoRoot "论文分区\ccfc\tools\bench_e4_json_real.py"
$summarizeScript = Join-Path $repoRoot "论文分区\ccfc\tools\summarize_e4_json_real.py"
$e4Summary = Join-Path $repoRoot "论文分区\ccfc\result\E4\e4_summary.csv"
$openSummary = Join-Path $outDir "e4_json_real_summary_open_loop.csv"
$closedNoRetrySummary = Join-Path $outDir "e4_json_real_summary_closed_loop_no_retry.csv"
$closedRetrySummary = Join-Path $outDir "e4_json_real_summary_closed_loop_retry.csv"
$finalCsv = Join-Path $outDir "e4_json_real_matrix_final.csv"
$finalMd = Join-Path $outDir "e4_json_real_matrix_final.md"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host ""
Write-Host "请先烧录固件: 论文分区/ccfc/固件烧录/mvm_esp8266_e4_json_real.ino"
Read-Host "烧录完成后输入任意内容继续"

Set-Location $repoRoot

& python $benchScript `
  --serial $SerialPort `
  --repeat $Repeat `
  --disturb-prob $DisturbProb `
  --seed $Seed `
  --settle-ms $SettleMs `
  --mode open_loop `
  --variant open_loop `
  --out-dir $outDir `
  --write-latest

if (-not $OpenLoopOnly) {
  & python $benchScript `
    --serial $SerialPort `
    --repeat $Repeat `
    --disturb-prob $DisturbProb `
    --seed $Seed `
    --settle-ms $SettleMs `
    --mode closed_loop_no_retry `
    --variant closed_loop_no_retry `
    --out-dir $outDir

  & python $benchScript `
    --serial $SerialPort `
    --repeat $Repeat `
    --disturb-prob $DisturbProb `
    --seed $Seed `
    --settle-ms $SettleMs `
    --mode closed_loop_retry `
    --max-retry $MaxRetry `
    --variant closed_loop_retry `
    --out-dir $outDir
}

$summaryArgs = @(
  $summarizeScript,
  "--json-summary", $openSummary
)
if (-not $OpenLoopOnly) {
  $summaryArgs += @("--json-summary", $closedNoRetrySummary, "--json-summary", $closedRetrySummary)
}
$summaryArgs += @(
  "--e4-summary", $e4Summary,
  "--out-csv", $finalCsv,
  "--out-md", $finalMd
)

& python @summaryArgs

Write-Host ""
Write-Host "E4+ 完成，输出："
Write-Host (" - " + $openSummary)
if (-not $OpenLoopOnly) {
  Write-Host (" - " + $closedNoRetrySummary)
  Write-Host (" - " + $closedRetrySummary)
}
Write-Host (" - " + $finalCsv)
Write-Host (" - " + $finalMd)
