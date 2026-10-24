#!/system/bin/sh
# Recreate only compatibility files, never copy another guest's /data.
set -e
SRC=/system/etc/aemu-compat
DST=/data/local/tmp/ae-hyos
mkdir -p "$DST/lib"
for name in librustutils.dylib.so libhyper_os_flutter.so libGLES_aemu.upload-sync.so; do
    cp "$SRC/lib/$name" "$DST/lib/$name.new"
    chmod 0644 "$DST/lib/$name.new"
    mv -f "$DST/lib/$name.new" "$DST/lib/$name"
done
cp "$SRC/hyos_spawner.gles" "$DST/hyos_spawner.gles.new"
chmod 0755 "$DST/hyos_spawner.gles.new"
mv -f "$DST/hyos_spawner.gles.new" "$DST/hyos_spawner.gles"
# AE reinjects its stock GLES driver at each boot. Replace its inode before Home.
cp "$SRC/lib/libGLES_aemu.upload-sync.so" /vendor/lib64/egl/libGLES_aemu.so.hyos-new
chmod 0755 /vendor/lib64/egl/libGLES_aemu.so.hyos-new
mv -f /vendor/lib64/egl/libGLES_aemu.so.hyos-new /vendor/lib64/egl/libGLES_aemu.so
setprop debug.flutter.renderer impelleropengl
setprop debug.hwui.renderer skiagl
setprop debug.aemu.gl 3
setprop persist.sys.force_ignore_blur false
# Sync persisted Android density before framework/native UI initialization.
/system/bin/sh "$SRC/display-profile.sh" || echo 'Display profile sync failed; using post-boot fallback.'
setprop persist.sys.rust_runtime_active 1
setprop rust.runtime_active 1
echo $$ > "$DST/spawner.pid"
exec "$DST/hyos_spawner.gles" /system_ext/bin --spawner --start-spawner-server >> "$DST/runtime.log" 2>&1
