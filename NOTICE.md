# 致谢与许可

## 原包和 AE

原包来自[酷安作者分享帖](https://www.coolapk.com/feed/74091859)，感谢原作者的分享。这里是在原包基础上做 AE 适配和修复，原 ROM 的署名与许可仍然保留。

虚拟机项目：[AEmulator / uxazu](https://github.com/uxazu/AEmulator)。本项目基于 **AE 0.0.0.3**，其他版本还没测试。

## 本项目

维护者：poohpiggy。修复和文档整理过程中使用了 Codex 辅助。

自己写的工具、补丁脚本和文档使用根目录的 [MIT 许可](LICENSE)。ROM、第三方 APK、字体、音频和主题素材仍归各自作者，Release 中的整个 ROM 包不适用 MIT。

## 资源补丁

- `assets/icons.static.zip` 由原 ROM 主题素材整理，图片保留原有权利。`tools/MaskIcons.java` 是处理圆角的代码。
- `overlay/recents/` 是多任务资源 overlay 的源码，`assets/AEGuestRecents.apk` 是对应 APK。签名私钥未公开。
- 构建用的商店 APK 和 66 个原生库不放在源码仓库中，由构建工具从自行准备的基包中提取。
