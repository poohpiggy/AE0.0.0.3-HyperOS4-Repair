"""Offline checks for early-display rewriting and MediaProvider readiness."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DisplayRewrite(unittest.TestCase):
    def awk_program(self):
        text = (ROOT / 'payload/system/etc/aemu-compat/display-profile.sh').read_text()
        match = re.search(r"if ! awk -v dpi=\"\$ae_dpi\" '(.*?)' \"\$TMP_XML\"", text, re.S)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_local_display_only_and_no_stale_dimensions(self):
        source = '<display-settings>\n<display name="local:0" forcedWidth="720" forcedHeight="1280" forcedDensity="240" />\n<display name="external:1" forcedWidth="1920" forcedDensity="160" />\n</display-settings>\n'
        result = subprocess.run(['awk', '-v', 'dpi=403', self.awk_program()], input=source, text=True, capture_output=True, check=True).stdout
        local = next(line for line in result.splitlines() if 'local:0' in line)
        self.assertIn('forcedDensity="403"', local)
        self.assertNotIn('forcedWidth', local)
        self.assertNotIn('forcedHeight', local)
        self.assertIn('<display name="external:1" forcedWidth="1920" forcedDensity="160" />', result)

    def test_missing_local_display_is_added(self):
        source = '<display-settings>\n<config identifier="0" />\n</display-settings>\n'
        result = subprocess.run(['awk', '-v', 'dpi=320', self.awk_program()], input=source, text=True, capture_output=True, check=True).stdout
        self.assertIn('<display name="local:0" forcedDensity="320" />', result)

    def test_missing_display_document_fails(self):
        result = subprocess.run(['awk', '-v', 'dpi=320', self.awk_program()], input='broken document\n', text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)


class MediaReadiness(unittest.TestCase):
    def run_fake_guest(self, never_ready=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        binaries, state, audio = root / 'bin', root / 'state', root / 'audio'
        for d in [binaries, state, audio]: d.mkdir()
        (state / 'configured-integrated-v2').touch()
        for folder in ['ringtones', 'notifications', 'alarms']:
            (audio / folder).mkdir()
            (audio / folder / 'test.ogg').write_bytes(b'fake audio')
        stubs = {
            'getprop': 'if [ "$1" = sys.boot_completed ]; then echo 1; else echo 403; fi',
            'wm': 'echo "density:$*" >> "$TEST_STATE/events"',
            'pm': 'echo package:/existing.apk',
            'sleep': 'exit 0',
            'content': '''if [ "$1" = query ]; then
 count=0; test ! -f "$TEST_STATE/queries" || count=$(cat "$TEST_STATE/queries")
 count=$((count+1)); echo "$count" > "$TEST_STATE/queries"
 echo "query:$count" >> "$TEST_STATE/events"
 if [ "$NEVER_READY" = 1 ] || [ "$count" -eq 1 ]; then echo 'Error: Could not find provider'; exit 1; fi
 echo 'No result found.'
else
 echo scan >> "$TEST_STATE/events"
 echo 'Result: Bundle[test]'
fi''',
        }
        for name, body in stubs.items():
            path = binaries / name
            path.write_text('#!/bin/sh\n' + body + '\n'); path.chmod(0o755)
        text = (ROOT / 'payload/system/etc/aemu-compat/settings.sh').read_text()
        text = text.replace('export PATH=/system/bin:/system/xbin', 'export PATH="$TEST_BIN:/usr/bin:/bin"')
        text = text.replace('DST=/data/local/tmp/ae-hyos', 'DST="$TEST_STATE"')
        text = text.replace('/product/media/audio', str(audio))
        script = root / 'settings.sh'; script.write_text(text)
        env = os.environ.copy()
        env.update(TEST_BIN=str(binaries), TEST_STATE=str(state), NEVER_READY='1' if never_ready else '0')
        result = subprocess.run(['bash', str(script)], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return state

    def test_waits_for_provider_before_scanning(self):
        state = self.run_fake_guest()
        events = (state / 'events').read_text().splitlines()
        self.assertEqual(events.count('scan'), 3)
        self.assertLess(events.index('query:2'), events.index('scan'))
        self.assertTrue((state / 'builtin-audio-indexed-r3').exists())
        self.assertIn('Indexed 3 built-in audio files.', (state / 'first-boot.log').read_text())

    def test_timeout_does_not_mark_or_scan(self):
        state = self.run_fake_guest(never_ready=True)
        self.assertFalse((state / 'builtin-audio-indexed-r3').exists())
        self.assertNotIn('scan', (state / 'events').read_text().splitlines())
        self.assertIn('will retry next boot', (state / 'first-boot.log').read_text())


if __name__ == '__main__':
    unittest.main()
