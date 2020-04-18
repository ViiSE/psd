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
import subprocess
import platform
import json
import time
import sys
from datetime import timedelta


class Job:
    def __init__(self, name, cmd, schedule, is_sh):
        self.name = name
        self.cmd = cmd
        self.schedule = schedule
        self.is_shell = is_sh
        self.job = None
        self.start_datetime = None
        self.stop_datetime = None

    def try_start(self):  # True - job is running, False - job is not running
        if self.schedule["start"]["time"] == "now":
            if self.job is None:
                self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                print("[ Job '" + str(self.name) + "' started at " + str(datetime.datetime.now()) + " ]")
            return True
        else:
            if self.job is None:
                if self.start_datetime is None:
                    start_h_m = int_time(self.schedule["start"]["time"])
                    self.start_datetime = datetime.datetime.combine(
                        datetime.date.today(),
                        datetime.time(start_h_m[0], start_h_m[1], 0))

                now = datetime.datetime.now()
                if now > self.start_datetime:
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    print("[ Job '" + str(self.name) + "' started at " + str(now) + " ]")
                    start_day = self.schedule["start"]["day"]
                    if "day" in self.schedule["finish"]:
                        start_day += self.schedule["finish"]["day"]

                    start_h_m = int_time(self.schedule["start"]["time"])
                    self.start_datetime = datetime.datetime.combine(
                        datetime.date.today() + timedelta(days=start_day),
                        datetime.time(start_h_m[0], start_h_m[1], 0))
                    return True
                else:
                    return False
            else:
                return True

    def try_stop(self):  # true - job is finished, false - job is not finished
        if self.schedule["finish"]["time"] == "never":
            return False
        else:
            if self.stop_datetime is None:
                stop_day = 0
                if "day" in self.schedule["finish"]:
                    stop_day = self.schedule["finish"]["day"]

                stop_h_m = int_time(self.schedule["finish"]["time"])
                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))

            now = datetime.datetime.now()
            if now > self.stop_datetime:
                if platform.system() == 'Windows':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.job.pid)])
                else:
                    self.job.kill()
                self.job = None
                print("[ Job '" + self.name + "' finished at + " + str(now) + " ]")

                stop_day = self.schedule["start"]["day"]
                if "day" in self.schedule["finish"]:
                    stop_day += self.schedule["finish"]["day"]

                stop_h_m = int_time(self.schedule["finish"]["time"])
                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))


class JobRep:
    def __init__(self, name, cmd, schedule, is_sh, repeat):
        self.name = name
        self.cmd = cmd
        self.schedule = schedule
        self.is_shell = is_sh
        self.start_datetime = None
        self.stop_datetime = None
        self.repeat = repeat
        self.is_start = False
        self.next_repeat = None

    def try_start(self):  # True - job is running, False - job is not running
        if self.is_start:
            return True
        elif self.schedule["start"]["time"] == "now":
            self.is_start = True
            print("[ Job '" + str(self.name) + "' started at " + str(datetime.datetime.now()) + " ]")
            return True
        else:
            if self.start_datetime is None:
                start_h_m = int_time(self.schedule["start"]["time"])
                self.start_datetime = datetime.datetime.combine(
                    datetime.date.today(),
                    datetime.time(start_h_m[0], start_h_m[1], 0))

            now = datetime.datetime.now()
            if now > self.start_datetime:
                subprocess.Popen(self.cmd, shell=self.is_shell)
                print("[ Job '" + str(self.name) + "' started at " + str(now) + " ]")
                start_day = self.schedule["start"]["day"]
                if "day" in self.schedule["finish"]:
                    start_day += self.schedule["finish"]["day"]

                start_h_m = int_time(self.schedule["start"]["time"])
                self.start_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=start_day),
                    datetime.time(start_h_m[0], start_h_m[1], 0))
                self.is_start = True
                self.next_repeat = calc_repeat(now, self.repeat)
                return True
            else:
                return False

    def try_stop(self):  # true - job is finished, false - job is not finished
        if self.schedule["finish"]["time"] == "never":
            return False
        else:
            if self.stop_datetime is None:
                stop_day = 0
                if "day" in self.schedule["finish"]:
                    stop_day = self.schedule["finish"]["day"]

                stop_h_m = int_time(self.schedule["finish"]["time"])
                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))

            now = datetime.datetime.now()
            if now > self.stop_datetime:
                stop_day = self.schedule["start"]["day"]
                if "day" in self.schedule["finish"]:
                    stop_day += self.schedule["finish"]["day"]

                stop_h_m = int_time(self.schedule["finish"]["time"])
                self.stop_datetime = datetime.datetime.combine(
                    datetime.date.today() + timedelta(days=stop_day),
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))
                self.is_start = False
                print("[ Job '" + self.name + "' finished at + " + str(now) + " ]")
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


is_shell = sys.argv[1].lower() == 'true'

jobs = []
jobs_r = []

settings = json.load(open("psd.json"))
for js in settings["jobs"]:
    if "name" not in js:
        print("Field 'name' is not found in job!")
        exit(-1)
    if "cmd" not in js:
        print("Field 'cmd' is not found in job!")
        exit(-1)
    if "schedule" not in js:
        print("Field 'schedule' is not found in job!")
        exit(-1)
    if "start" not in js["schedule"]:
        print("Field 'start' is not found in job{schedule}!")
        exit(-1)
    if "time" not in js["schedule"]["start"]:
        print("Field 'time' is not found in job{schedule{start}}!")
        exit(-1)
    if not is_time_format(js["schedule"]["start"]["time"]):
        if js["schedule"]["start"]["time"] != "now":
            print("Field 'time' has wrong pattern! Expected ##:##, actual " + str(js["schedule"]["start"]["time"]))
            exit(-1)
    if "finish" not in js["schedule"]:
        print("Field 'finish' is not found in job{schedule}!")
        exit(-1)
    if "time" not in js["schedule"]["finish"]:
        print("Field 'time' is not found in job{schedule{finish}}!")
        exit(-1)
    if not is_time_format(js["schedule"]["finish"]["time"]):
        if js["schedule"]["finish"]["time"] != "never":
            print("Field 'time' has wrong pattern! Expected ##:##, actual " + str(js["schedule"]["finish"]["time"]))
            exit(-1)
    if "repeat" in js:
        if "unit" not in js["repeat"]:
            print("Field 'unit' is not found in job{repeat}!")
            exit(-1)
        if "val" not in js["repeat"]:
            print("Field 'val' is not found in job{repeat}!")
            exit(-1)

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
while True:
    for j in jobs:
        if j.try_start():
            j.try_stop()
    for jr in jobs_r:
        if jr.try_start():
            if not jr.try_stop():
                jr.try_repeat()
    time.sleep(1)
