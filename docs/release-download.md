# 下载和合并

当前包约 **4.48 GB / 4.17 GiB**，分成 3 个普通二进制分卷，不是 7-Zip 分卷压缩。

从同一个 Release 下载：

- `HyperOS4-AE0.0.0.3-f55fceb6.zip.part001`
- `HyperOS4-AE0.0.0.3-f55fceb6.zip.part002`
- `HyperOS4-AE0.0.0.3-f55fceb6.zip.part003`
- `parts.json`
- Windows 用 `join_release.ps1`，其他环境可用 `join_release.py`

文件名中 `f55fceb6` 是当前完整 ZIP 哈希的前 8 位，只是为了避免拿错新旧分卷，不是另一个版本号。合并后仍叫 `HyperOS4-AE0.0.0.3.zip`。

## Windows

把这些文件放在同一目录，打开 PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\join_release.ps1
```

这条执行策略只影响本次进程，不修改系统持久策略；不用装 Python。

## Python

```sh
python3 join_release.py
```

也可以运行仓库里的脚本，指定下载目录中的清单：

```sh
python3 tools/join_release.py /path/to/downloads/parts.json
```

合并工具会核对每卷及完整 ZIP 的大小/SHA-256。已有同名输出时不会覆盖；如果手里已有旧包，请先自己换个名字保存，别把新旧分卷混在一起。请预留约 4.5 GB 额外空间。

合并后在 **AE 0.0.0.3** 导入。推荐 1080×2160 / 403 DPI；其他显示设置与开机步骤见 [导入说明](import-guide.md)。
