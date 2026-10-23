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
# Synchronize MIUI panel metadata with this instance before starting native UI.
read -r ae_w ae_h ae_unused < /dhd.fbgeom
ae_dpi=$(getprop qemu.sf.lcd_density)
case "$ae_w:$ae_h:$ae_dpi" in
    *[!0-9:]*|:*|*::*|*:) exit 1 ;;
esac
setprop persist.sys.miui_resolution "$ae_w,$ae_h,$ae_dpi"
setprop persist.sys.miui_default_resolution "${ae_w}x${ae_h}"
setprop persist.miui.density_v2 "$ae_dpi"
# Correct only the native MIUI auto-density base; Android density is separately configured.
    ae_numerator=$((ae_dpi * 1000000))
    ae_native_scale="$((ae_numerator / 182383423))."
    ae_remainder=$((ae_numerator % 182383423))
    ae_digit_index=0
    while test "$ae_digit_index" -lt 6; do
        ae_remainder=$((ae_remainder * 10))
        ae_native_scale="${ae_native_scale}$((ae_remainder / 182383423))"
        ae_remainder=$((ae_remainder % 182383423))
        ae_digit_index=$((ae_digit_index + 1))
    done
    for ae_scale_prop in ro.miui.density.primaryscale ro.miui.density.secondaryscale; do
        if test -z "$(getprop "$ae_scale_prop")"; then
            setprop "$ae_scale_prop" "$ae_native_scale"
        fi
    done
setprop persist.sys.rust_runtime_active 1
setprop rust.runtime_active 1
echo $$ > "$DST/spawner.pid"
exec "$DST/hyos_spawner.gles" /system_ext/bin --spawner --start-spawner-server >> "$DST/runtime.log" 2>&1
