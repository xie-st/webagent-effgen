param(
    [ValidateSet('site','smoke','browsergym','runner-smoke')]
    [string]$Mode = 'site',
    [ValidateSet('normal','slow','rate','login')]
    [string]$Scenario = 'normal'
)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $env:PYTHONUTF8 = '1'
    switch ($Mode) {
        'site' { & '.venv\Scripts\python.exe' sandbox.py --scenario $Scenario }
        'smoke' { & '.venv\Scripts\python.exe' smoke_test.py }
        'runner-smoke' { & '.venv\Scripts\python.exe' runner.py --agent smoke_test:profile_driver --task profile }
        'browsergym' {
            # BrowserGym 0.14.3 pins Playwright 1.44. Its bundled Chromium
            # failed to launch here; both browsers use the verified local build.
            $priorChromium = $env:WEBAGENT_CHROMIUM
            try {
                if (-not $env:WEBAGENT_CHROMIUM) {
                    $env:WEBAGENT_CHROMIUM = Join-Path $env:LOCALAPPDATA 'ms-playwright\chromium-1243\chrome-win64\chrome.exe'
                }
                & '.venv-browsergym\Scripts\python.exe' browsergym_smoke.py
            } finally {
                $env:WEBAGENT_CHROMIUM = $priorChromium
            }
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "Test process exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
