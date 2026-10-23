#!/system/bin/sh
# Provision defaults once per new guest; subsequent boots preserve user settings.
export PATH=/system/bin:/system/xbin
DST=/data/local/tmp/ae-hyos
mkdir -p "$DST"
exec >> "$DST/first-boot.log" 2>&1
test -f "$DST/configured-integrated-v2" && exit 0
attempt=0
while test "$(getprop sys.boot_completed)" != 1; do
    sleep 2
    attempt=$((attempt + 1))
    test "$attempt" -lt 300 || exit 1
done
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
