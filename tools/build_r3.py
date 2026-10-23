from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, time, zipfile

# Configured by CLI; all image mutation is confined to an empty work directory.
ROOT = Path(__file__).resolve().parents[1]
W = OUT = BASE = I = P = None
NAME = 'HyperOS4-AE-MIX2S-R3-1080p403-Apps-Ringtone.zip'
CHUNK = 4*1024*1024
REPORT = {'revision':3, 'scope':'AE guest only', 'changes':[], 'images':{}}

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def log(*args): print(*args, flush=True)

def dbg(cmd, write=False):
    r = subprocess.run(['debugfs']+(['-w'] if write else [])+['-R',cmd,str(I/'system.img')],capture_output=True,text=True)
    if r.returncode or any(s in r.stderr for s in ['File not found','Could not allocate','No free space','short write','Usage:','Bad value']):
        raise RuntimeError(cmd+'\n'+r.stdout+r.stderr)
    return r.stdout

def exists(path):
    r = subprocess.run(['debugfs','-R','stat '+path,str(I/'system.img')],capture_output=True,text=True)
    return 'Inode:' in r.stdout and 'File not found' not in r.stderr

def mkdir(path):
    if path in ('/','.') or exists(path): return
    mkdir(str(Path(path).parent)); dbg('mkdir '+path,True)
    dbg('set_inode_field '+path+' mode 040755',True)

def install(path, source, mode=0o644):
    mkdir(str(Path(path).parent))
    if exists(path): dbg('rm '+path,True)
    result=dbg(f'write {source} {path}',True)
    assert 'Allocated inode' in result, result
    for k,v in [('mode','0'+format(0o100000|mode,'o')),('uid','0'),('gid','0')]:
        dbg(f'set_inode_field {path} {k} {v}',True)
    readback=W/'readback.bin'; readback.unlink(missing_ok=True)
    dbg(f'dump {path} {readback}')
    assert sha(readback)==sha(source),path
    readback.unlink()
    REPORT['changes'].append({'path':path,'sha256':sha(source),'size':Path(source).stat().st_size,'mode':oct(mode)})

def prepare_settings():
    target=P/'system/etc/aemu-compat/settings.sh'
    baseline=W/'settings.original.sh'
    if not baseline.exists(): shutil.copyfile(ROOT/'tools/settings.original.sh',baseline)
    old=baseline.read_text()
    tail=old[old.index('set -e\n'):]
    prefix='''#!/system/bin/sh
# AE guest provisioning: preserve user settings after the initial defaults.
export PATH=/system/bin:/system/xbin
DST=/data/local/tmp/ae-hyos
mkdir -p "$DST"
exec >> "$DST/first-boot.log" 2>&1
attempt=0
while test "$(getprop sys.boot_completed)" != 1; do
    sleep 2
    attempt=$((attempt + 1))
    test "$attempt" -lt 300 || exit 1
done
if ! test -f "$DST/configured-integrated-v2"; then
'''
    provision='''
fi
# Android logical DPI and native MIUI auto-density must agree.
ae_dpi=$(getprop qemu.sf.lcd_density)
case "$ae_dpi" in ''|*[!0-9]*) exit 1 ;; esac
wm density "$ae_dpi" || echo 'Density setup failed; retry next boot.'
# These original ROM APKs were skipped when their shared-library entries were absent.
# Do not replace installed versions or clear application data/consent.
for ae_pair in \\
  com.miui.weather2:/product/data-app/MIUIWeather/MIUIWeather.apk \\
  com.miui.themestore:/product/data-app/MIUIThemeStore/MIUIThemeStore.apk; do
    ae_pkg=${ae_pair%%:*}
    ae_apk=${ae_pair#*:}
    ae_installed=$(pm path "$ae_pkg" 2>/dev/null)
    case "$ae_installed" in
      package:*) ;;
      *) test ! -f "$ae_apk" || pm install -r "$ae_apk" || echo "Preinstall failed: $ae_pkg" ;;
    esac
done
# Index built-in audio through MediaProvider; never copy another VM's database.
if ! test -f "$DST/builtin-audio-indexed-r3"; then
    ae_scan_ok=1
    ae_scan_count=0
    for ae_dir in /product/media/audio/ringtones /product/media/audio/notifications /product/media/audio/alarms; do
        for ae_file in "$ae_dir"/*; do
            test -f "$ae_file" || continue
            ae_result=$(content call --uri content://media --method scan_file --arg "$ae_file" --extra android.intent.extra.originated_from_shell:b:true 2>&1) || ae_scan_ok=0
            case "$ae_result" in
              *'Result: Bundle['*) ae_scan_count=$((ae_scan_count + 1)) ;;
              *) ae_scan_ok=0; echo "Audio indexing failed: $ae_file: $ae_result" ;;
            esac
        done
    done
    if test "$ae_scan_ok" = 1 && test "$ae_scan_count" -gt 0; then
        echo "Indexed $ae_scan_count built-in audio files."
        touch "$DST/builtin-audio-indexed-r3"
    fi
fi
'''
    target.write_text(prefix+tail+provision)
    for f in [target,P/'system/etc/aemu-compat/start-spawner.sh']:
        subprocess.run(['bash','-n',str(f)],check=True)

def extract():
    with zipfile.ZipFile(BASE) as z:
        manifest=json.loads(z.read('AE-INTEGRATED.json'))
        expected_base=json.loads((ROOT/'manifests/r2-base.json').read_text())
        for name in ['system.img','vendor.img','boot.img']:
            assert manifest['images'][name] == expected_base['images'][name], 'Unsupported R2 base: '+name
        (W/'base-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        for name in ['system.img','vendor.img','boot.img']:
            dst=I/name
            h=hashlib.sha256(); count=0; tick=time.time()
            with z.open(name) as src,dst.open('wb') as out:
                while b:=src.read(CHUNK):
                    h.update(b);out.write(b);count+=len(b)
                    if time.time()-tick>25:log('EXTRACT',name,count);tick=time.time()
            expected=manifest.get('images',{}).get(name,{})
            if expected.get('sha256'): assert h.hexdigest()==expected['sha256'],name
            assert count==z.getinfo(name).file_size
            log('BASE_VERIFIED',name,count,h.hexdigest())

def merge():
    assert sha(P/'product/app/MIUIBrowserOfficial/MIUIBrowser.apk')=='1f5e546a133a4b6530dd183e711648a6de0d0e4c78049b646c2e52bf4035d75a'
    for path in ['/system_ext/framework/hyperos.rustruntime.jar','/mi_ext/product/framework/miui-uninstall-empty.jar']:
        assert exists(path),path
    stats=dbg('stats')
    free=int(re.search(r'Free blocks:\s+(\d+)',stats)[1])*int(re.search(r'Block size:\s+(\d+)',stats)[1])
    if free<350*1024*1024:
        log('GROW_SYSTEM',free)
        with (I/'system.img').open('ab') as f:f.truncate((I/'system.img').stat().st_size+512*1024*1024)
        subprocess.run(['resize2fs',str(I/'system.img')],check=True)
    old='/product/priv-app/MIUIBrowser/MIUIBrowser.apk'
    assert exists(old)
    old_apk=W/'browser-original.apk';dbg(f'dump {old} {old_apk}')
    assert sha(old_apk)=='8c097aeb2f7d9232cd9dc5c974fdf8054978482fa86a34a5e7d2afe5b9844a23'
    install('/system/etc/aemu-compat/backups/MIUIBrowser.original.apk',old_apk)
    dbg('rm '+old,True)
    if exists(old+'.fsv_meta'):dbg('rm '+old+'.fsv_meta',True)
    REPORT['changes'].append({'path':old,'removed_from_scan':True,'backup':'/system/etc/aemu-compat/backups/MIUIBrowser.original.apk'})
    for p in sorted(P.rglob('*')):
        if p.is_file():
            rel='/'+p.relative_to(P).as_posix()
            log('MERGE',rel)
            install(rel,p,0o755 if p.suffix=='.sh' else 0o644)
    prop=W/'system.build.prop';dbg(f'dump /system/build.prop {prop}')
    changes={'ro.sf.lcd_density':'403','persist.miui.density_v2':'403','persist.sys.miui_resolution':'1080,2160,403','persist.sys.miui_default_resolution':'1080x2160'}
    lines=[];seen=set()
    for line in prop.read_text().splitlines():
        key=line.split('=',1)[0].strip()
        if key in changes and not line.lstrip().startswith('#'):
            line=key+'='+changes[key];seen.add(key)
        lines.append(line)
    lines += ['# AE R3 display defaults']+[k+'='+v for k,v in changes.items() if k not in seen]
    prop.write_text('\n'.join(lines)+'\n');install('/system/build.prop',prop)
    REPORT['display']={'resolution':[1080,2160],'logical_dpi':403,'ae_instance_settings':'Set 1080x2160 / 403 in AE before first boot; importer may choose its own preset.'}
    for name in ['system.img','vendor.img']:
        log('FSCK',name)
        with (W/(name+'.fsck.log')).open('w') as f:r=subprocess.run(['e2fsck','-fn',str(I/name)],stdout=f,stderr=subprocess.STDOUT)
        assert r.returncode==0,(name,r.returncode)
    REPORT['filesystem_checks']='system/vendor: e2fsck -fn exit 0'

def package():
    for name in ['system.img','vendor.img','boot.img']:
        log('HASH',name);REPORT['images'][name]={'size':(I/name).stat().st_size,'sha256':sha(I/name)}
    REPORT['validation']='Individual fixes verified on existing guest; archive filesystem and every decompressed ZIP member verified. This new archive has not been fresh-import boot tested.'
    REPORT['privacy']='No VM user-data database, account, download history, media, or private app state included.'
    report=W/'AE-INTEGRATED.json';report.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
    readme=W/'使用说明.md'
    readme.write_text('''# HyperOS 4 · MIX2S · AE R3

仅用于 AEmulator 虚拟机导入，不用于实体手机刷机。

1. 在 AE 新建实例并直接选择本 ZIP 导入。
2. **第一次启动前，在该实例的 AE 设置中填写：宽 1080、高 2160、DPI 403。** AE 导入器可能仍自行选择 540×960/240；包内 JSON 不会替代 AE 的实例设置。
3. 首次启动自动设置逻辑密度、登记内置音频并补装天气/主题商店；请等待约 2–3 分钟。应用协议和权限由你自行决定。
4. 首次初始化完成后，从 AE 菜单正常重启一次实例，使全部原生界面从一致密度初始化。后续启动保留铃声与用户设置。

403 是此实例采用的逻辑 DPI，不宣称是 MIX2S 出厂逻辑 DPI；实体 MIX2S 的 5.99 英寸、1080×2160 对应约 403 PPI。

本次合入：系统内置铃声/通知/闹钟的 MediaStore 索引建立；已验证的原生界面密度修正；hyperos.rustruntime.v3/v5 与 miui-uninstall-empty.jar 的真实库注册；将签名冲突的旧浏览器预置包移出扫描位置，改为商店下载的原签名小米浏览器 20.30.1021023，保留正常签名校验。旧浏览器 APK 在 /system/etc/aemu-compat/backups/MIUIBrowser.original.apk。

原 R2 的 GLES、音频、模拟电话/短信、WebView 等兼容修复保留。本次未加入任何临时绘图代理、探针或试验性图标资源。时钟/日历静态预览及未解决的液态玻璃/动态图标问题不宣称已修复。

不携带旧实例用户数据、账号、浏览记录或铃声数据库；音频索引在新实例内正规建立。此 ZIP 已进行文件系统与完整成员 SHA-256/CRC 校验；当前实例中的单项修复经过验证，但该新 ZIP 尚未做全新导入启动测试。
''')
    entries=[(n,I/n) for n in ['boot.img','system.img','vendor.img']]+[('AE-INTEGRATED.json',report),('使用说明.md',readme)]
    expected={n:{'size':p.stat().st_size,'sha256':sha(p)} for n,p in entries}
    part=OUT/(NAME+'.partial'); dest=OUT/NAME
    with zipfile.ZipFile(part,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        for name,path in entries:
            log('ZIP9',name)
            count=0;tick=time.time()
            with path.open('rb') as src,z.open(name,'w',force_zip64=path.stat().st_size>=zipfile.ZIP64_LIMIT) as out:
                while b:=src.read(CHUNK):
                    out.write(b);count+=len(b)
                    if time.time()-tick>25:log('COMPRESS_PROGRESS',name,count,path.stat().st_size);tick=time.time()
    with zipfile.ZipFile(part) as z:
        assert z.namelist()==[n for n,p in entries]
        for info in z.infolist():
            log('VERIFY_ZIP',info.filename,info.compress_size,info.file_size)
            with z.open(info) as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
            assert digest==expected[info.filename]['sha256']
            assert info.file_size==expected[info.filename]['size']
            assert info.compress_type==zipfile.ZIP_DEFLATED
    digest=sha(part);part.replace(dest)
    receipt={'archive':dest.name,'size':dest.stat().st_size,'sha256':digest,'compression':'ZIP Deflate level 9, ZIP64','members':expected,'filesystem_checks':REPORT['filesystem_checks'],'fresh_import_boot_tested':False}
    (OUT/(NAME+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    (OUT/(NAME+'.sha256')).write_text(digest+'  '+NAME+'\n')
    shutil.copyfile(readme,OUT/'AE-R3使用说明.md')
    log('READY',json.dumps(receipt,ensure_ascii=False))

def main():
    import argparse
    global W, OUT, BASE, I, P
    ap=argparse.ArgumentParser(description="Merge the recorded R3 payload into the exact R2 base (AE 0.0.0.3).")
    ap.add_argument('--base-zip',type=Path,required=True)
    ap.add_argument('--browser-apk',type=Path,required=True)
    ap.add_argument('--work-dir',type=Path,required=True,help='New or empty work directory, without whitespace')
    ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args()
    BASE=args.base_zip.resolve(); W=args.work_dir.resolve(); OUT=args.output_dir.resolve()
    if any(c.isspace() for c in str(W)):
        ap.error('Work directory must not contain whitespace (debugfs command format).')
    for tool in ['debugfs','resize2fs','e2fsck','bash']:
        if not shutil.which(tool): ap.error('Missing external tool: '+tool)
    if not BASE.is_file() or not args.browser_apk.is_file(): ap.error('Base ZIP and browser APK must exist.')
    if sha(args.browser_apk) != '1f5e546a133a4b6530dd183e711648a6de0d0e4c78049b646c2e52bf4035d75a':
        ap.error('Browser APK does not match the recorded R3 input.')
    if W.exists() and any(W.iterdir()): ap.error('Work directory must be empty; no existing images are overwritten.')
    if (OUT/NAME).exists() or (OUT/(NAME+'.partial')).exists(): ap.error('Output archive already exists.')
    # Reject unsupported bases before extracting or modifying images.
    with zipfile.ZipFile(BASE) as z:
        actual=json.loads(z.read('AE-INTEGRATED.json'))
        expected=json.loads((ROOT/'manifests/r2-base.json').read_text())
        for name in ['system.img','vendor.img','boot.img']:
            if actual.get('images',{}).get(name) != expected['images'][name]: ap.error('Unsupported R2 base: '+name)
    W.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    I=W/'images'; I.mkdir(); P=W/'payload'
    shutil.copytree(ROOT/'payload',P)
    browser=P/'product/app/MIUIBrowserOfficial/MIUIBrowser.apk'
    browser.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(args.browser_apk,browser)
    prepare_settings(); extract(); merge(); package()

if __name__=='__main__':
    main()
