param(
  [Parameter(Mandatory=$true)][string]$SerialPort,
  [int]$Repeat = 30,
  [double]$Timeout = 1.0,
  [double]$TimeoutStep = 5.0,
  [string]$OutDir = "论文分区/ccfc/result/E2_orthogonal"
)

$variants = @(
  @{ Variant = "a0_base_guarded"; Firmware = "论文分区/ccfc/固件烧录/mvm_esp8266_e2_a0_base_guarded.ino" },
  @{ Variant = "a1_no_auth_only"; Firmware = "论文分区/ccfc/固件烧录/mvm_esp8266_e2_a1_no_auth_only.ino" },
  @{ Variant = "a2_no_load_validator_only"; Firmware = "论文分区/ccfc/固件烧录/mvm_esp8266_e2_a2_no_load_validator_only.ino" },
  @{ Variant = "a3_no_step_limit_only"; Firmware = "论文分区/ccfc/固件烧录/mvm_esp8266_e2_a3_no_step_limit_only.ino" },
  @{ Variant = "a4_no_call_depth_only"; Firmware = "论文分区/ccfc/固件烧录/mvm_esp8266_e2_a4_no_call_depth_only.ino" },
  @{ Variant = "a5_no_bad_encoding_fault_only"; Firmware = "论文分区/ccfc/固件烧录/mvm_esp8266_e2_a5_no_bad_encoding_fault_only.ino" }
)

foreach ($item in $variants) {
  $v = $item.Variant
  $fw = $item.Firmware
  Write-Host "== Variant $v ==" -ForegroundColor Cyan
  Write-Host "Please flash firmware: $fw" -ForegroundColor Yellow
  Read-Host "Press Enter after flashing to continue"
  python "论文分区/ccfc/tools/bench_e2_orthogonal.py" `
    --serial $SerialPort `
    --fw-proto `
    --all-cases `
    --repeat $Repeat `
    --timeout $Timeout `
    --timeout-step $TimeoutStep `
    --variant $v `
    --out-dir $OutDir `
    --write-latest
}

Write-Host "All orthogonal E2 variants completed." -ForegroundColor Green

