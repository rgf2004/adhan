# Raspberry Pi Adhan Clock
This projects uses a python script which automatically calculates [adhan](https://en.wikipedia.org/wiki/Adhan) times every day and plays all five adhans at their scheduled time using cron. 

## Prerequisites
1. Raspberry Pi running Raspbian
  1. I would stay away from Raspberry Pi zero esp if you're new to this stuff since it doesn't come with a built in audio out port.
  2. Also, if you haven't worked with raspberry pi before, I would highly recommend using [these](https://www.raspberrypi.org/documentation/installation/noobs.md) instructions to get it up and running: https://www.raspberrypi.org/documentation/installation/noobs.md
2. Speakers
3. Auxiliary audio cable
4. `mpg123` is installed. ```sudo apt install mpg123``` ( the replacement of the old omxplayer tool)
5. (Optional) Python virtual environment if you want isolated dependencies.

## Python environment (optional, recommended)
```bash
cd /home/pi/adhan
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Instructions
1. Install git: Go to raspberry pi terminal (command line interface) and install `git`
  * `$ sudo apt-get install git`
2. Clone repo: Clone this repository on your raspberry pi in your `home` directory. (Tip: run `$ cd ~` to go to your home directory)
  * `$ git clone <get repo clone url from github and put it here>`
  * After doing that you should see an `adhan` direcotry in your `home` directory. 

## Run it for the first time
Run this command:

First, copy the template to your local settings file:
```bash
$ cp ./settings.example.json ./settings.json
```

Then run the scheduler:
```bash
$ ./updateAzaanTimers.py --config ./settings.json
```

Before running, open `./settings.json` and update the `general.location` latitude/longitude and `general.method` (for calculated mode), or switch to `mode: "mawaqit"` and set `general.mawaqit_file`.

If everything worked, your output will look something like this:
```
05:51
11:52
14:11
16:30
17:53
51 5 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-fajr.mp3 100 # rpiAdhanClockJob
52 11 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 100 # rpiAdhanClockJob
11 14 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 100 # rpiAdhanClockJob
30 16 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 100 # rpiAdhanClockJob
53 17 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 100 # rpiAdhanClockJob
15 3 * * * /home/pi/adhan/updateAzaanTimers.py --config /home/pi/adhan/settings.json >> /home/pi/adhan/adhan.log 2>&1 # rpiAdhanClockJob
@monthly truncate -s 0 /home/pi/adhan/adhan.log 2>&1 # rpiAdhanClockJob
Script execution finished at: 2017-01-06 21:22:31.512667
```

If you look at the last few lines, you'll see that 5 adhan times have been scheduled. Then there is another line at the end which makes sure that at 03:15 every day the same script will run and calculate adhan times for that day. And lastly, there is a line to clear logs on a monthly basis so that your log file doesn't grow too big.

Note that for later runs you can omit `--config`; it defaults to `./settings.json` and the script reads from it every time.

VOILA! You're done!! Plug in your speakers and enjoy!

## Configuration (`settings.json`)
This repo ships `settings.example.json`. Copy it to `settings.json` for your local configuration (your local file is ignored by git so it won’t be overwritten on pulls). The script requires the file to exist and reads it every run.

Example (`settings.json`):
```json
{
  "general": {
    "mode": "calculated",
    "location": { "lat": 30.345621, "lng": 60.512126 },
    "method": "MWL",
    "mawaqit_file": null,
    "log_file": "adhan.log",
    "update_time": "03:15",
    "default_audio": "Adhan-Madinah.mp3",
    "default_volume": 100
  },
  "prayers": {
    "fajr": { "audio": "Adhan-fajr.mp3", "volume": 100, "enabled": true },
    "dhuhr": { "audio": "Adhan-Madinah.mp3", "volume": 100, "enabled": true },
    "asr": { "audio": "Adhan-Madinah.mp3", "volume": 100, "enabled": true },
    "maghrib": { "audio": "Adhan-Madinah.mp3", "volume": 100, "enabled": true },
    "isha": { "audio": "Adhan-Madinah.mp3", "volume": 100, "enabled": true }
  }
}
```

Attribute notes:
* `general.mode`: `calculated` or `mawaqit`.
* `general.location.lat` / `general.location.lng`: required when `mode` is `calculated`.
* `general.method`: required when `mode` is `calculated`. Allowed values: `MWL`, `ISNA`, `Egypt`, `Makkah`, `Karachi`, `Tehran`, `Jafari`.
* `general.mawaqit_file`: required when `mode` is `mawaqit`.
* `general.update_time`: daily refresh time in `HH:MM` (24-hour) for recalculating/syncing.
* `general.log_file`: output log path (relative to repo or absolute).
* `general.default_audio` / `general.default_volume`: defaults used for any prayer missing its own audio/volume.
* `prayers.<name>`: one of `fajr`, `dhuhr`, `asr`, `maghrib`, `isha`.
* `prayers.<name>.audio`: audio file path (relative to repo or absolute).
* `prayers.<name>.volume`: percent `0-100`.
* `prayers.<name>.enabled`: set `false` to skip that prayer.
* Cron jobs are installed for the current user running the script (not hardcoded to `pi`).

## Alternative: Using Mawaqit Prayer Times

Instead of calculating prayer times, you can use prayer times from [Mawaqit](https://mawaqit.net/) mosques. This is useful if you want to sync with your local mosque's schedule.

### Step 1: Generate the Mawaqit JSON file

The included `mawaqit_util.py` helper script uses the [mawaqit](https://pypi.org/project/mawaqit/) Python library.

First, install it:
```bash
pip install mawaqit
```

Then use the included `mawaqit_util.py` script to find your mosque and generate the JSON file:

```bash
# Find nearby mosques by coordinates
python /home/pi/adhan/mawaqit_util.py -u your@email.com -p yourpassword nearby --lat 48.85 --lng 2.35

# Or search mosques by name
python /home/pi/adhan/mawaqit_util.py -u your@email.com -p yourpassword search "mosque name"
```

The `nearby` and `search` commands will display a list of mosques with their names and UUIDs:
```
1. Mosque Name
   UUID: 30872b8b-c065-4d14-bca6-8cb813dde014
   Address: 123 Street, City
```

Use the UUID from the results to generate the JSON file:
```bash
python /home/pi/adhan/mawaqit_util.py -u your@email.com -p yourpassword generate 30872b8b-c065-4d14-bca6-8cb813dde014 -o /home/pi/adhan/mawaqit.json
```

Note: You need a Mawaqit account (free) to use the API. Register at [mawaqit.net](https://mawaqit.net/).

### Step 2: Run the adhan clock with mawaqit

Update your `./settings.json` to set `general.mode` to `mawaqit` and point `general.mawaqit_file` to the JSON file, then run:
```bash
./updateAzaanTimers.py --config ./settings.json
```

The mawaqit JSON file contains a full year calendar, so you only need to regenerate it once a year.

For subsequent runs, just run with the same config (or omit `--config` to use `./settings.json`):
```bash
./updateAzaanTimers.py --config ./settings.json
```

Please see the [manual](http://praytimes.org/manual) for advanced configuration instructions. 

There are 2 additional arguments that are optional, you can set them in the first run or
further runs: `--fajr-azaan-volume` and `azaan-volume`. You can control the volume of the Azaan
by supplying numbers in millibels. To get more information on how to select the values, run the command with `-h`.

## Configuring custom actions before/after adhan

Sometimes it is needed to run custom commands either before, after or before
and after playing adhan. For example, if you have
[Quran playing continuously](https://github.com/LintangWisesa/RPi_QuranSpeaker),
you would want to pause and resume the playback. Another example, is to set your
status on a social network, or a calendar, to block/unblock the Internet
using [pi.hole rules](https://docs.pi-hole.net/), ... etc.

You can easily do this by adding scripts in the following directories:
- `before-hooks.d`: Scripts to run before adhan playback
- `after-hooks.d`: Scripts to run after adhan playback

### Example:
To pause/resume Quran playback if using the
[RPi_QuranSpeaker](https://github.com/LintangWisesa/RPi_QuranSpeaker) project, place
the following in 2 new files under the above 2 directories:

```bash
# before-hooks.d/01-pause-quran-speaker.sh
#!/usr/bin/env bash
/home/pi/RPi_QuranSpeaker/pauser.py pause
```

```bash
# after-hooks.d/01-resume-quran-speaker.sh
#!/usr/bin/env bash
/home/pi/RPi_QuranSpeaker/pauser.py resume
```

Do not forget to make the scripts executable:
```bash
chmod u+x ./before-hooks.d/01-pause-quran-speaker.sh
chmod u+x ./after-hooks.d/01-resume-quran-speaker.sh
```

## Tips:
1. You can see your currently scheduled jobs by running `crontab -l`
2. The output of the job that runs at 03:15 every night is being captured in `/home/pi/adhan/adhan.log`. This way you can keep track of all successful runs and any potential issues. This file will be truncated at midnight on the forst day of each month. To view the output type `$ cat /home/pi/adhan/adhan.log`

## Credits
I have made modifications / bug fixes but I've used the following as starting point:
* Python code to calculate adhan times: http://praytimes.org/code/ 
* Basic code to turn the above into an adhan clock: http://randomconsultant.blogspot.co.uk/2013/07/turn-your-raspberry-pi-into-azaanprayer.html
* Cron scheduler: https://pypi.python.org/pypi/python-crontab/ 
