
$root = "c:\Users\sherr\.gemini\antigravity\Atomadic\projects\atomadic"
$checks = @(
    "atomadic.toml",
    "bootstrap.py",
    "docs\SUPREME_BLUEPRINT.md",
    "config\atomadic_soul.json",
    "src\atomadic\core",
    "src\atomadic\ethics"
)

$failed = 0
foreach ($check in $checks) {
    if (Test-Path (Join-Path $root $check)) {
        Write-Host "[OK] $check found." -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $check NOT found." -ForegroundColor Red
        $failed++
    }
}

if ($failed -eq 0) {
    Write-Host "Build Verification PASSED." -ForegroundColor Cyan
} else {
    Write-Host "Build Verification FAILED ($failed errors)." -ForegroundColor Red
    exit 1
}
