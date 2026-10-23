# Release 下载与合并

原 ZIP 为 **4,393,500,616 bytes**，超过 GitHub Release 单附件限制，因此采用普通二进制分卷，**不是 7-Zip 分卷压缩格式**。

从同一 Release 下载所有 `.part001` / `.part002` / `.part003`、`parts.json` 和相应合并脚本到同一目录。分卷不单独导入 AE，也不要改名。

## Windows

无需安装 Python。打开文件所在目录的 PowerShell，运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\join_release.ps1
```

`ExecutionPolicy Bypass` 仅作用于这次进程，不修改系统或用户的持久执行策略。脚本不会下载程序或修改系统配置，只读取分卷并写入合并后的 ZIP。

## Python（Windows / Linux / macOS）

```sh
python3 join_release.py
```

需要 Python 3.8+。也可使用仓库里的版本：

```sh
python3 tools/join_release.py /path/to/downloads/parts.json
```

两种脚本都会校验各卷大小与 SHA-256，再校验最终 ZIP。已有同名 ZIP 或 `.partial` 文件时停止，不覆盖它们。请预留约 4.4 GB 额外空间。

## 导入

只将合并后的完整 ZIP 导入 **AE 0.0.0.3**。首次启动前手动配置 **1080×2160 / 403 DPI**；初始化后重启一次，详见 [导入说明](import-guide.md)。

分卷和合并不会改变原 ZIP 内任何成员；原始 SHA-256 保留于 `manifests/*.sha256`。
