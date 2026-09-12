# OptiScaler DLSSNR Pre-SR Multipass CN

社区简体中文派生仓库。构建时从 `wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass` 拉取源码，不长期复制整个上游。

- 上游：`https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass`
- 跟踪分支：`main`
- 中文框架复用自 `Night-SHANG/OptiScaler-CN`
- 未翻译 UI 自动回退英文
- 同时保存当前开发分支与最新稳定 Release 的 UI 清单
- GitHub Actions 每日自动扫描、构建，并在上游出现新稳定版本时发布中文版 Release

> 本仓库不是 wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass 官方项目。

## DLSS Neural Rendering 额外要求

`nvngx_dlssnr.dll` 是 NVIDIA 专有运行库，不包含在本仓库 Release 中，也不会由本仓库重新分发。请按照上游项目说明自行提供。

当前上游稳定版还包含经过校验的 Pre-SR / Multipass hybrid 资产。本仓库发布时调用上游 `get_hybrid_assets.ps1` 获取这些资产，再交给上游 `package_release.ps1` 校验并打包；获取或校验失败时会停止 Release，不会发布缺少 hybrid 资源的残缺包。

## 本地化

核心翻译文件：`Localization/zh-CN.json`。普通 OptiScaler UI 优先复用已有翻译，Fork 新增的 DLSSNR UI 由扫描器单独发现。

## 自动维护

`Upstream Sync` 每天检查一次，也支持手动运行。发生源码注入锚点变化、扫描结构错误或编译失败时停止发布，不覆盖稳定版本。
