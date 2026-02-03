#!/usr/bin/env python3

import datetime
import time
import sys
import json
import os
from os.path import dirname, abspath, join as pathjoin
import argparse
import shlex
import getpass

root_dir = dirname(abspath(__file__))
sys.path.insert(0, pathjoin(root_dir, 'crontab'))

from praytimes import PrayTimes
PT = PrayTimes()

from crontab import CronTab
cron_user = getpass.getuser()
system_cron = CronTab(user=cron_user)

# HELPER FUNCTIONS
# ---------------------------------
def parseArgs():
    parser = argparse.ArgumentParser(description='Calculate prayer times and install cronjobs to play Adhan')
    parser.add_argument(
        '--config',
        dest='config_path',
        default=pathjoin(root_dir, 'settings.json'),
        help='Path to JSON config file (default: ./settings.json)',
    )
    return parser

def clamp_percent(v, field_name):
    try:
        v = int(v)
    except (TypeError, ValueError):
        raise ValueError(f'Invalid {field_name} (must be integer 0-100): {v}')
    return max(0, min(100, v))

def resolve_path(p):
    if not p:
        return None
    return p if os.path.isabs(p) else pathjoin(root_dir, p)

def load_config(config_path):
    config_path = resolve_path(config_path)
    if not os.path.exists(config_path):
        print(f'Error: Config file not found: {config_path}')
        sys.exit(1)
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        print('Error: Config must be a JSON object')
        sys.exit(1)
    return data, config_path

def parse_time_hhmm(value, field_name):
    try:
        hour_str, min_str = value.split(':', 1)
        hour = int(hour_str)
        minute = int(min_str)
    except Exception:
        raise ValueError(f'Invalid {field_name} (expected HH:MM): {value}')
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f'Invalid {field_name} (expected HH:MM): {value}')
    return hour, minute

def get_times_from_mawaqit(mawaqit_file):
    """Read prayer times from a mawaqit JSON file for the current date."""
    # Resolve relative paths
    if not mawaqit_file.startswith('/') and not os.path.isabs(mawaqit_file):
        mawaqit_file = pathjoin(root_dir, mawaqit_file)

    # Validate file exists
    if not os.path.exists(mawaqit_file):
        print(f"Error: Mawaqit file not found: {mawaqit_file}")
        sys.exit(1)

    # Load and parse JSON
    with open(mawaqit_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get times for current date
    now = datetime.datetime.now()
    month_idx = now.month - 1  # 0-indexed
    day_key = str(now.day)

    try:
        day_times = data['calendar'][month_idx][day_key]
    except (KeyError, IndexError) as e:
        print(f"Error: Could not find times for {now.month}/{now.day} in mawaqit file: {e}")
        sys.exit(1)

    # [Fajr, Shuruq, Dhuhr, Asr, Maghrib, Isha]
    return {
        'fajr': day_times[0],
        'dhuhr': day_times[2],
        'asr': day_times[3],
        'maghrib': day_times[4],
        'isha': day_times[5]
    }

def addAzaanTime (strPrayerName, strPrayerTime, objCronTab, strCommand):
  job = objCronTab.new(command=strCommand,comment=strPrayerName)
  timeArr = strPrayerTime.split(':')
  hour = timeArr[0]
  min = timeArr[1]
  job.minute.on(int(min))
  job.hour.on(int(hour))
  job.set_comment(strJobComment)
  print(job)
  return

def addUpdateCronJob (objCronTab, strCommand, hour, minute):
  job = objCronTab.new(command=strCommand)
  job.minute.on(minute)
  job.hour.on(hour)
  job.set_comment(strJobComment)
  print(job)
  return

def addClearLogsCronJob (objCronTab, strCommand):
  job = objCronTab.new(command=strCommand)
  job.day.on(1)
  job.minute.on(0)
  job.hour.on(0)
  job.set_comment(strJobComment)
  print(job)
  return
# ---------------------------------
# HELPER FUNCTIONS END

# Parse arguments
parser = parseArgs()
args = parser.parse_args()

config, config_path = load_config(args.config_path)
general = config.get('general', {})
prayers_cfg = config.get('prayers', {})

mode = general.get('mode', 'calculated')
if mode not in ('calculated', 'mawaqit'):
    print('Error: general.mode must be "calculated" or "mawaqit"')
    sys.exit(1)

default_audio = general.get('default_audio', 'Adhan-Madinah.mp3')
default_volume = clamp_percent(general.get('default_volume', 100), 'general.default_volume')
log_file = general.get('log_file', 'adhan.log')
update_time = general.get('update_time', '03:15')

try:
    update_hour, update_minute = parse_time_hhmm(update_time, 'general.update_time')
except ValueError as e:
    print(f'Error: {e}')
    sys.exit(1)

log_file_path = resolve_path(log_file) or pathjoin(root_dir, 'adhan.log')


def get_prayer_config(name):
    cfg = prayers_cfg.get(name, {}) or {}
    enabled = cfg.get('enabled', True)
    audio = cfg.get('audio', default_audio)
    if audio is None:
        audio = default_audio
    volume_value = cfg.get('volume', default_volume)
    if volume_value is None:
        volume_value = default_volume
    volume = clamp_percent(volume_value, f'prayers.{name}.volume')
    return enabled, audio, volume

def build_play_command(audio, volume):
    audio_path = resolve_path(audio) or audio
    if not audio_path:
        print('Error: audio file path is required for prayer playback')
        sys.exit(1)
    return '{} {} {} >> {} 2>&1'.format(
        shlex.quote(pathjoin(root_dir, 'playAzaan.sh')),
        shlex.quote(audio_path),
        shlex.quote(str(volume)),
        shlex.quote(log_file_path),
    )

now = datetime.datetime.now()

# Determine mode and get prayer times
if mode == 'mawaqit':
    mawaqit_file = general.get('mawaqit_file')
    if not mawaqit_file:
        print('Error: general.mawaqit_file is required when mode is "mawaqit"')
        sys.exit(1)
    times = get_times_from_mawaqit(mawaqit_file)
else:
    location = general.get('location', {}) or {}
    lat = location.get('lat')
    lng = location.get('lng')
    method = general.get('method')
    if lat is None or lng is None or not method:
        print('Error: general.location.lat, general.location.lng, and general.method are required when mode is "calculated"')
        sys.exit(1)
    PT.setMethod(method)
    utcOffset = -(time.timezone/3600)
    isDst = time.localtime().tm_isdst
    times = PT.getTimes((now.year, now.month, now.day), (lat, lng), utcOffset, isDst)

strUpdateCommand = '{}/updateAzaanTimers.py --config {} >> {} 2>&1'.format(
    root_dir,
    shlex.quote(config_path),
    shlex.quote(log_file_path),
)
strClearLogsCommand = 'truncate -s 0 {} 2>&1'.format(shlex.quote(log_file_path))
strJobComment = 'rpiAdhanClockJob'

# Remove existing jobs created by this script
system_cron.remove_all(comment=strJobComment)
print(times['fajr'])
print(times['dhuhr'])
print(times['asr'])
print(times['maghrib'])
print(times['isha'])

# Add times to crontab
for prayer_key in ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']:
    enabled, audio, volume = get_prayer_config(prayer_key)
    if not enabled:
        continue
    play_cmd = build_play_command(audio, volume)
    addAzaanTime(prayer_key, times[prayer_key], system_cron, play_cmd)

# Run this script again overnight
addUpdateCronJob(system_cron, strUpdateCommand, update_hour, update_minute)

# Clear the logs every month
addClearLogsCronJob(system_cron, strClearLogsCommand)

system_cron.write_to_user(user=cron_user)
print('Script execution finished at: ' + str(now))
