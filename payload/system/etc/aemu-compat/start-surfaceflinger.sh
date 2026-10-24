#!/system/bin/sh
# Read the AE framebuffer profile before MIUI SurfaceFlinger allocates its target.
export PATH=/system/bin:/system/xbin
BASE=/system/etc/aemu-compat
/system/bin/sh "$BASE/display-profile.sh" || echo 'Early display sync failed; continuing compositor startup.'
# Use the already verified driver consistently, before SF maps it.
SRC=$BASE/lib/libGLES_aemu.upload-sync.so
DST=/vendor/lib64/egl/libGLES_aemu.so
if test -f "$SRC"; then
    cp "$SRC" "$DST.display-new" && chmod 0755 "$DST.display-new" && mv -f "$DST.display-new" "$DST"
fi
# Preserve the existing guest-only ION placeholder behavior.
if ! test -e /dev/ion; then ln -s /dev/null /dev/ion; fi
mkdir -p /data/local/tmp/ae-hyos
printf 'surfaceflinger exec: AE=' >> /data/local/tmp/ae-hyos/display-profile.log
cat /dhd.fbgeom >> /data/local/tmp/ae-hyos/display-profile.log
exec /system/bin/surfaceflinger "$@"
