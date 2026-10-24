# 这个包怎么继续合并

发布的 ZIP 是另一段修复对话里已经完成导入验收的原文件。这次只整理上传，没有重新跑一次镜像构建，也没有连手机。

`tools/build_package.py` 是按实际合包步骤整理的参数版：从上一份已公开的包继续合入这一轮 payload、资源 overlay 和静态主题，再从原签名浏览器里展开 66 个库。它不是从原厂 ROM 开始的一键构建。

需要 Python 3.11+、Linux 的 `debugfs` 和 `e2fsck`，以及上一份 SHA-256 为 `dd01bd45...` 的完整 ZIP。旧输入的精确大小和哈希保留在 `manifests/history/archive-dd01bd45.json`。

```sh
python3 tools/build_package.py \
  --base-zip /path/to/earlier-package.zip \
  --work-dir /path/to/empty-build \
  --output-dir /path/to/output
```

工作目录必须为空且路径不带空白，不覆盖已有输出。工具只处理电脑里的镜像，不连接 ADB。

构建过程会回读比对写入文件、跑 system/vendor 文件系统检查、ZIP64 高压缩，再解压核对所有成员。**参数整理版只做过语法/离线检查，没在这次上传中重新构建整包；重新生成的输出需要单独导入测试，也不保证与发布文件字节一致。**

`tools/history/build_initial_package.py` 保留上一轮工具，当前构建脚本复用它的 debugfs 帮助函数。`tools/MaskIcons.java` 是当时的圆角处理实现；本次没有重画主题图片。

## 核对发布 ZIP

```sh
python3 tools/verify_archive.py /path/to/HyperOS4-AE0.0.0.3.zip --receipt manifests/archive.json
```

会检查整包大小/哈希、成员集合、路径、每个成员的大小/SHA-256，并通过完整解压验证 CRC。

## 离线检查

```sh
python3 -m unittest discover -s tests -v
bash -n payload/system/etc/aemu-compat/display-profile.sh
bash -n payload/system/etc/aemu-compat/settings.sh
```

测试使用临时目录、假媒体服务和小 ZIP，不运行真实客体命令，也不代替手机里的测试。

## 两个小资源补丁

- `overlay/recents/` 是多任务资源 overlay 的源码；已使用构件为 `assets/AEGuestRecents.apk`。签名私钥不上传，重编译/签名需要自行准备 Android 构建工具及本地密钥。
- `assets/icons.static.zip` 只含 transform_config.xml 和三张静态 PNG。图片保留原有权利，见 `NOTICE.md`。不是用户数据或完整主题目录备份。
