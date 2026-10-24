# 改显示参数，为什么要赶在 SurfaceFlinger 前面

之前同步参数的地方在 spawner。它能改属性，却可能已经晚于合成缓冲区分配，所以会出现 `wm size` 对了、画面仍用旧尺寸的情况。

当前启动顺序：

1. 两份 SurfaceFlinger 服务定义都进入 `start-surfaceflinger.sh`。
2. 包装脚本调用 `display-profile.sh`，读取 AE 的 framebuffer 宽高和 `qemu.sf.lcd_density`。
3. 同步 MIUI 元数据，转换显示配置的 ABX，只处理 `local:0` 的旧强制宽高和密度；保留其他显示项、原权限和属主，最后原子替换。
4. 安装已验证的 upload-sync 驱动，再执行真正的 SurfaceFlinger。
5. spawner 仍保留一次显示同步；开机后 `settings.sh` 做逻辑 DPI 和首次应用/媒体初始化。

转换器缺失、配置不可读或转换失败时会留下日志，并继续启动合成服务，避免因为显示配置处理失败直接挡住开机。

720×1280 / 320 和 1080×2160 / 403 两个方向都测过。修改 AE 参数后重启实例生效；不是热切换，也没说所有组合都测过。

代码审查曾发现短 init 模板会丢掉原来的 `onrestart`、`writepid` 和属性触发器。当前 payload 保留这些配置，两份定义内容一致。
