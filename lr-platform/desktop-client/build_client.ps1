$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
$ClientRoot = Resolve-Path "$ProjectRoot\desktop-client"
$OutputDir = Join-Path $ProjectRoot "backend\static\client"
$IconPath = Join-Path $ClientRoot "resources\lr-remote-logo.ico"
$LogoPath = Join-Path $ClientRoot "resources\lr-remote-logo.png"
$UpdaterPath = Join-Path $ProjectRoot "backend\static\updater\LR Updater.exe"
$ManifestDir = Join-Path $ProjectRoot "backend\static\app-updates"
$VersionFile = Join-Path $ClientRoot "build_version.py"
$PythonRoot = Split-Path -Parent (python -c "import sys; print(sys.executable)")
$TkinterLibPath = Join-Path $PythonRoot "Lib\tkinter"
$TclDataPath = Join-Path $PythonRoot "tcl\tcl8.6"
$TkDataPath = Join-Path $PythonRoot "tcl\tk8.6"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
New-Item -ItemType Directory -Force -Path $ManifestDir | Out-Null

python -m pip install -r "$ClientRoot\requirements.txt"

if (!(Test-Path $UpdaterPath)) {
    python "$ProjectRoot\installer\build\build_updater.py"
}

if (!(Test-Path $IconPath)) {
    python -c "from PIL import Image; img=Image.open(r'$LogoPath').convert('RGBA'); img.save(r'$IconPath', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])"
}

$Version = (Get-Date).ToUniversalTime().ToString("yyyy.MM.dd.HHmmss")
Set-Content -Path $VersionFile -Encoding UTF8 -Value "APP_VERSION = `"$Version`""

Push-Location $ClientRoot
try {
    python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name lr_remote_access_client `
        --icon "$IconPath" `
        --collect-all customtkinter `
        --collect-submodules tkinter `
        --hidden-import _tkinter `
        --hidden-import tkinter `
        --hidden-import tkinter.constants `
        --hidden-import tkinter.filedialog `
        --hidden-import tkinter.font `
        --hidden-import tkinter.messagebox `
        --hidden-import tkinter.ttk `
        --add-data "$TkinterLibPath;tkinter" `
        --add-data "$TclDataPath;_tcl_data" `
        --add-data "$TkDataPath;_tk_data" `
        --add-data "$ClientRoot\resources;resources" `
        --add-data "$UpdaterPath;resources" `
        --distpath "$OutputDir" `
        --workpath "$ClientRoot\build" `
        --specpath "$ClientRoot\build" `
        main.py
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

$ExePath = Join-Path $OutputDir "lr_remote_access_client.exe"
if (!(Test-Path $ExePath)) {
    throw "Build failed: $ExePath was not created."
}

$Hash = (Get-FileHash -Path $ExePath -Algorithm SHA256).Hash.ToLowerInvariant()
$Manifest = [ordered]@{
    app_id = "desktop-client"
    app_name = "Desktop Client"
    version = $Version
    file_name = "lr_remote_access_client.exe"
    file_path = $ExePath
    sha256 = $Hash
    released_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}
$ManifestJson = $Manifest | ConvertTo-Json
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Join-Path $ManifestDir "desktop-client.json"), $ManifestJson, $Utf8NoBom)

Write-Host "Built $ExePath"
