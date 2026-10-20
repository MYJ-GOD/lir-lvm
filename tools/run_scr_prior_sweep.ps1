param(
  [Parameter(Mandatory=$true)][string]$SerialPort,
  [Parameter(Mandatory=$true)][ValidateSet("guarded","noguard")][string]$Variant,
  [int]$N = 200,
  [double]$Timeout = 1.0,
  [int]$Seed = 20260218,
  [string]$OutDir = "result/E5_prior"
)

$priors = @(0.1,0.3,0.5,0.7,0.9)

foreach ($p in $priors) {
  Write-Host "== Running variant=$Variant fault-prior=$p n=$N ==" -ForegroundColor Cyan
  python $benchScript `
    --serial $SerialPort `
    --variant $Variant `
    --fault-prior $p `
    --n $N `
    --timeout $Timeout `
    --seed $Seed `
    --out-dir $OutDir `
    --write-latest
}

Write-Host "Sweep done for variant=$Variant" -ForegroundColor Green
