# HyperOS 4 for AE 0.0.0.3

在 AE 0.0.0.3 上跑 HyperOS 4 的一些修修补补。保留原生小米桌面，渲染走 OpenGL ES。

最开始只是想把 Vulkan 换成 GL，后面一路修到了桌面、图标、声音和模拟电话，最近又补了分辨率适配、多任务和首次开机的铃声扫描。脚本和折腾过程都放在这个仓库里。

[下载](https://github.com/poohpiggy/AE0.0.0.3-HyperOS4-Repair/releases/tag/hyperos4-ae0.0.0.3) · [导入说明](docs/import-guide.md) · [修改日志](CHANGELOG.md) · [排错记录](docs/troubleshooting.md)

## 怎么用

这个包用于 **AE 0.0.0.3 虚拟机**，不能给实体手机刷。

1. 到 Release 下载三个分卷、`parts.json` 和合并脚本，按[说明](docs/release-download.md)合并成 ZIP。
2. 在 AE 里新建实例，导入 `HyperOS4-AE0.0.0.3.zip`。
3. 推荐 **1080×2160 / 403 DPI**。第一次启动等约 2–3 分钟，初始化完成后重启一次。

**K80、Neo11 都已测试，可以导入运行。** 默认的 540×960 / 240 DPI 也能启动。之后想换分辨率，改 AE 的实例设置再重启就行。

## 最近改了什么

- 分辨率和 DPI 在 SurfaceFlinger 启动前同步，解决改完参数后画面缩小、裁切的问题。
- 修了多任务卡片空白，能看到设置和浏览器的预览。
- 补齐浏览器缺的 66 个 ARM64 库，解决预置浏览器首次启动闪退。
- 天气、日历和时钟换用静态兼容图标，调整了圆角和大小。
- 首次开机等媒体服务准备好再扫描铃声，干净导入后能自动登记全部 56 个内置音频。

具体怎么查出来的，放在[这次的修复记录](docs/latest-repairs.md)里。之前的 VK → GL、WebView、音频和模拟电话等改动见[折腾经过](docs/journey.md)。

## 还有哪些问题

- 液态玻璃、部分图标黑块还没解决。
- 安全中心仍有启动异常。
- 日历日期和时钟指针是固定的，不会实时更新。

分辨率切换测了 720×1280 / 320 和 1080×2160 / 403 两组。更详细的测试情况见[测试记录](docs/validation.md)。

## 文件和源码

包体约 **4.48 GB**，Release 里分成了三卷。合并脚本会检查文件哈希，别混用旧分卷。

SHA-256：

```text
f55fceb63243a7f89533de1f341f3329c7da6c83e5ce6746d69a0167d7704391
```

仓库里的 `payload/` 是系统脚本和配置，`overlay/`、`assets/` 是多任务和图标补丁，`tools/` 放打包、校验和合并工具。构建方法见[构建说明](docs/build.md)。

早期部分原生补丁的源码没留下来，所以这里还不是能从原厂 ROM 一键构建的完整工程。完整 ROM 从 Release 下载。

## 致谢

原包来自[酷安原作者的分享](https://www.coolapk.com/feed/74091859)，AE 项目见 [AEmulator](https://github.com/uxazu/AEmulator)。感谢原作者和上游的工作。

自己写的脚本和文档使用 [MIT](LICENSE)，ROM、APK 和主题素材仍按各自的许可。详细说明见 [NOTICE](NOTICE.md)。
