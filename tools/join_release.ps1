# Windows PowerShell 5.1+; no Python or archiver required.
param([string]$ManifestPath = (Join-Path $PSScriptRoot 'parts.json'))
$ErrorActionPreference = 'Stop'
$manifestFile = Get-Item -LiteralPath $ManifestPath
$folder = $manifestFile.DirectoryName
$manifest = Get-Content -LiteralPath $manifestFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
$names = @($manifest.archive.name) + @($manifest.parts | ForEach-Object { $_.name })
foreach ($name in $names) {
    if ($name -match '[/\\:]' -or [IO.Path]::GetFileName($name) -ne $name) { throw 'Unsafe file name.' }
}
$dest = Join-Path $folder $manifest.archive.name
$partial = "$dest.partial"
if ((Test-Path -LiteralPath $dest) -or (Test-Path -LiteralPath $partial)) { throw 'Output or partial file already exists.' }
$sum = ($manifest.parts | Measure-Object -Property size -Sum).Sum
if ($manifest.parts.Count -eq 0 -or $sum -ne $manifest.archive.size) { throw 'Invalid part sizes.' }
$created = $false
try {
    $output = [IO.File]::Open($partial, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    $created = $true
    try {
        foreach ($part in $manifest.parts) {
            $path = Join-Path $folder $part.name
            $file = Get-Item -LiteralPath $path
            if ($file.Length -ne $part.size) { throw "Part size mismatch: $($part.name)" }
            if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $part.sha256) { throw "Part hash mismatch: $($part.name)" }
            $inputFile = [IO.File]::OpenRead($path)
            try { $inputFile.CopyTo($output) } finally { $inputFile.Dispose() }
            Write-Host "Joined $($part.name)"
        }
    } finally { $output.Dispose() }
    if ((Get-Item -LiteralPath $partial).Length -ne $manifest.archive.size) { throw 'ZIP size mismatch.' }
    if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.archive.sha256) { throw 'ZIP SHA-256 mismatch.' }
    [IO.File]::Move($partial, $dest)
    Write-Host "Verified ZIP: $dest"
} catch {
    if ($created -and (Test-Path -LiteralPath $partial)) { Remove-Item -LiteralPath $partial }
    throw
}
