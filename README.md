# AE 0.0.0.3 · HyperOS 4 修复记录与 R3 打包工具

> **基于 AEmulator（AE）0.0.0.3。** 在红米 K80 上运行 HyperOS 4 / MIX2S 客体，保留原生桌面，采用 OpenGL ES 渲染路径。

这是我排查 AE 虚拟机兼容问题、验证修复并整理 R3 导入包的折腾记录。仓库包含保留下来的修复脚本、库注册声明、打包工具和校验依据。文中的“客体”就是 AE 里面的虚拟系统。**补丁只改这里，不修改宿主系统或 AE APK。包体仅供 AE 导入，不用于实体 MIX2S 刷机。**

[折腾经过](docs/journey.md) · [怎么查错的](docs/troubleshooting.md) · [最早的 VK → GL](docs/gles-migration.md) · [修改日志](CHANGELOG.md) · [导入说明](docs/import-guide.md) · [验证记录](docs/validation.md) · [原包与致谢](NOTICE.md)

## 当前版本

| 项目 | 状态 |
| --- | --- |
| AE 基线 | **0.0.0.3**；不承诺其他 AE 版本兼容 |
| 客体 | HyperOS 4，MIX2S 适配包 |
| 显示配置 | AE 实例手动设为 **1080 × 2160 / 403 DPI** |
| 渲染路线 | OpenGL ES；不启用 Vulkan |
| R3 包体 | ZIP Deflate level 9 / ZIP64，4,393,500,616 bytes（约 4.39 GB / 4.09 GiB） |
| 当前使用状态 | 作者认为现有版本已基本满足日常使用需求 |
| 验证范围 | 既有实例单项修复及包体完整性已核验；**我已在 K80、Neo11 上完成 R3 导入测试，均可运行** |

## R3 做了什么

- **铃声与提示音**：通过 MediaProvider 为系统铃声、通知和闹钟建立索引，不搬运旧实例媒体数据库。
- **显示与原生界面密度**：同步 AE 实例几何、逻辑 DPI 和 MIUI 密度元数据。403 是本实例逻辑 DPI，并非声称 MIX2S 的出厂逻辑 DPI。
- **天气等预装应用**：补充 `hyperos.rustruntime.v3/v5` 和 `miui-uninstall-empty.jar` 的真实库声明；已安装应用保留，不清除用户数据或协议选择。
- **浏览器安装冲突**：旧预置 APK 移出扫描位置并备份，使用商店原签名版本，保留系统签名校验。
- **启动持久化**：兼容运行文件从系统分区恢复，默认设置仅首次应用；媒体扫描失败时不写成功标记。
- **打包与核验**：镜像合并后 `e2fsck -fn`，ZIP64 高压缩，再逐成员解压核对大小、SHA-256 和 CRC。

R2 已有的 GLES、WebView、音频、模拟电话/短信兼容改动由基包继承。本仓库没有恢复出全部历史原生补丁源码，不能据此声称能从原厂 ROM 一键重建整套 R2。

## 下载与导入

[下载最终 R3 Release](https://github.com/poohpiggy/AE0.0.0.3-HyperOS4-Repair/releases/tag/r3-ae0.0.0.3)。包体按 GitHub 单附件限制分卷；下载所有分卷及合并工具后，按 [合并说明](docs/release-download.md) 还原原始 ZIP。

原始 ZIP SHA-256：

```text
dd01bd45975d6b8a02a69aa0080320b47e8f160781fe2bf3940ee091f2919333
```

导入前在 AE 0.0.0.3 中配置 **1080 × 2160 / 403 DPI**。首次初始化后正常重启一次，详见 [导入说明](docs/import-guide.md)。

## 仓库结构

```text
payload/       保留下来的 Android 启动脚本和库声明
manifests/     R2 基线、R3 合并清单、原始 ZIP 校验清单
reports/       文件系统检查与历史构建摘要
tools/        参数化打包、ZIP 核验和分卷合并工具
tests/        校验工具的合成归档测试
docs/         排查过程、修复原理、导入和验证说明
```

打包入口见 [构建说明](docs/build.md)。本仓库不提交 ROM 镜像、商店 APK、旧实例用户数据或完整聊天原文。

## 关于这些 commits

之前的排查发生在 2026-10-21 至 2026-10-24（UTC+8）。这些 commits 是现在按实际改动分组补整理的，时间也是现在，没有往回改日期。有效的修复、没用的尝试、后来撤掉的东西和还没测到的部分都会写清楚。

## 许可与来源

项目自有脚本和文档采用 [MIT License](LICENSE)。**MIT 不覆盖 HyperOS ROM、APK、系统资源、AE 及其他第三方二进制。** 原包分享来源、AE 上游及署名范围见 [NOTICE.md](NOTICE.md)。
