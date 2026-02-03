# Adhan Clock (Raspberry Pi) – Agent Notes

## What this repo does
Schedules and plays daily Adhan (call to prayer) audio on a Raspberry Pi. A Python script calculates prayer times (or reads them from Mawaqit), then writes cron jobs that play MP3 files at those times via `mpg123`. Optional hook scripts can run before/after audio.

## Key entrypoints
- `updateAzaanTimers.py`: main scheduler. Calculates/loads prayer times, writes cron jobs for the `pi` user, and saves settings.
- `playAzaan.sh`: plays the audio with `mpg123`, applies volume, runs before/after hooks.
- `mawaqit_util.py`: helper to generate `mawaqit.json` from the Mawaqit API.

## How it works (runtime flow)
1. `updateAzaanTimers.py` loads `.settings` (if present), merges CLI args, and saves updated settings.
2. It either:
   - Calculates times using `praytimes.py`, or
   - Reads times from a Mawaqit JSON file (calendar for the current date).
3. It removes existing cron jobs tagged with `rpiAdhanClockJob`.
4. It creates new cron jobs for 5 prayers plus:
   - Daily re-run of `updateAzaanTimers.py` at 03:15.
   - Monthly log truncation at 00:00 on day 1.
5. It writes to the `pi` user crontab.

## Dependencies
- System: `mpg123` for audio playback.
- Python: `python3`.
- Optional: `mawaqit` Python package (only if using Mawaqit mode).
- Cron library: bundled under `crontab/` (used by `updateAzaanTimers.py`).

## Configuration & files
- `.settings`: saved settings (lat, lng, method, volumes, audio files, mawaqit file).
- `adhan.log`: log file for job output (appended by cron commands).
- `before-hooks.d/` and `after-hooks.d/`: optional executable hook scripts run before/after audio.
- Audio files: `Adhan-*.mp3` in repo root; can also pass custom absolute paths.

## Common commands
First-time (calculated times):
```bash
/home/pi/adhan/updateAzaanTimers.py --lat <LAT> --lng <LNG> --method <METHOD>
```

Mawaqit JSON generation:
```bash
python /home/pi/adhan/mawaqit_util.py -u <email> -p <password> nearby --lat <LAT> --lng <LNG>
python /home/pi/adhan/mawaqit_util.py -u <email> -p <password> search "<mosque name>"
python /home/pi/adhan/mawaqit_util.py -u <email> -p <password> generate <UUID> -o /home/pi/adhan/mawaqit.json
```

Run with Mawaqit times:
```bash
/home/pi/adhan/updateAzaanTimers.py --mawaqit /home/pi/adhan/mawaqit.json
```

Subsequent runs (uses `.settings`):
```bash
/home/pi/adhan/updateAzaanTimers.py
```

## Volumes and audio
- `--fajr-azaan-volume` and `--azaan-volume` are percent (0–100).
- `--fajr-audio` and `--azaan-audio` can be relative to repo or absolute paths.
- `playAzaan.sh` converts percent to mpg123 gain (0–32767).

## Operational notes / gotchas
- Cron is written for user `pi` (`CronTab(user='pi')`). On non-Pi systems, adjust this in `updateAzaanTimers.py`.
- If no `.settings` file exists and no CLI args are provided, `updateAzaanTimers.py` exits with usage.
- The README mentions a 1am update; the current script schedules the update at **03:15**. The script is authoritative.

## File map (quick reference)
- `updateAzaanTimers.py`: scheduling logic, settings, cron jobs.
- `playAzaan.sh`: audio playback + hooks.
- `praytimes.py`: prayer time calculations.
- `mawaqit_util.py`: Mawaqit JSON generation helper.
- `crontab/`: bundled python-crontab library.
- `before-hooks.d/`, `after-hooks.d/`: optional scripts.
