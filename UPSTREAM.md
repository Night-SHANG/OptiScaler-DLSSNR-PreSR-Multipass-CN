# Upstream

- Repository: `https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass`
- Development branch: `main`
- Stable channel: latest non-draft, non-prerelease GitHub Release

本仓库只维护本地化层、扫描/构建/发布工具和语言资源。CI 在干净环境拉取指定上游 ref。

DLSSNR Fork 的正式打包使用其自带 `package_release.ps1`，以保留 forwarder、文档及上游的安全检查；`nvngx_dlssnr.dll` 不会被打包。

当前 wilsjo2 稳定 Release 还包含验证过的 hybrid 资产。本仓库先调用上游 `get_hybrid_assets.ps1` 获取资产，再把找到的 `asset-manifest.json` 所在目录通过 `-HybridAssetsDirectory` 交给上游 packager；任何获取、manifest 定位或上游哈希校验失败都会阻断发布。
