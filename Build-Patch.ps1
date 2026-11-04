param(
    [string]$SourceRomFs = '',
    [string]$Output = '',
    [ValidateSet('', 'switch', 'emulator', 'both')][string]$Target = ''
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($SourceRomFs)) {
    $SourceRomFs = (Read-Host 'Original Japanese v1.0.3 RomFS folder').Trim('"')
}
if ([string]::IsNullOrWhiteSpace($Target)) {
    $packagePath = Join-Path $PSScriptRoot 'package.json'
    if (-not (Test-Path -LiteralPath $packagePath)) { throw 'Use a release ZIP or specify -Target switch/emulator/both.' }
    $Target = (Get-Content -LiteralPath $packagePath -Raw | ConvertFrom-Json).target
}
if ([string]::IsNullOrWhiteSpace($Output)) {
    $Output = Join-Path (Split-Path -Parent $PSScriptRoot) ('Iwakura-Aria-Korean-v0.5.1-' + $Target + '-Built')
}
$patchPython = (Get-Command python -ErrorAction Stop).Source
& $patchPython -X utf8 (Join-Path $PSScriptRoot 'apply_patch.py') --source-romfs $SourceRomFs --output $Output --target $Target
if ($LASTEXITCODE -ne 0) { throw 'Patch build failed. Check the error above. Original files were not changed.' }
Write-Host ('Finished: ' + $Output)
