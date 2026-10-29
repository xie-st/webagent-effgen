param(
    [ValidateSet('site','smoke','browsergym','runner-smoke')]
    [string]$Mode = 'site',
    [ValidateSet('normal','slow','rate','login')]
    [string]$Scenario = 'normal'
)
$ErrorActionPreference = 'Stop'
function Find-EnvironmentPython([string]$EnvironmentName) {
    $candidates = @(
        (Join-Path $PSScriptRoot "$EnvironmentName\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if ((Test-Path -LiteralPath $candidate -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path (Split-Path (Split-Path $candidate)) "pyvenv.cfg") -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw "Python environment not found: $EnvironmentName. Rebuild it using README.md."
}
Push-Location -LiteralPath $PSScriptRoot
try {
    $env:PYTHONUTF8 = '1'
    $python = Find-EnvironmentPython $(if ($Mode -eq 'browsergym') { '.venv-browsergym' } else { '.venv' })
    switch ($Mode) {
        'site' { & $python sandbox.py --scenario $Scenario }
        'smoke' { & $python smoke_test.py }
        'runner-smoke' { & $python runner.py --agent smoke_test:profile_driver --task profile }
        'browsergym' {
            # BrowserGym 0.14.3 pins Playwright 1.44. Its bundled Chromium
            # failed to launch here; both browsers use the verified local build.
            $priorChromium = $env:WEBAGENT_CHROMIUM
            try {
                if (-not $env:WEBAGENT_CHROMIUM) {
                    $env:WEBAGENT_CHROMIUM = Join-Path $env:LOCALAPPDATA 'ms-playwright\chromium-1243\chrome-win64\chrome.exe'
                }
                & $python browsergym_smoke.py
            } finally {
                $env:WEBAGENT_CHROMIUM = $priorChromium
            }
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "Test process exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
