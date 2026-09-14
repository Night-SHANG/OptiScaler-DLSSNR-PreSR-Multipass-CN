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
$upstreamPackager = Join-Path $SourceRoot "package_release.ps1"
if (-not (Test-Path -LiteralPath $upstreamPackager)) {
    throw "Fork package_release.ps1 not found: $upstreamPackager"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$releaseDir = Join-Path $SourceRoot "release"
$packagerCommand = Get-Command $upstreamPackager
$supportsHybridAssets = $packagerCommand.Parameters.ContainsKey('HybridAssetsDirectory')
$supportsRtx40Mfg = $packagerCommand.Parameters.ContainsKey('EnableRtx40Mfg')

# Fail closed if upstream changes the package interface in a way this wrapper
# does not understand.  v0.7.7 uses HybridAssetsDirectory; v0.8.3 adds the
# EnableRtx40Mfg dual-build contract and no longer needs the old hybrid helper.
$commonParameters = @('Verbose','Debug','ErrorAction','WarningAction','InformationAction','ProgressAction',
                      'ErrorVariable','WarningVariable','InformationVariable','OutVariable','OutBuffer','PipelineVariable')
$knownPackagerParameters = @('Version','SkipBuild','HybridAssetsDirectory','EnableRtx40Mfg')
$unknownMandatory = @()
foreach ($item in $packagerCommand.Parameters.GetEnumerator()) {
    if ($commonParameters -contains $item.Key) { continue }
    if ($knownPackagerParameters -contains $item.Key) { continue }
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
    throw "Upstream package_release.ps1 gained unsupported mandatory parameter(s): $($unknownMandatory -join ', ')"
}
if (-not $supportsHybridAssets -and -not $supportsRtx40Mfg) {
    throw "Unsupported upstream package_release.ps1 contract: expected HybridAssetsDirectory or EnableRtx40Mfg"
}

$hybridScratch = $null
$hybridAssetsDirectory = $null
if ($supportsHybridAssets) {
    # Legacy releases use the upstream helper to fetch and verify FP8/NVFP4
    # hybrid assets before package_release.ps1 is allowed to run.
    $hybridFetcher = Join-Path $SourceRoot "get_hybrid_assets.ps1"
    if (-not (Test-Path -LiteralPath $hybridFetcher)) {
        throw "Fork get_hybrid_assets.ps1 not found; refusing to package legacy release without upstream hybrid assets"
    }
    $hybridScratch = Join-Path $OutputDir "_hybrid-assets"
    if (Test-Path -LiteralPath $hybridScratch) { Remove-Item $hybridScratch -Recurse -Force }
    # Important: get_hybrid_assets.ps1 requires its destination path to NOT exist.
    # It creates the destination itself after validating the requested location.

    $hybridCommand = Get-Command $hybridFetcher
    $invokeArgs = @{}
    $destinationParam = @('Destination','OutputDirectory','OutputDir','TargetDirectory','AssetDirectory') |
        Where-Object { $hybridCommand.Parameters.ContainsKey($_) } | Select-Object -First 1
    if ($destinationParam) { $invokeArgs[$destinationParam] = $hybridScratch }

    $unknownHybridMandatory = @()
    foreach ($item in $hybridCommand.Parameters.GetEnumerator()) {
        if ($commonParameters -contains $item.Key) { continue }
        if ($destinationParam -and $item.Key -eq $destinationParam) { continue }
        $mandatory = $false
        foreach ($attr in $item.Value.Attributes) {
            if ($attr -is [System.Management.Automation.ParameterAttribute] -and $attr.Mandatory) {
                $mandatory = $true
                break
            }
        }
        if ($mandatory) { $unknownHybridMandatory += $item.Key }
    }
    if ($unknownHybridMandatory.Count -gt 0) {
        throw "Upstream get_hybrid_assets.ps1 gained unsupported mandatory parameter(s): $($unknownHybridMandatory -join ', ')"
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
}

function Invoke-UpstreamPackage {
    param(
        [Parameter(Mandatory=$true)][string]$PackageVersion,
        [bool]$Rtx40Mfg = $false
    )

    $args = @{
        Version = $PackageVersion
        SkipBuild = $true
    }
    if ($supportsHybridAssets) {
        $args['HybridAssetsDirectory'] = $hybridAssetsDirectory
    }
    if ($Rtx40Mfg) {
        if (-not $supportsRtx40Mfg) {
            throw "RTX 40 MFG package requested but upstream packager does not expose -EnableRtx40Mfg"
        }
        $args['EnableRtx40Mfg'] = $true
    }

    Push-Location $SourceRoot
    try {
        & $upstreamPackager @args
        if (-not $?) { throw "Upstream package_release.ps1 failed for $PackageVersion" }
    }
    finally {
        Pop-Location
    }

    $sourceZip = Get-ChildItem -LiteralPath $releaseDir -Filter "*.zip" -File |
        Where-Object { $_.Name -like "*$PackageVersion*" } |
        Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if (-not $sourceZip) {
        throw "Upstream packager did not create a ZIP for $PackageVersion"
    }
    return $sourceZip
}

function New-CnPackage {
    param(
        [Parameter(Mandatory=$true)]$SourceZip,
        [Parameter(Mandatory=$true)][string]$Variant,
        [string]$NameSuffix = ""
    )

    $stage = Join-Path $OutputDir ("_stage-" + $Variant)
    if (Test-Path -LiteralPath $stage) { Remove-Item $stage -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    Expand-Archive -LiteralPath $SourceZip.FullName -DestinationPath $stage -Force
    Copy-Item (Join-Path $repo "Localization\OptiScalerCN.ini") (Join-Path $stage "OptiScalerCN.ini") -Force
    Copy-Item (Join-Path $repo "README.zh-CN.md") (Join-Path $stage "README.CN.zh-CN.md") -Force
    Copy-Item (Join-Path $repo "UPSTREAM.md") (Join-Path $stage "UPSTREAM.CN.md") -Force

    $name = "$($cfg.package_prefix)-$safeRef-$sha$NameSuffix.zip"
    $zip = Join-Path $OutputDir $name
    if (Test-Path -LiteralPath $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    Remove-Item $stage -Recurse -Force

    return [pscustomobject]@{
        variant = $Variant
        package = (Split-Path -Leaf $zip)
        sha256 = $hash
    }
}

$baseVersion = "cn-$safeRef-$sha"
$packages = @()
$standardSource = Invoke-UpstreamPackage -PackageVersion $baseVersion
$standardPackage = New-CnPackage -SourceZip $standardSource -Variant "standard"
$packages += $standardPackage

if ($supportsRtx40Mfg) {
    $mfgVersion = "$baseVersion-rtx40-mfg"
    $mfgSource = Invoke-UpstreamPackage -PackageVersion $mfgVersion -Rtx40Mfg $true
    $mfgPackage = New-CnPackage -SourceZip $mfgSource -Variant "rtx40-mfg" -NameSuffix "-rtx40-mfg"
    $packages += $mfgPackage
}

$metadata = [ordered]@{
    upstream_repository = $cfg.repository
    upstream_ref = $UpstreamRef
    upstream_commit = (git -C $SourceRoot rev-parse HEAD).Trim()
    package = $standardPackage.package
    sha256 = $standardPackage.sha256
    packages = @($packages)
    hybrid_assets = [bool]$supportsHybridAssets
    rtx40_mfg = [bool]$supportsRtx40Mfg
    built_at_utc = (Get-Date).ToUniversalTime().ToString('o')
}
$metadata | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $OutputDir "build-metadata.json")

if ($hybridScratch) {
    Remove-Item $hybridScratch -Recurse -Force -ErrorAction SilentlyContinue
}
foreach ($item in $packages) {
    Write-Host "PACKAGE=$($item.package)"
    Write-Host "SHA256=$($item.sha256)"
}
