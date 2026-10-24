#!/system/bin/sh
# Early-boot display profile sync; invoke from start-spawner before native UI.
export PATH=/system/bin:/system/xbin

DST=/data/local/tmp/ae-hyos
LOG=$DST/display-profile.log
XML=/data/system/display_settings.xml
TMP_XML=/data/system/.display_settings.xml.ae-new
TMP_ABX=/data/system/.display_settings.xml.ae-abx
mkdir -p "$DST" 2>/dev/null
exec >> "$LOG" 2>&1

log() { echo "$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null) $*"; }
fail() { log "display profile: $*; continuing without XML update"; }
cleanup() { rm -f "$TMP_XML" "$TMP_ABX"; }

read -r ae_w ae_h ae_unused < /dhd.fbgeom
ae_dpi=$(getprop qemu.sf.lcd_density)
case "$ae_w:$ae_h:$ae_dpi" in
    *[!0-9:]*|:*|*::*|*:) log 'invalid framebuffer geometry or qemu.sf.lcd_density'; exit 1 ;;
esac
if test "$ae_w" -le 0 || test "$ae_h" -le 0 || test "$ae_dpi" -le 0; then
    log "nonpositive AE display profile"
    exit 1
fi

setprop persist.sys.miui_resolution "$ae_w,$ae_h,$ae_dpi"
setprop persist.sys.miui_default_resolution "${ae_w}x${ae_h}"
setprop persist.miui.density_v2 "$ae_dpi"
# Match the native MIUI auto-density base, without overwriting existing values.
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

cleanup
if ! test -x /system/bin/abx2xml || ! test -x /system/bin/xml2abx; then
    fail 'ABX converters unavailable'
    exit 0
fi

if test -e "$XML"; then
    ae_mode=$(stat -c '%a' "$XML" 2>/dev/null) || ae_mode=
    ae_owner=$(stat -c '%u:%g' "$XML" 2>/dev/null) || ae_owner=
    if test -z "$ae_mode" || test -z "$ae_owner"; then
        fail 'cannot read original file mode/owner'
        exit 0
    fi
    if ! /system/bin/abx2xml "$XML" "$TMP_XML"; then
        fail 'abx2xml failed'
        cleanup
        exit 0
    fi
else
    ae_mode=600
    ae_owner=1000:1000
    cat > "$TMP_XML" <<'XML'
<?xml version="1.0" encoding="utf-8" standalone="yes" ?>
<display-settings>
<config identifier="0" />
<display name="local:0" />
</display-settings>
XML
fi

# abx2xml emits each display start tag on one line; do not rewrite other displays.
if ! awk -v dpi="$ae_dpi" '
{
    if ($0 ~ /<display[[:space:]]/ && $0 ~ /name="local:0"/) {
        gsub(/[[:space:]]forced(Width|Height|Density)="[^"]*"/, "")
        if ($0 ~ /\/>/) sub(/[[:space:]]*\/>/, " forcedDensity=\"" dpi "\" />")
        else sub(/>/, " forcedDensity=\"" dpi "\">")
        found=1
    }
    if ($0 ~ /<\/display-settings>/ && !found) {
        sub(/<\/display-settings>/, "<display name=\"local:0\" forcedDensity=\"" dpi "\" />\n</display-settings>")
        found=1
    }
    print
}
END { if (!found) exit 2 }
' "$TMP_XML" > "$TMP_XML.rewritten"; then
    fail 'XML rewrite failed'
    rm -f "$TMP_XML.rewritten"
    cleanup
    exit 0
fi
mv -f "$TMP_XML.rewritten" "$TMP_XML" || { fail 'cannot stage rewritten XML'; cleanup; exit 0; }

if ! /system/bin/xml2abx "$TMP_XML" "$TMP_ABX"; then
    fail 'xml2abx failed'
    cleanup
    exit 0
fi
chmod "$ae_mode" "$TMP_ABX" || { fail 'chmod failed'; cleanup; exit 0; }
chown "$ae_owner" "$TMP_ABX" || { fail 'chown failed'; cleanup; exit 0; }
if ! mv -f "$TMP_ABX" "$XML"; then
    fail 'atomic replacement failed'
    cleanup
    exit 0
fi
rm -f "$TMP_XML"
log "synced local:0 forcedDensity=$ae_dpi for ${ae_w}x${ae_h}"
exit 0
