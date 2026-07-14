param(
    [int]$PollSeconds = 10,
    [switch]$BuildOnStart,
    [switch]$Once
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
$LogDir = Join-Path $ProjectRoot "instance\logs"
$LogFile = Join-Path $LogDir "auto_update_build.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"), $Message
    for ($attempt = 0; $attempt -lt 5; $attempt++) {
        try {
            Add-Content -Path $LogFile -Value $line
            break
        }
        catch {
            if ($attempt -eq 4) { throw }
            Start-Sleep -Milliseconds 200
        }
    }
    Write-Host $line
}

function Get-SourceHash {
    param(
        [string]$Root,
        [string[]]$Include
    )

    $files = foreach ($pattern in $Include) {
        Get-ChildItem -Path $Root -Recurse -File -Include $pattern -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch '\\(__pycache__|build|dist|specs|work)\\' -and
                $_.Name -ne "build_version.py"
            }
    }

    $fingerprint = $files |
        Sort-Object FullName |
        ForEach-Object {
            $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
            "{0}:{1}:{2}" -f $_.FullName.Substring($ProjectRoot.Path.Length), $_.Length, $hash
        }

    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($fingerprint -join "`n"))
    $sha = [System.Security.Cryptography.SHA256]::Create()
    return [System.BitConverter]::ToString($sha.ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
}

function Build-AdminPanel {
    Write-Log "Admin Panel source changed. Building package..."
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & python (Join-Path $ProjectRoot "installer\build\build_admin_panel.py") 2>&1 |
        ForEach-Object { Write-Log "ADMIN: $_" }
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    if ($exitCode -ne 0) {
        throw "Admin Panel build failed with exit code $exitCode"
    }
    Write-Log "Admin Panel package published."
}

function Build-DesktopClient {
    Write-Log "Desktop Client source changed. Building package..."
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "desktop-client\build_client.ps1") 2>&1 |
        ForEach-Object { Write-Log "DESKTOP: $_" }
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    if ($exitCode -ne 0) {
        throw "Desktop Client build failed with exit code $exitCode"
    }
    Write-Log "Desktop Client package published."
}

$AdminRoot = Join-Path $ProjectRoot "admin-panel"
$DesktopRoot = Join-Path $ProjectRoot "desktop-client"
$AdminHash = Get-SourceHash -Root $AdminRoot -Include @("*.py", "*.png", "*.ico")
$DesktopHash = Get-SourceHash -Root $DesktopRoot -Include @("*.py", "*.png", "*.ico")

Write-Log "Auto update publisher started. PollSeconds=$PollSeconds BuildOnStart=$BuildOnStart Once=$Once"

if ($BuildOnStart) {
    Build-AdminPanel
    Build-DesktopClient
    $AdminHash = Get-SourceHash -Root $AdminRoot -Include @("*.py", "*.png", "*.ico")
    $DesktopHash = Get-SourceHash -Root $DesktopRoot -Include @("*.py", "*.png", "*.ico")
}

do {
    Start-Sleep -Seconds $PollSeconds

    $nextAdminHash = Get-SourceHash -Root $AdminRoot -Include @("*.py", "*.png", "*.ico")
    $nextDesktopHash = Get-SourceHash -Root $DesktopRoot -Include @("*.py", "*.png", "*.ico")

    if ($nextAdminHash -ne $AdminHash) {
        try {
            Build-AdminPanel
            $AdminHash = Get-SourceHash -Root $AdminRoot -Include @("*.py", "*.png", "*.ico")
        }
        catch {
            Write-Log "ADMIN ERROR: $_"
            $AdminHash = $nextAdminHash
        }
    }

    if ($nextDesktopHash -ne $DesktopHash) {
        try {
            Build-DesktopClient
            $DesktopHash = Get-SourceHash -Root $DesktopRoot -Include @("*.py", "*.png", "*.ico")
        }
        catch {
            Write-Log "DESKTOP ERROR: $_"
            $DesktopHash = $nextDesktopHash
        }
    }
}
while (-not $Once)

Write-Log "Auto update publisher stopped."
