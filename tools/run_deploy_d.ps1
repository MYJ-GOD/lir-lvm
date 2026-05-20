Param(
  [string]$SerialPort = "COM5",
  [int]$ThroughputRepeat = 1000,
  [int]$E3Repeat = 30
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$outDir = Join-Path $repoRoot "论文分区\ccfc\result\E10_deploy"
$throughputSummary = Join-Path $outDir "throughput_summary.csv"
$e3Summary = Join-Path $outDir "e3_mem_summary.csv"
$e4Trials = Join-Path $repoRoot "论文分区\ccfc\result\E4\e4_trials.csv"
$powerManual = Join-Path $outDir "power_manual.csv"
$finalCsv = Join-Path $outDir "deploy_metrics_final.csv"
$finalMd = Join-Path $outDir "deploy_metrics_final.md"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host ""
Write-Host "Step1: 请烧录吞吐固件"
Write-Host "  论文分区/ccfc/固件烧录/mvm_esp8266_e2_a0_base_guarded.ino"
Read-Host "烧录完成后输入任意内容继续"

Set-Location $repoRoot
python "论文分区/ccfc/tools/bench_deploy_throughput.py" `
  --serial $SerialPort `
  --repeat $ThroughputRepeat `
  --variant guarded `
  --out-dir $outDir `
  --write-latest

Write-Host ""
Write-Host "Step2: 请烧录E3遥测固件"
Write-Host "  论文分区/ccfc/固件烧录/mvm_esp8266_e10_e3_telemetry.ino"
Read-Host "烧录完成后输入任意内容继续"

python "论文分区/ccfc/tools/bench_deploy_e3_mem.py" `
  --serial $SerialPort `
  --repeat $E3Repeat `
  --variant e3_telemetry `
  --out-dir $outDir `
  --write-latest

python "论文分区/ccfc/tools/summarize_deploy_d.py" `
  --throughput-summary $throughputSummary `
  --e3-summary $e3Summary `
  --e4-trials $e4Trials `
  --power-manual $powerManual `
  --out-csv $finalCsv `
  --out-md $finalMd

Write-Host ""
Write-Host "部署指标输出："
Write-Host " - $throughputSummary"
Write-Host " - $e3Summary"
Write-Host " - $finalCsv"
Write-Host " - $finalMd"
Write-Host "功耗如未填写，请编辑：$powerManual 后再重跑 summarize_deploy_d.py"
