# 这个包是怎么打出来的

基线：**AE 0.0.0.3**。工具整理自实际使用过的 R3 构建脚本，原始路径改为命令行参数。

## 输入与限制

- Python 3.11+；Linux 环境中的 `debugfs`、`resize2fs`、`e2fsck` 和 `bash`。
- 精确匹配 `manifests/r2-base.json` 的 R2 导入 ZIP。旧 R2 本地包已清理，本仓库不提供从原厂 ROM 重建它的全部源码。
- 原签名浏览器 `20.30.1021023` 的 APK，哈希须匹配应用修复说明。
- 足够容纳原镜像、合并镜像和高压 ZIP 的磁盘空间；工作目录必须为空且路径不带空白。

工具会检查输入并在单独工作目录处理镜像，不连接 ADB、不修改手机或运行中的 AE。

```sh
python3 tools/build_package.py \
  --base-zip /path/to/R2.zip \
  --browser-apk /path/to/MIUIBrowser.apk \
  --work-dir /path/to/empty-r3-build \
  --output-dir /path/to/output
```

流程：比对 R2 镜像清单 → 流式提取与哈希 → 对系统镜像合入 payload → 回读校验写入文件 → 必要时扩容 → `e2fsck -fn` → ZIP level 9 / ZIP64 → 全成员解压哈希/CRC。

公开工具经过语法和独立校验工具测试，**未在本次整理中重建 4.39 GB 包体**，因为旧基包与浏览器输入已不在保留工作区。参数化后生成包的 ZIP 时间戳和记录文本可能不同，不承诺与历史 ZIP 字节一致。

## 独立验证历史 ZIP

```sh
python3 tools/verify_archive.py /path/to/HyperOS4-AE0.0.0.3.zip \
  --receipt manifests/archive.json
```

它检查归档整体大小/SHA-256、成员集合、重复路径、不安全路径、各成员大小及 SHA-256，并通过完整解压触发 ZIP CRC 校验。

## 本地测试

```sh
python3 -m unittest discover -s tests -v
bash -n payload/system/etc/aemu-compat/settings.sh
bash -n payload/system/etc/aemu-compat/start-spawner.sh
```

测试仅创建临时小 ZIP，验证正确归档可通过，损坏/缺失/多余成员与非法路径会被拒绝。它们不等价于 AE 中的启动验证。
