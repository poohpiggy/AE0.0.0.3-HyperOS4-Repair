# 最开始那步：把 VK 路线改成 GL

这次折腾一开始的要求就很明确：**在 AE 0.0.0.3 里跑 HyperOS 4，而且只用 OpenGL ES，不走 Vulkan。**

平时说“VK 转 GL”比较顺口，实际做的是把这份 ROM 的渲染路线切到 GLES，再补它遇到的兼容问题。现在保留的记录不能证明写出过一个通用的 Vulkan→OpenGL API 翻译器，所以这里按当时真正做过的东西写。

## 一开始查到了什么

解开系统包和两个 Vendor 包后，发现不只是一个默认渲染器的问题：Vendor 还给设置、桌面、SystemUI 等应用单独开了 Vulkan。只改一个全局属性，应用还是可能继续走 VK。

当时的原包说明还提到玻璃效果依赖新版 Vulkan 驱动，所以“关掉 VK”不代表原来的视觉效果也一定能完整保留。

## 当时怎么改

1. 关全局和逐应用的 Vulkan 开关。
2. 指定 HWUI 用 `skiagl`，Flutter 用 `impelleropengl`。
3. 清理 Vendor 里的 Vulkan 驱动和功能声明。历史记录写的是每份 Vendor 移除 3 个驱动、4 个功能声明；原始删除清单现在没有保留下来，这里不猜具体文件名。
4. 检查启动 ramdisk，避免开机时又把配置改回去。
5. 分别生成 MIX2S 和 MIX3 的实验包，跑文件系统与压缩包检查，再去 AE 里试。

后来 R2 清单里还能看到这些配置，原值保存在 `manifests/gles-properties.json`：

```properties
debug.hwui.renderer=skiagl
debug.flutter.renderer=impelleropengl
debug.renderengine.backend=skiagl
ro.hwui.use_vulkan=false
persist.sys.hwui.partial.vk=false
persist.sys.vk_mode_enabled=false
```

这些属性是这份包用过的配置，不是“随便找一台手机照抄就能修好”的通用答案。

## 换成 GL 之后，事情还没结束

最先遇到的是原生桌面启动和 Flutter GLES 首帧白屏。后面又碰到图标黑块、纹理上传同步、视频的 YUV/RGB 路径等问题。

历史记录里明确提到做过 YUV→RGB 兼容库，沿用 AE 已有 GLES 通信接口，没有改 AE APK。这个是视频颜色数据的转换，和“VK→GL”的 API 转译不是一件事。

后来的思路是：能开桌面还不够，要滑动、进设置、返回、重启，再看图标和视频。几条报错没了，也不代表画面就一定正常。详细过程在 [排错记录](troubleshooting.md)。

## 现在还剩什么

R3 继承了基包的 GLES 兼容改动。普通图标和主要交互当时已经跑通，但时钟/日历动态图标、液态玻璃仍有单独的问题，不能一起算成“全修好了”。

早期原生补丁的完整源文件已经随旧工作区清理，公开仓库保留了能找到的脚本、配置、哈希和过程，没有拿新写的代码冒充当时源码。
