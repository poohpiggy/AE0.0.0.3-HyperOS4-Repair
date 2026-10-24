#!/system/bin/sh
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
set -e
settings put global device_provisioned 1
settings put secure user_setup_complete 1
settings put global disable_window_blurs 0
settings put system background_blur_enable 1
settings put secure background_blur_enable 1
settings put secure material_style 1
settings put secure material_style_selected 1
settings put global window_animation_scale 0
settings put global transition_animation_scale 0
settings put global animator_duration_scale 1
settings put system ringtone file:///system/media/audio/ringtones/MiRemix.ogg
settings put system ringtone_sound_slot_1 file:///system/media/audio/ringtones/MiRemix.ogg
settings put system ringtone_sound_slot_2 file:///system/media/audio/ringtones/MiRemix.ogg
echo 'Integrated defaults applied successfully.' 
touch "$DST/configured-integrated-v2"

fi
# Android logical DPI and native MIUI auto-density must agree.
ae_dpi=$(getprop qemu.sf.lcd_density)
case "$ae_dpi" in ''|*[!0-9]*) exit 1 ;; esac
wm density "$ae_dpi" || echo 'Density setup failed; retry next boot.'
# These original ROM APKs were skipped when their shared-library entries were absent.
# Do not replace installed versions or clear application data/consent.
for ae_pair in \
  com.miui.weather2:/product/data-app/MIUIWeather/MIUIWeather.apk \
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
    # sys.boot_completed can precede MediaProvider publication on a clean import.
    # Probe the actual user-0 provider instead of assuming that boot means ready.
    ae_media_attempt=0
    while :; do
        ae_probe=$(content query --uri content://media/internal/audio/media --projection _id 2>&1) || ae_probe="Error: $ae_probe"
        case "$ae_probe" in
            *Error*|*Exception*|*'Could not find provider'*|'') ;;
            *'Row:'*|*'No result found.'*) break ;;
        esac
        ae_media_attempt=$((ae_media_attempt + 1))
        if test "$ae_media_attempt" -ge 150; then
            echo "MediaProvider not ready; audio indexing will retry next boot."
            exit 0
        fi
        sleep 2
    done
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
