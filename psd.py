# Copyright (C) 2020  ViiSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import json
import platform
import signal
import subprocess
import sys
import time
from datetime import timedelta

DOW = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,  "fri": 4, "sat": 5, "sun": 6}


class Job:
    def __init__(self, name, cmd, schedule, is_sh):
        self.name = name
        self.cmd = cmd
        self.schedule = schedule
        self.is_shell = is_sh
        self.job = None
        self.start_datetime = None
        self.stop_datetime = None
        self.init_start_dt()
        self.init_stop_dt()

    def init_start_dt(self):
        if self.schedule["start"]["time"] == "now":
            return None

        if self.start_datetime is None:
            start_h_m = int_time(self.schedule["start"]["time"])
            if isinstance(self.schedule["start"]["day"], str):
                start_date = next_weekday(datetime.date.today(), DOW[self.schedule["start"]["day"]])
            else:
                start_date = datetime.date.today()

            self.start_datetime = datetime.datetime.combine(
                start_date,
                datetime.time(start_h_m[0], start_h_m[1], 0))

    def init_stop_dt(self):
        if self.schedule["finish"]["time"] == "never":
            return None

        if self.stop_datetime is None:
            stop_h_m = int_time(self.schedule["finish"]["time"])
            stop_day = 0
            if "day" in self.schedule["finish"]:
                if isinstance(self.schedule["finish"]["day"], str):
                    stop_day = DOW[self.schedule["finish"]["day"]]
                    self.stop_datetime = next_weekday(
                        datetime.datetime.combine(
                            datetime.date.today(),
                            datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                        stop_day)
                else:
                    stop_day = self.schedule["finish"]["day"]
                    self.stop_datetime = datetime.datetime.combine(
                        datetime.date.today() + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))
            else:
                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))

    def try_start(self):  # True - job is running, False - job is not running
        if self.schedule["start"]["time"] == "now":
            if self.job is None:
                self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                print("[ Job '" + str(self.name) + "' started at " + str(datetime.datetime.now()) + " ]")
            return True
        else:
            if self.job is None:
                now = datetime.datetime.now()
                if self.start_datetime <= now <= self.stop_datetime:
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    start_h_m = int_time(self.schedule["start"]["time"])
                    start_day = self.schedule["start"]["day"]
                    start_date = datetime.datetime.now()
                    if "day" in self.schedule["finish"]:
                        if isinstance(self.schedule["finish"]["day"], str):
                            start_date = next_weekday(datetime.date.today(), DOW[self.schedule["finish"]["day"]])
                        else:
                            start_day += self.schedule["finish"]["day"]
                    self.start_datetime = datetime.datetime.combine(
                        start_date + timedelta(days=start_day),
                        datetime.time(start_h_m[0], start_h_m[1], 0))
                    print("[ Job '" + str(self.name) + "' started at " + str(now) +
                          ". Finished in: " + str(self.stop_datetime) +
                          ". Next start: " + str(self.start_datetime) + " ]")
                    return True
                else:
                    return False
            else:
                return True

    def try_stop(self):  # true - job is finished, false - job is not finished
        if self.schedule["finish"]["time"] == "never":
            return False
        else:
            now = datetime.datetime.now()
            if now > self.stop_datetime:
                if platform.system() == 'Windows':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.job.pid)])
                else:
                    self.job.kill()
                self.job = None
                print("[ Job '" + self.name + "' finished at " + str(now) + " ]")

                stop_h_m = int_time(self.schedule["finish"]["time"])
                stop_day = self.schedule["start"]["day"]
                if "day" in self.schedule["finish"]:
                    if isinstance(self.schedule["finish"]["day"], str):
                        stop_day = DOW[self.schedule["finish"]["day"]]
                        self.stop_datetime = next_weekday(
                            datetime.datetime.combine(
                                datetime.date.today(),
                                datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                            stop_day)
                        return True
                    else:
                        stop_day += self.schedule["finish"]["day"]

                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))
                return True
            else:
                return False

    def stop_immediately(self):
        if self.job is not None:
            if platform.system() == 'Windows':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.job.pid)])
            else:
                self.job.kill()
            print("[ Job '" + self.name + "' finished at " + str(datetime.datetime.now()) + " ]")


class JobRep:
    def __init__(self, name, cmd, schedule, is_sh, repeat):
        self.name = name
        self.cmd = cmd
        self.schedule = schedule
        self.is_shell = is_sh
        self.start_datetime = None
        self.repeat = repeat
        self.is_start = False
        self.next_repeat = None
        self.start_datetime = None
        self.stop_datetime = None
        self.init_start_dt()
        self.init_stop_dt()

    def init_start_dt(self):
        if self.schedule["start"]["time"] == "now":
            return None

        if self.start_datetime is None:
            start_h_m = int_time(self.schedule["start"]["time"])
            if isinstance(self.schedule["start"]["day"], str):
                start_date = next_weekday(datetime.date.today(), DOW[self.schedule["start"]["day"]])
            else:
                start_date = datetime.date.today()

            self.start_datetime = datetime.datetime.combine(
                start_date,
                datetime.time(start_h_m[0], start_h_m[1], 0))

    def init_stop_dt(self):
        if self.schedule["start"]["time"] == "never":
            return None

        if self.stop_datetime is None:
            stop_h_m = int_time(self.schedule["finish"]["time"])
            stop_day = 0
            if "day" in self.schedule["finish"]:
                if isinstance(self.schedule["finish"]["day"], str):
                    stop_day = DOW[self.schedule["finish"]["day"]]
                    self.stop_datetime = next_weekday(
                        datetime.datetime.combine(
                            datetime.date.today(),
                            datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                        stop_day)
                else:
                    stop_day = self.schedule["finish"]["day"]
                    self.stop_datetime = datetime.datetime.combine(
                        datetime.date.today() + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))
            else:
                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))

    def try_start(self):  # True - job is running, False - job is not running
        if self.is_start:
            return True
        elif self.schedule["start"]["time"] == "now":
            self.is_start = True
            subprocess.Popen(self.cmd, shell=self.is_shell)
            print("[ Job '" + str(self.name) + "' started at " + str(datetime.datetime.now()) + " ]")
            return True
        else:
            now = datetime.datetime.now()
            if self.start_datetime <= now <= self.stop_datetime:
                subprocess.Popen(self.cmd, shell=self.is_shell)
                self.is_start = True
                self.next_repeat = calc_repeat(now, self.repeat)
                start_h_m = int_time(self.schedule["start"]["time"])
                start_day = self.schedule["start"]["day"]
                start_date = datetime.datetime.now()
                if "day" in self.schedule["finish"]:
                    if isinstance(self.schedule["finish"]["day"], str):
                        start_date = next_weekday(datetime.date.today(), DOW[self.schedule["finish"]["day"]])
                    else:
                        start_day += self.schedule["finish"]["day"]
                self.start_datetime = datetime.datetime.combine(
                    start_date + timedelta(days=start_day),
                    datetime.time(start_h_m[0], start_h_m[1], 0))
                print("[ Job '" + str(self.name) + "' started at " + str(now) +
                      ". Finished in: " + str(self.stop_datetime) +
                      ". Next start: " + str(self.start_datetime) + " ]")
                return True
            else:
                return False

    def try_stop(self):  # true - job is finished, false - job is not finished
        if self.schedule["finish"]["time"] == "never":
            return False
        else:
            now = datetime.datetime.now()
            if now > self.stop_datetime:
                self.is_start = False
                print("[ Job '" + self.name + "' finished at " + str(now) + " ]")
                stop_h_m = int_time(self.schedule["finish"]["time"])
                stop_day = self.schedule["start"]["day"]
                if "day" in self.schedule["finish"]:
                    if isinstance(self.schedule["finish"]["day"], str):
                        stop_day = DOW[self.schedule["finish"]["day"]]
                        self.stop_datetime = next_weekday(
                            datetime.datetime.combine(
                                datetime.date.today(),
                                datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                            stop_day)
                        return True
                    else:
                        stop_day += self.schedule["finish"]["day"]

                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))
                return True
            else:
                return False

    def try_repeat(self):
        now = datetime.datetime.now()
        if now > self.next_repeat:
            subprocess.Popen(self.cmd, shell=self.is_shell)
            self.next_repeat = calc_repeat(now, self.repeat)


def calc_repeat(dt, repeat):
    if repeat["unit"] == "s":
        return dt + timedelta(seconds=repeat["val"])
    elif repeat["unit"] == "m":
        return dt + timedelta(minutes=repeat["val"])
    elif repeat["unit"] == "h":
        return dt + timedelta(hours=repeat["val"])


def int_time(t):
    hour = int(t[0:2])
    minute = int(t[3:5])
    return [hour, minute]


def is_time_format(t):
    try:
        time.strptime(t, '%H:%M')
        return True
    except ValueError:
        return False


def next_weekday(dt, weekday):
    days_ahead = weekday - dt.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return dt + datetime.timedelta(days_ahead)


def is_dow(maybe_dow):
    return maybe_dow in DOW


def now_in_range(start, end):
    s = datetime.datetime.strptime(start, "%H:%M").time()
    e = datetime.datetime.strptime(end, "%H:%M").time()
    now = datetime.datetime.strptime(str(datetime.datetime.now().time().strftime("%H:%M")), "%H:%M").time()
    if s <= e:
        return s <= now <= e
    else:
        return s <= now or now <= e


def error(message):
    print(message)
    exit(-1)


def sigint_handler(signum, frame):
    for _j in jobs:
        _j.stop_immediately()
    print()
    exit(1)


try:
    f_name = sys.argv[1]
except IndexError:
    f_name = "psd.json"

jobs = []
jobs_r = []

settings = json.load(open(f_name))
if "is_shell" not in settings:
    is_shell = True
else:
    is_shell = settings["is_shell"]

for js in settings["jobs"]:
    if "name" not in js:
        error("Field 'name' is not found in job!")
    if "cmd" not in js:
        error("Field 'cmd' is not found in job!\nJob name: " + js["name"])
    if "schedule" not in js:
        error("Field 'schedule' is not found in job!\nJob name: " + js["name"])
    if "start" not in js["schedule"]:
        error("Field 'start' is not found in job{schedule}!\nJob name: " + js["name"])
    if "day" in js["schedule"]["start"]:
        if isinstance(js["schedule"]["start"]["day"], str):
            if not is_dow(js["schedule"]["start"]["day"]):
                error("Field 'day' in job{schedule{start}} is not day of week! Found "
                      + str(js["schedule"]["start"]["day"])
                      + ".\nPossible values: 'mon', 'tue', 'wed', 'thu', 'fri','sat', 'sun'.\nJob name: " + js["name"])
        elif not isinstance(js["schedule"]["start"]["day"], int):
            error("Field 'day' in job{schedule{start}} is not int!\nJob name: " + js["name"])
    if "time" not in js["schedule"]["start"]:
        error("Field 'time' is not found in job{schedule{start}}!\nJob name: " + js["name"])
    if not is_time_format(js["schedule"]["start"]["time"]):
        if js["schedule"]["start"]["time"] != "now":
            error("Field 'time' has wrong pattern! Expected ##:##, actual " + str(js["schedule"]["start"]["time"])
                  + "\nJob name: " + js["name"])
    if "finish" not in js["schedule"]:
        error("Field 'finish' is not found in job{schedule}!\nJob name: " + js["name"])
    if "day" in js["schedule"]["finish"]:
        if isinstance(js["schedule"]["finish"]["day"], str):
            if not is_dow(js["schedule"]["finish"]["day"]):
                error("Field 'day' in job{schedule{finish}} is not day of week! Found "
                      + str(js["schedule"]["finish"]["day"])
                      + ".\nPossible values: 'mon', 'tue', 'wed', 'thu', 'fri','sat', 'sun'.\nJob name: " + js["name"])
        elif not isinstance(js["schedule"]["finish"]["day"], int):
            error("Field 'day' in job{schedule{finish}} is not int!\nJob name: " + js["name"])
    if "time" not in js["schedule"]["finish"]:
        error("Field 'time' is not found in job{schedule{finish}}!\nJob name: " + js["name"])
    if not is_time_format(js["schedule"]["finish"]["time"]):
        if js["schedule"]["finish"]["time"] != "never":
            error("Field 'time' has wrong pattern! Expected ##:##, actual " + str(js["schedule"]["finish"]["time"])
                  + "\nJob name: " + js["name"])
    if "repeat" in js:
        if "unit" not in js["repeat"]:
            error("Field 'unit' is not found in job{repeat}!\nJob name: " + js["name"])
        if "val" not in js["repeat"]:
            error("Field 'val' is not found in job{repeat}!\nJob name: " + js["name"])

        jobs_r.append(JobRep(
            js["name"],
            js["cmd"],
            js["schedule"],
            is_shell,
            js["repeat"]))
    else:
        jobs.append(Job(
            js["name"],
            js["cmd"],
            js["schedule"],
            is_shell))

print("[ Schedule started at " + str(datetime.datetime.now()) + " ]")
signal.signal(signal.SIGINT, sigint_handler)

while True:
    for j in jobs:
        if j.try_start():
            j.try_stop()
    for jr in jobs_r:
        if jr.try_start():
            if not jr.try_stop():
                jr.try_repeat()
    time.sleep(1)

