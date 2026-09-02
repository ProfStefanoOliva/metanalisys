$ErrorActionPreference = "Stop"

$Version = "v0.1.0-alpha.9"
$PlatformName = "Windows-x64"
$AppName = "metanalisys"
$PackageName = "$AppName-$Version-$PlatformName"

$RepoRoot = Split-Path -Parent $PSCommandPath
$DistRoot = Join-Path $RepoRoot "dist"
$PackageDir = Join-Path $DistRoot $PackageName
$PyInstallerDir = Join-Path $DistRoot $AppName
$ZipPath = Join-Path $DistRoot "$PackageName.zip"
$SpecPath = Join-Path $RepoRoot "metanalisys_windows_portable.spec"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"

function Remove-LocalPathIfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,
        [Parameter(Mandatory = $true)]
        [string] $AllowedRoot
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $fullAllowedRoot = [System.IO.Path]::GetFullPath($AllowedRoot)

    if (-not $fullPath.StartsWith($fullAllowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside expected directory: $fullPath"
    }

    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Recurse -Force
    }
}

Set-Location -LiteralPath $RepoRoot

if (-not [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)) {
    throw "This script must be run on Windows."
}

if (-not [Environment]::Is64BitProcess) {
    throw "This script must be run from a 64-bit PowerShell process."
}

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Virtual environment Python not found: $PythonPath. Create .venv and install runtime/build requirements first."
}

if (-not (Test-Path -LiteralPath $SpecPath)) {
    throw "PyInstaller spec file not found: $SpecPath"
}

foreach ($requiredFile in @("LICENSE", "README_PORTABLE.txt")) {
    $requiredPath = Join-Path $RepoRoot $requiredFile
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required packaging file not found: $requiredPath"
    }
}

$pythonMachine = (& $PythonPath -c "import platform; print(platform.machine())").Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect virtual environment Python architecture."
}
if ($pythonMachine -notin @("AMD64", "x86_64")) {
    throw "Expected a Windows x64 Python virtual environment, found architecture: $pythonMachine"
}

& $PythonPath -c "import customtkinter, PIL"
if ($LASTEXITCODE -ne 0) {
    throw "Runtime dependencies are missing in .venv. Install them with: .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt"
}

& $PythonPath -m PyInstaller --version
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not available in .venv. Install build dependencies with: .\.venv\Scripts\python.exe -m pip install -r .\requirements-build.txt"
}

Remove-LocalPathIfExists -Path $PackageDir -AllowedRoot $DistRoot
Remove-LocalPathIfExists -Path $ZipPath -AllowedRoot $DistRoot

& $PythonPath -m PyInstaller --clean --noconfirm $SpecPath
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

if (-not (Test-Path -LiteralPath $PyInstallerDir)) {
    throw "Expected PyInstaller output directory not found: $PyInstallerDir"
}

Move-Item -LiteralPath $PyInstallerDir -Destination $PackageDir

Copy-Item -LiteralPath (Join-Path $RepoRoot "LICENSE") -Destination $PackageDir
Copy-Item -LiteralPath (Join-Path $RepoRoot "README_PORTABLE.txt") -Destination $PackageDir

Compress-Archive -LiteralPath $PackageDir -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host "Portable package created:"
Write-Host $ZipPath
