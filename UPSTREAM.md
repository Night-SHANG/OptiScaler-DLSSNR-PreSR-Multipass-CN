# Upstream

- Repository: `https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass`
- Development branch: `main`
- Stable channel: latest non-draft, non-prerelease GitHub Release

本仓库只维护本地化层、扫描/构建/发布工具和语言资源。CI 在干净环境拉取指定上游 ref。

DLSSNR Fork 的正式打包使用其自带 `package_release.ps1`，以保留 forwarder、文档及上游的安全检查；`nvngx_dlssnr.dll` 不会被打包。

当前 wilsjo2 稳定 Release 还包含验证过的 hybrid 资产。本仓库先调用上游 `get_hybrid_assets.ps1` 获取资产，再把找到的 `asset-manifest.json` 所在目录通过 `-HybridAssetsDirectory` 交给上游 packager；任何获取、manifest 定位或上游哈希校验失败都会阻断发布。

## Maintenance checkpoint: 2026-10-31

- Development build pinned to `6125a75b37f7e2a408e31934f4827e5660429203` (`main`, upstream tag `v0.8.10`). GitHub marks this release **prerelease**; it is not promoted to the stable channel.
- Latest non-prerelease release remains `v0.8.3`, source `47e134cb` (full SHA is recorded in `Localization/stable/meta.json`). Existing release tracking is retained until an actual authorized successful release.
- Pushing localization changes to `main` can automatically publish via the existing workflows. A maintenance-branch PR runs the read-only build/check workflows; publication still requires separate approval. This maintenance does not change workflow triggers or permissions.
