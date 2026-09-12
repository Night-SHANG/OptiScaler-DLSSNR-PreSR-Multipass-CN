param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$UpstreamRef = "unknown"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$cfg = Get-Content (Join-Path $repo "upstream.json") -Raw | ConvertFrom-Json
$sha = (git -C $SourceRoot rev-parse --short=12 HEAD).Trim()
$safeRef = $UpstreamRef -replace '[^A-Za-z0-9._-]','-'
$version = "cn-$safeRef-$sha"
$upstreamPackager = Join-Path $SourceRoot "package_release.ps1"
if (-not (Test-Path -LiteralPath $upstreamPackager)) {
    throw "Fork package_release.ps1 not found: $upstreamPackager"
}

# Current wilsjo2 releases ship verified precompiled FP8/NVFP4 hybrid assets.
# Fetch them through the fork's own helper, then give the verified directory to
# package_release.ps1.  Fail closed instead of silently publishing a CN archive
# that is missing functionality present in the upstream release.
$hybridFetcher = Join-Path $SourceRoot "get_hybrid_assets.ps1"
if (-not (Test-Path -LiteralPath $hybridFetcher)) {
    throw "Fork get_hybrid_assets.ps1 not found; refusing to package without upstream hybrid assets"
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$hybridScratch = Join-Path $OutputDir "_hybrid-assets"
if (Test-Path -LiteralPath $hybridScratch) { Remove-Item $hybridScratch -Recurse -Force }
# Important: get_hybrid_assets.ps1 requires its destination path to NOT exist.
# It creates the destination itself after validating the requested location.

$command = Get-Command $hybridFetcher
$invokeArgs = @{}
$destinationParam = @('Destination','OutputDirectory','OutputDir','TargetDirectory','AssetDirectory') |
    Where-Object { $command.Parameters.ContainsKey($_) } | Select-Object -First 1
if ($destinationParam) { $invokeArgs[$destinationParam] = $hybridScratch }

$commonParameters = @('Verbose','Debug','ErrorAction','WarningAction','InformationAction','ProgressAction',
                      'ErrorVariable','WarningVariable','InformationVariable','OutVariable','OutBuffer','PipelineVariable')
$unknownMandatory = @()
foreach ($item in $command.Parameters.GetEnumerator()) {
    if ($commonParameters -contains $item.Key) { continue }
    if ($destinationParam -and $item.Key -eq $destinationParam) { continue }
    $mandatory = $false
    foreach ($attr in $item.Value.Attributes) {
        if ($attr -is [System.Management.Automation.ParameterAttribute] -and $attr.Mandatory) {
            $mandatory = $true
            break
        }
    }
    if ($mandatory) { $unknownMandatory += $item.Key }
}
if ($unknownMandatory.Count -gt 0) {
    throw "Upstream get_hybrid_assets.ps1 gained unsupported mandatory parameter(s): $($unknownMandatory -join ', ')"
}

Push-Location $SourceRoot
try {
    & $hybridFetcher @invokeArgs
    if (-not $?) { throw "Upstream get_hybrid_assets.ps1 failed" }
}
finally {
    Pop-Location
}

$manifestCandidates = @()
foreach ($searchRoot in @($hybridScratch, $SourceRoot)) {
    if (Test-Path -LiteralPath $searchRoot) {
        $manifestCandidates += Get-ChildItem -LiteralPath $searchRoot -Filter "asset-manifest.json" -File -Recurse -ErrorAction SilentlyContinue
    }
}
$hybridManifest = $manifestCandidates | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.Directory.FullName "OptiScaler\nvfp4\hybrid")
} | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
if (-not $hybridManifest) {
    throw "get_hybrid_assets.ps1 completed but no valid asset-manifest.json + OptiScaler/nvfp4/hybrid tree was found"
}
$hybridAssetsDirectory = $hybridManifest.Directory.FullName
Write-Host "Hybrid assets: $hybridAssetsDirectory"

# Let the fork's own packager enforce its release allow-list, hashes, portable
# defaults and proprietary-runtime exclusions.  We only wrap the resulting ZIP
# with the community CN config/docs.
& $upstreamPackager -Version $version -SkipBuild -HybridAssetsDirectory $hybridAssetsDirectory
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$releaseDir = Join-Path $SourceRoot "release"
$sourceZip = Get-ChildItem -LiteralPath $releaseDir -Filter "*.zip" -File |
    Where-Object { $_.Name -like "*$version*" } |
    Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
if (-not $sourceZip) { throw "Upstream packager did not create a ZIP for $version" }
$stage = Join-Path $OutputDir "_stage"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Expand-Archive -LiteralPath $sourceZip.FullName -DestinationPath $stage -Force
Copy-Item (Join-Path $repo "Localization\OptiScalerCN.ini") (Join-Path $stage "OptiScalerCN.ini") -Force
Copy-Item (Join-Path $repo "README.zh-CN.md") (Join-Path $stage "README.CN.zh-CN.md") -Force
Copy-Item (Join-Path $repo "UPSTREAM.md") (Join-Path $stage "UPSTREAM.CN.md") -Force
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$name = "$($cfg.package_prefix)-$safeRef-$sha.zip"
$zip = Join-Path $OutputDir $name
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
@{
    upstream_repository = $cfg.repository
    upstream_ref = $UpstreamRef
    upstream_commit = (git -C $SourceRoot rev-parse HEAD).Trim()
    package = (Split-Path -Leaf $zip)
    sha256 = $hash
    hybrid_assets = $true
    built_at_utc = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $OutputDir "build-metadata.json")
Remove-Item $stage -Recurse -Force
Remove-Item $hybridScratch -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "PACKAGE=$zip"
Write-Host "SHA256=$hash"
