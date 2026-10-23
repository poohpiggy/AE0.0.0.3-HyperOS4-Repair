# 天气与浏览器安装问题

## 天气、主题与运行库声明

运行库文件实际存在，但 PackageManager 没读到匹配声明时，应用可能安装失败。R3 在 `/system_ext/etc/permissions/` 补充：

| library name | ROM 内实际路径 |
| --- | --- |
| `hyperos.rustruntime.v3` | `/system_ext/framework/hyperos.rustruntime.jar` |
| `hyperos.rustruntime.v5` | `/system_ext/framework/hyperos.rustruntime.jar` |
| `miui-uninstall-empty.jar` | `/mi_ext/product/framework/miui-uninstall-empty.jar` |

声明不是空造库：原文件先被确认存在。库注册修复不等于已经逐项验证所有应用的原生功能。启动脚本仅在应用缺失时尝试安装原包天气/主题 APK，保留已安装版本和用户数据。

## 浏览器签名冲突

旧 `/product/priv-app/MIUIBrowser/MIUIBrowser.apk` 移出预置扫描位置，备份到 `/system/etc/aemu-compat/backups/MIUIBrowser.original.apk`，再安装商店原签名浏览器版本 `20.30.1021023`。未禁用签名校验。

构建时核对两个已知文件：

- 旧浏览器 SHA-256：`8c097aeb2f7d9232cd9dc5c974fdf8054978482fa86a34a5e7d2afe5b9844a23`
- 替换浏览器 SHA-256：`1f5e546a133a4b6530dd183e711648a6de0d0e4c78049b646c2e52bf4035d75a`

APK 不存入源码仓库。历史修复的成功结论来自当时安装验证，不推广为任意后续商店版本都能安装。
