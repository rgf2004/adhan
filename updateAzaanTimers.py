#!/usr/bin/env python3

import datetime
import time
import sys
import json
import os
from os.path import dirname, abspath, join as pathjoin
import argparse
import shlex

root_dir = dirname(abspath(__file__))
sys.path.insert(0, pathjoin(root_dir, 'crontab'))

from praytimes import PrayTimes
PT = PrayTimes() 

from crontab import CronTab
system_cron = CronTab(user='pi')

#HELPER FUNCTIONS
#---------------------------------
#---------------------------------
#Function to add azaan time to cron
def parseArgs():
    parser = argparse.ArgumentParser(description='Calculate prayer times and install cronjobs to play Adhan')
    parser.add_argument('--lat', type=float, dest='lat',
                        help='Latitude of the location, for example 30.345621')
    parser.add_argument('--lng', type=float, dest='lng',
                        help='Longitude of the location, for example 60.512126')
    parser.add_argument('--method', choices=['MWL', 'ISNA', 'Egypt', 'Makkah', 'Karachi', 'Tehran', 'Jafari'],
                        dest='method',
                        help='Method of calculation')
    parser.add_argument('--fajr-azaan-volume', type=int, dest='fajr_azaan_vol',
                        help='Volume for fajr azaan as a percent (0-100). 100 is normal (default 100)')
    parser.add_argument('--azaan-volume', type=int, dest='azaan_vol',
                        help='Volume for azaan (other than fajr) as a percent (0-100). 100 is normal (default 100)')
    parser.add_argument('--fajr-audio', dest='fajr_audio',
                        help='MP3 filename or path for fajr (default Adhan-fajr.mp3)')
    parser.add_argument('--azaan-audio', dest='azaan_audio',
                        help='MP3 filename or path for all other prayers (default Adhan-Madinah.mp3)')
    parser.add_argument('--mawaqit', dest='mawaqit_file',
                        help='Path to mawaqit JSON file for prayer times (alternative to lat/lng/method)')
    return parser

def mergeArgs(args):
    file_path = pathjoin(root_dir, '.settings')
    # load values
    lat = lng = method = fajr_azaan_vol = azaan_vol = fajr_audio = azaan_audio = mawaqit_file = None
    try:
        with open(file_path, 'rt') as f:
            parts = f.readlines()[0].strip().split(',')
            # Backward compatible:
            # - old format: lat,lng,method,fajr_volume,azaan_volume
            # - new format: lat,lng,method,fajr_volume,azaan_volume,fajr_audio,azaan_audio
            # - newest format: lat,lng,method,fajr_volume,azaan_volume,fajr_audio,azaan_audio,mawaqit_file
            while len(parts) < 8:
                parts.append('')
            lat, lng, method, fajr_azaan_vol, azaan_vol, fajr_audio, azaan_audio, mawaqit_file = parts[:8]
    except:
        print('No .settings file found')
    def clamp_percent(v):
        return max(0, min(100, int(v)))
    def norm_audio(v, default_name):
        v = (v or '').strip()
        return v or default_name
    # merge args
    if args.lat:
        lat = args.lat
    if lat:
        lat = float(lat)
    if args.lng:
        lng = args.lng
    if lng:
        lng = float(lng)
    if args.method:
        method = args.method
    if args.fajr_azaan_vol:
        fajr_azaan_vol = args.fajr_azaan_vol
    if args.azaan_vol:
        azaan_vol = args.azaan_vol
    if args.fajr_audio:
        fajr_audio = args.fajr_audio
    if args.azaan_audio:
        azaan_audio = args.azaan_audio
    if args.mawaqit_file:
        mawaqit_file = args.mawaqit_file
    elif mawaqit_file:
        mawaqit_file = mawaqit_file.strip() or None

    if fajr_azaan_vol:
        fajr_azaan_vol = clamp_percent(fajr_azaan_vol)
    if azaan_vol:
        azaan_vol = clamp_percent(azaan_vol)
    fajr_audio = norm_audio(fajr_audio, 'Adhan-fajr.mp3')
    azaan_audio = norm_audio(azaan_audio, 'Adhan-Madinah.mp3')

    # save values
    with open(file_path, 'wt') as f:
        f.write('{},{},{},{},{},{},{},{}'.format(
            lat or '', lng or '', method or '',
            fajr_azaan_vol or 100, azaan_vol or 100,
            fajr_audio, azaan_audio, mawaqit_file or ''
        ))
    return lat or None, lng or None, method or None, fajr_azaan_vol or 100, azaan_vol or 100, fajr_audio, azaan_audio, mawaqit_file or None

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

def addUpdateCronJob (objCronTab, strCommand):
  job = objCronTab.new(command=strCommand)
  job.minute.on(15)
  job.hour.on(3)
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
#---------------------------------
#---------------------------------
#HELPER FUNCTIONS END

#Parse arguments
parser = parseArgs()
args = parser.parse_args()
#Merge args with saved values if any
lat, lng, method, fajr_azaan_vol, azaan_vol, fajr_audio, azaan_audio, mawaqit_file = mergeArgs(args)
print(lat, lng, method, fajr_azaan_vol, azaan_vol, fajr_audio, azaan_audio, mawaqit_file)

now = datetime.datetime.now()

# Determine mode and get prayer times
if mawaqit_file:
    # Mawaqit mode
    if args.lat or args.lng or args.method:
        print("Warning: Using mawaqit file; --lat, --lng, --method will be ignored")
    times = get_times_from_mawaqit(mawaqit_file)
else:
    # Praytimes mode (original behavior)
    if not lat or not lng or not method:
        parser.print_usage()
        sys.exit(1)
    PT.setMethod(method)
    utcOffset = -(time.timezone/3600)
    isDst = time.localtime().tm_isdst
    times = PT.getTimes((now.year, now.month, now.day), (lat, lng), utcOffset, isDst)

fajr_audio_path = fajr_audio if fajr_audio.startswith('/') else pathjoin(root_dir, fajr_audio)
azaan_audio_path = azaan_audio if azaan_audio.startswith('/') else pathjoin(root_dir, azaan_audio)
strPlayFajrAzaanMP3Command = '{} {} {} >> {} 2>&1'.format(
    shlex.quote(pathjoin(root_dir, 'playAzaan.sh')),
    shlex.quote(fajr_audio_path),
    shlex.quote(str(fajr_azaan_vol)),
    shlex.quote(pathjoin(root_dir, 'adhan.log')),
)
strPlayAzaanMP3Command = '{} {} {} >> {} 2>&1'.format(
    shlex.quote(pathjoin(root_dir, 'playAzaan.sh')),
    shlex.quote(azaan_audio_path),
    shlex.quote(str(azaan_vol)),
    shlex.quote(pathjoin(root_dir, 'adhan.log')),
)
strUpdateCommand = '{}/updateAzaanTimers.py >> {}/adhan.log 2>&1'.format(root_dir, root_dir)
strClearLogsCommand = 'truncate -s 0 {}/adhan.log 2>&1'.format(root_dir)
strJobComment = 'rpiAdhanClockJob'

# Remove existing jobs created by this script
system_cron.remove_all(comment=strJobComment) 
print(times['fajr'])
print(times['dhuhr'])
print(times['asr'])
print(times['maghrib'])
print(times['isha'])

# Add times to crontab
addAzaanTime('fajr',times['fajr'],system_cron,strPlayFajrAzaanMP3Command)
addAzaanTime('dhuhr',times['dhuhr'],system_cron,strPlayAzaanMP3Command)
addAzaanTime('asr',times['asr'],system_cron,strPlayAzaanMP3Command)
addAzaanTime('maghrib',times['maghrib'],system_cron,strPlayAzaanMP3Command)
addAzaanTime('isha',times['isha'],system_cron,strPlayAzaanMP3Command)

# Run this script again overnight
addUpdateCronJob(system_cron, strUpdateCommand)

# Clear the logs every month
addClearLogsCronJob(system_cron,strClearLogsCommand)

system_cron.write_to_user(user='pi')
print('Script execution finished at: ' + str(now))
