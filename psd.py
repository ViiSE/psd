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
from os import path

DOW = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,  "fri": 4, "sat": 5, "sun": 6}

MONTHS = {"dec": 12, "jan": 1,  "feb": 2,
          "mar": 3,  "apr": 4,  "may": 5,
          "jun": 6,  "jul": 7,  "aug": 8,
          "sep": 9,  "oct": 10, "nov": 11}


class DateTimeMonthsJob:
    def __init__(self, _dt, _months):
        self._dt = _dt
        self._months = _months
        self._iterator = 0
        _today = datetime.datetime.today()
        for _month in _months:
            if _today.month > MONTHS[_month]:
                self._iterator += 1
                continue
            elif _today.day > _dt.day:
                self._iterator += 1
                continue
            elif _today.day == _dt.day:
                if _today.hour > _dt.hour:
                    self._iterator += 1
                    continue
                elif _today.hour == _dt.hour:
                    if _today.minute > _dt.minute:
                        self._iterator += 1
                        continue

    def next_date_time(self):
        year = self._dt.year

        if self._iterator >= len(self._months):
            self._iterator = 0
            year += 1

        _month = MONTHS[self._months[self._iterator]]
        self._dt = datetime.datetime(
            year, _month, 1, 0, 0, 0, 0)
        self._iterator += 1
        return self._dt


def add_months(dt, months):
    if isinstance(months, int):
        _month = dt.month - 1 + months
        year = dt.year + _month // 12
        _month = _month % 12 + 1
        return datetime.date(year, _month, 1)
    else:
        _year = dt.year
        _month = MONTHS[months]

        if dt.month >= _month:
            _year += 1
        dt = datetime.datetime(
            _year, _month, 1, 0, 0, 0, 0)
        return dt


class Job:
    def __init__(self, name, cmd, schedule, when_finished, is_sh):
        self.name = name
        self.cmd = cmd
        self.schedule = schedule
        self.is_shell = is_sh
        self.when_finished = when_finished
        self.job = None
        self.start_datetime = None
        self.stop_datetime = None
        self.dt_month = None
        self.init_start_dt()
        self.init_stop_dt()

    def init_start_dt(self):
        if self.start_datetime is None:
            if "month" in self.schedule["start"]:
                if isinstance(self.schedule["start"]["month"]["values"], list):
                    self.dt_month = DateTimeMonthsJob(datetime.datetime.today(),
                                                      self.schedule["start"]["month"]["values"])
                    start_date = self.dt_month.next_date_time()
                else:
                    start_date = add_months(datetime.date.today(), self.schedule["start"]["month"]["values"])
                if isinstance(self.schedule["start"]["month"]["day"], str):
                    for i in range(self.schedule["start"]["month"]["each"]):
                        start_date = next_weekday(start_date, DOW[self.schedule["start"]["month"]["day"]])
                else:
                    start_date = datetime.date(year=start_date.year,
                                               month=start_date.month,
                                               day=self.schedule["start"]["month"]["day"])
                start_h_m = int_time(self.schedule["start"]["month"]["time"])
            else:
                if self.schedule["start"]["time"] == "now":
                    return None
                start_h_m = int_time(self.schedule["start"]["time"])
                if isinstance(self.schedule["start"]["day"], str):
                    start_date = next_weekday(datetime.date.today(), DOW[self.schedule["start"]["day"]])
                else:
                    start_date = datetime.date.today()

            self.start_datetime = datetime.datetime.combine(
                start_date,
                datetime.time(start_h_m[0], start_h_m[1], 0))

    def init_stop_dt(self):
        if self.start_datetime is None:
            start_dt = datetime.date.today()
        else:
            start_dt = self.start_datetime

        if "month" in self.schedule["finish"]:
            if isinstance(self.schedule["finish"]["month"]["values"], str):
                stop_date = add_months(start_dt, self.schedule["finish"]["month"]["values"])
            else:
                stop_date = add_months(start_dt, self.schedule["finish"]["month"]["values"])
            if isinstance(self.schedule["finish"]["month"]["day"], str):
                for i in range(self.schedule["finish"]["month"]["each"]):
                    stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
            else:
                stop_date = datetime.date(year=stop_date.year,
                                          month=stop_date.month,
                                          day=self.schedule["finish"]["month"]["day"])
            stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
            self.stop_datetime = datetime.datetime.combine(
                stop_date,
                datetime.time(stop_h_m[0], stop_h_m[1], 0))
        else:
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
                                start_dt,
                                datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                            stop_day)
                    else:
                        stop_day = self.schedule["finish"]["day"]
                        self.stop_datetime = datetime.datetime.combine(
                            start_dt + timedelta(days=stop_day),
                            datetime.time(stop_h_m[0], stop_h_m[1], 0))
                else:
                    self.stop_datetime = datetime.datetime.combine(
                        start_dt + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))

    def try_start(self):  # True - job is running, False - job is not running
        if "month" in self.schedule["start"]:
            if self.job is None:
                now = datetime.datetime.now()
                if self.start_datetime <= now <= self.stop_datetime:
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    if isinstance(self.schedule["start"]["month"]["values"], list):
                        start_date = self.dt_month.next_date_time()
                    else:
                        start_date = add_months(self.start_datetime, self.schedule["start"]["month"]["values"])
                    if isinstance(self.schedule["start"]["month"]["day"], str):
                        for i in range(self.schedule["start"]["month"]["each"]):
                            start_date = next_weekday(start_date, DOW[self.schedule["start"]["month"]["day"]])
                    else:
                        start_date = datetime.date(year=start_date.year,
                                                   month=start_date.month,
                                                   day=self.schedule["start"]["month"]["day"])
                    start_h_m = int_time(self.schedule["start"]["month"]["time"])

                    self.start_datetime = datetime.datetime.combine(
                        start_date,
                        datetime.time(start_h_m[0], start_h_m[1], 0))

                    if self.when_finished:
                        if self.start_datetime < self.stop_datetime:
                            temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                            month=self.stop_datetime.month,
                                                            day=self.stop_datetime.day)
                            if isinstance(self.schedule["start"]["day"], str):
                                temp_start_date += next_weekday(temp_start_date,
                                                                DOW[self.schedule["start"]["day"]])
                            else:
                                temp_start_date += timedelta(days=self.schedule["start"]["day"])
                            self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                    month=temp_start_date.month,
                                                                    day=temp_start_date.day,
                                                                    hour=self.start_datetime.hour,
                                                                    minute=self.start_datetime.minute,
                                                                    second=self.start_datetime.second)
                    print("[ Job '" + str(self.name) + "' started at " + str(now) +
                          ". Finished in: " + str(self.stop_datetime) +
                          ". Next start: " + str(self.start_datetime) + " ]")
                    return True
                else:
                    return False
            else:
                return True
        else:
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

                        if self.when_finished:
                            if self.start_datetime < self.stop_datetime:
                                temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                                month=self.stop_datetime.month,
                                                                day=self.stop_datetime.day)
                                if isinstance(self.schedule["start"]["day"], str):
                                    temp_start_date += next_weekday(temp_start_date,
                                                                    DOW[self.schedule["start"]["day"]])
                                else:
                                    temp_start_date += timedelta(days=self.schedule["start"]["day"])
                                self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                        month=temp_start_date.month,
                                                                        day=temp_start_date.day,
                                                                        hour=self.start_datetime.hour,
                                                                        minute=self.start_datetime.minute,
                                                                        second=self.start_datetime.second)
                        print("[ Job '" + str(self.name) + "' started at " + str(now) +
                              ". Finished in: " + str(self.stop_datetime) +
                              ". Next start: " + str(self.start_datetime) + " ]")
                        return True
                    else:
                        return False
                else:
                    return True

    def try_stop(self):  # true - job is finished, false - job is not finished
        now = datetime.datetime.now()
        if "month" in self.schedule["finish"]:
            if now > self.stop_datetime:
                if platform.system() == 'Windows':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.job.pid)])
                else:
                    self.job.kill()
                self.job = None
                print("[ Job '" + self.name + "' finished at " + str(now) + " ]")

                if isinstance(self.schedule["finish"]["month"]["values"], str):
                    stop_date = add_months(self.stop_datetime, MONTHS[self.schedule["finish"]["month"]["values"]])
                else:
                    stop_date = add_months(self.stop_datetime, self.schedule["finish"]["month"]["values"])
                if isinstance(self.schedule["finish"]["month"]["day"], str):
                    for i in range(self.schedule["finish"]["month"]["each"]):
                        stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
                else:
                    stop_date = datetime.date(year=stop_date.year,
                                              month=stop_date.month,
                                              day=self.schedule["finish"]["month"]["day"])
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                self.stop_datetime = datetime.datetime.combine(
                    stop_date,
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))
                return True
        else:
            if self.schedule["finish"]["time"] == "never":
                return False
            else:
                if self.start_datetime is None:
                    start_dt = datetime.date.today()
                else:
                    start_dt = self.start_datetime

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
                                    start_dt,
                                    datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                                stop_day)
                            return True
                        else:
                            stop_day += self.schedule["finish"]["day"]

                    self.stop_datetime = datetime.datetime.combine(
                        start_dt + timedelta(days=stop_day),
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
    def __init__(self, name, cmd, schedule, is_sh, when_finished, repeat):
        self.name = name
        self.cmd = cmd
        self.schedule = schedule
        self.is_shell = is_sh
        self.start_datetime = None
        self.when_finished = when_finished
        self.repeat = repeat
        self.dt_month = None
        self.is_start = False
        self.is_stop = False
        self.job = None
        self.next_repeat = None
        self.start_datetime = None
        self.stop_datetime = None
        self.init_start_dt()
        self.init_stop_dt()

    def init_start_dt(self):
        if self.start_datetime is None:
            if "month" in self.schedule["start"]:
                if isinstance(self.schedule["start"]["month"]["values"], list):
                    self.dt_month = DateTimeMonthsJob(datetime.datetime.today(),
                                                      self.schedule["start"]["month"]["values"])
                    start_date = self.dt_month.next_date_time()
                else:
                    start_date = add_months(datetime.date.today(), self.schedule["start"]["month"]["values"])
                if isinstance(self.schedule["start"]["month"]["day"], str):
                    for i in range(self.schedule["start"]["month"]["each"]):
                        start_date = next_weekday(start_date, DOW[self.schedule["start"]["month"]["day"]])
                else:
                    start_date = datetime.date(year=start_date.year,
                                               month=start_date.month,
                                               day=self.schedule["start"]["month"]["day"])
                start_h_m = int_time(self.schedule["start"]["month"]["time"])
            else:
                if self.schedule["start"]["time"] == "now":
                    return None
                start_h_m = int_time(self.schedule["start"]["time"])
                if isinstance(self.schedule["start"]["day"], str):
                    start_date = next_weekday(datetime.date.today(), DOW[self.schedule["start"]["day"]])
                else:
                    start_date = datetime.date.today()

            self.start_datetime = datetime.datetime.combine(
                start_date,
                datetime.time(start_h_m[0], start_h_m[1], 0))

    def init_stop_dt(self):
        if self.start_datetime is None:
            start_dt = datetime.date.today()
        else:
            start_dt = self.start_datetime

        if "month" in self.schedule["finish"]:
            if isinstance(self.schedule["finish"]["month"]["values"], str):
                stop_date = add_months(start_dt, self.schedule["finish"]["month"]["values"])
            else:
                stop_date = add_months(start_dt, self.schedule["finish"]["month"]["values"])
            if isinstance(self.schedule["finish"]["month"]["day"], str):
                for i in range(self.schedule["finish"]["month"]["each"]):
                    stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
            else:
                stop_date = datetime.date(year=stop_date.year,
                                          month=stop_date.month,
                                          day=self.schedule["finish"]["month"]["day"])
            stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
            self.stop_datetime = datetime.datetime.combine(
                stop_date,
                datetime.time(stop_h_m[0], stop_h_m[1], 0))
        else:
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
                                start_dt,
                                datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                            stop_day)
                    else:
                        stop_day = self.schedule["finish"]["day"]
                        self.stop_datetime = datetime.datetime.combine(
                            start_dt + timedelta(days=stop_day),
                            datetime.time(stop_h_m[0], stop_h_m[1], 0))
                else:
                    self.stop_datetime = datetime.datetime.combine(
                        start_dt + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))

    def try_start(self):  # True - job is running, False - job is not running
        if self.is_stop:
            return False
        if self.is_start:
            return True
        elif "month" in self.schedule["start"]:
            if self.job is None:
                now = datetime.datetime.now()
                if self.start_datetime <= now <= self.stop_datetime:
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    self.is_start = True
                    self.next_repeat = calc_repeat(now, self.repeat)
                    if isinstance(self.schedule["start"]["month"]["values"], list):
                        start_date = self.dt_month.next_date_time()
                    else:
                        start_date = add_months(self.start_datetime, self.schedule["start"]["month"]["values"])
                    if isinstance(self.schedule["start"]["month"]["day"], str):
                        for i in range(self.schedule["start"]["month"]["each"]):
                            start_date = next_weekday(start_date, DOW[self.schedule["start"]["month"]["day"]])
                    else:
                        start_date = datetime.date(year=start_date.year,
                                                   month=start_date.month,
                                                   day=self.schedule["start"]["month"]["day"])
                    start_h_m = int_time(self.schedule["start"]["month"]["time"])

                    self.start_datetime = datetime.datetime.combine(
                        start_date,
                        datetime.time(start_h_m[0], start_h_m[1], 0))

                    if self.when_finished:
                        if self.start_datetime < self.stop_datetime:
                            temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                            month=self.stop_datetime.month,
                                                            day=self.stop_datetime.day)
                            if isinstance(self.schedule["start"]["day"], str):
                                temp_start_date += next_weekday(temp_start_date,
                                                                DOW[self.schedule["start"]["day"]])
                            else:
                                temp_start_date += timedelta(days=self.schedule["start"]["day"])
                            self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                    month=temp_start_date.month,
                                                                    day=temp_start_date.day,
                                                                    hour=self.start_datetime.hour,
                                                                    minute=self.start_datetime.minute,
                                                                    second=self.start_datetime.second)
                    print("[ Job '" + str(self.name) + "' started at " + str(now) +
                          ". Finished in: " + str(self.stop_datetime) +
                          ". Next start: " + str(self.start_datetime) + " ]")
                    return True
                else:
                    return False
            else:
                return True
        else:
            if self.schedule["start"]["time"] == "now":
                if self.job is None:
                    self.is_start = True
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    print("[ Job '" + str(self.name) + "' started at " + str(datetime.datetime.now()) + " ]")
                return True
            else:
                if self.job is None:
                    now = datetime.datetime.now()
                    if self.start_datetime <= now <= self.stop_datetime:
                        self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                        self.is_start = True
                        self.next_repeat = calc_repeat(now, self.repeat)
                        start_h_m = int_time(self.schedule["start"]["time"])
                        start_day = self.schedule["start"]["day"]
                        start_date = datetime.datetime.now()
                        if "day" in self.schedule["finish"]:
                            if isinstance(self.schedule["finish"]["day"], str):
                                start_date = next_weekday(datetime.date.today(),
                                                          DOW[self.schedule["finish"]["day"]])
                            else:
                                start_day += self.schedule["finish"]["day"]
                        self.start_datetime = datetime.datetime.combine(
                            start_date + timedelta(days=start_day),
                            datetime.time(start_h_m[0], start_h_m[1], 0))

                        if self.when_finished:
                            if self.start_datetime < self.stop_datetime:
                                temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                                month=self.stop_datetime.month,
                                                                day=self.stop_datetime.day)
                                if isinstance(self.schedule["start"]["day"], str):
                                    temp_start_date += next_weekday(temp_start_date,
                                                                    DOW[self.schedule["start"]["day"]])
                                else:
                                    temp_start_date += timedelta(days=self.schedule["start"]["day"])
                                self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                        month=temp_start_date.month,
                                                                        day=temp_start_date.day,
                                                                        hour=self.start_datetime.hour,
                                                                        minute=self.start_datetime.minute,
                                                                        second=self.start_datetime.second)
                        print("[ Job '" + str(self.name) + "' started at " + str(now) +
                              ". Finished in: " + str(self.stop_datetime) +
                              ". Next start: " + str(self.start_datetime) + " ]")
                        return True
                    else:
                        return False
                else:
                    return True

    def try_stop(self):  # true - job is finished, false - job is not finished
        if self.is_stop:
            return True

        now = datetime.datetime.now()
        if "month" in self.schedule["finish"]:
            if now > self.stop_datetime:
                self.is_start = False
                print("[ Job '" + self.name + "' finished at " + str(now) + " ]")

                if isinstance(self.schedule["finish"]["month"]["values"], str):
                    stop_date = add_months(self.stop_datetime, MONTHS[self.schedule["finish"]["month"]["values"]])
                else:
                    stop_date = add_months(self.stop_datetime, self.schedule["finish"]["month"]["values"])
                if isinstance(self.schedule["finish"]["month"]["day"], str):
                    for i in range(self.schedule["finish"]["month"]["each"]):
                        stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
                else:
                    stop_date = datetime.date(year=stop_date.year,
                                              month=stop_date.month,
                                              day=self.schedule["finish"]["month"]["day"])
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                self.stop_datetime = datetime.datetime.combine(
                    stop_date,
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))
                return True
        else:
            if self.schedule["finish"]["time"] == "never":
                return False
            else:
                if self.start_datetime is None:
                    start_dt = datetime.date.today()
                else:
                    start_dt = self.start_datetime

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
                                    start_dt,
                                    datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                                stop_day)
                            return True
                        else:
                            stop_day += self.schedule["finish"]["day"]

                    self.stop_datetime = datetime.datetime.combine(
                        start_dt + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))
                    return True
                else:
                    return False

    def try_repeat(self):
        if not self.is_stop:
            now = datetime.datetime.now()
            if now > self.next_repeat:
                if self.repeat["wait_finished"]:
                    if self.job is None:
                        self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                        self.next_repeat = calc_repeat(now, self.repeat)
                    elif self.job.poll() is not None:  # if process is terminated
                        self.next_repeat = calc_repeat(now, self.repeat)
                        self.job = None
                else:
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    self.next_repeat = calc_repeat(now, self.repeat)

    def try_stop_immediately(self):
        if not self.is_start:
            self.is_stop = True

        if not self.is_stop:
            if self.job is None:
                self.is_stop = True
                print("[ Job '" + self.name + "' finished at " + str(datetime.datetime.now()) + " ]")
            elif self.job.poll() is not None:  # if process is terminated
                self.is_stop = True
                print("[ Job '" + self.name + "' finished at " + str(datetime.datetime.now()) + " ]")


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


def is_month(maybe_dow):
    return maybe_dow in MONTHS


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
    if wait_rep_jobs:
        print("Wait repeated jobs finished...")
        is_run = True
        stop_j = [False] * len(jobs_r)
        while is_run:
            i = 0
            for _jr in jobs_r:
                _jr.try_stop_immediately()
                if _jr.is_stop:
                    stop_j[i] = True
                i += 1
            stop_count = 0
            for s_j in stop_j:
                if s_j is True:
                    stop_count += 1
            if stop_count == len(stop_j):
                is_run = False
                continue
            time.sleep(1)
        print()
    exit(1)


try:
    f_name = sys.argv[1]
except IndexError:
    f_name = "psd.json"

if f_name == '':
    f_name = "psd.json"

jobs = []
jobs_r = []

settings = json.load(open(f_name))
if "is_shell" not in settings:
    is_shell = True
else:
    is_shell = settings["is_shell"]
if "wait_repeated_jobs" not in settings:
    error("Field 'wait_repeated_jobs' not found in " + str(f_name) + "!")
else:
    wait_rep_jobs = settings["wait_repeated_jobs"]

working_dir = ""
if "working_dir" in settings:
    working_dir = settings["working_dir"]

for js in settings["jobs"]:
    _when_finished = False
    js_f_name = None
    if "file" in js:
        js_f_name = path.splitext(js["file"])[0]
        js = json.load(open(working_dir + js["file"]))

    if "name" not in js:
        if js_f_name is not None:
            js["name"] = js_f_name
        else:
            error("Field 'name' is not found in job!")
    if "cmd" not in js:
        error("Field 'cmd' is not found in job!\nJob name: " + js["name"])
    if "schedule" not in js:
        error("Field 'schedule' is not found in job!\nJob name: " + js["name"])
    if "start" not in js["schedule"]:
        error("Field 'start' is not found in job{schedule}!\nJob name: " + js["name"])
    if "when_finished" in js["schedule"]["start"]:
        if not isinstance(js["schedule"]["start"]["when_finished"], bool):
            error("Field 'when_finished' in job{schedule{start}} is not bool! Found "
                  + str(js["schedule"]["start"]["day"])
                  + ".\nPossible values:true, false."
                  + "\nJob name: " + js["name"])
        else:
            _when_finished = js["schedule"]["start"]["when_finished"]
    if "day" in js["schedule"]["start"]:
        if isinstance(js["schedule"]["start"]["day"], str):
            if not is_dow(js["schedule"]["start"]["day"]):
                error("Field 'day' in job{schedule{start}} is not days of week! Found "
                      + str(js["schedule"]["start"]["day"])
                      + ".\nPossible values:'mon', 'tue', 'wed', 'thu', 'fri','sat', 'sun'."
                      + "\nJob name: " + js["name"])
        elif not isinstance(js["schedule"]["start"]["day"], int):
            error("Field 'day' in job{schedule{start}} is not int!\nJob name: " + js["name"])
    if "time" not in js["schedule"]["start"]:
        if "month" in js["schedule"]["start"]:
            if isinstance(js["schedule"]["start"]["month"]["values"], list):
                for month in js["schedule"]["start"]["month"]["values"]:
                    if not is_month(month):
                        error("Element of list 'values' in job{schedule{start{month}}} is not month! Found "
                              + str(month)
                              + ".\nPossible values: 'jan', 'feb', 'mar', 'apr', 'may','jun', 'jul', 'aug', 'sep', "
                                "'oct', 'nov', 'dec'.\nJob name: " + js["name"])
            elif not isinstance(js["schedule"]["start"]["month"]["values"], int):
                error("Field 'values' in job{schedule{start{month}}} is not int!\nJob name: " + js["name"])
            if isinstance(js["schedule"]["start"]["month"]["day"], str):
                if not is_dow(js["schedule"]["start"]["month"]["day"]):
                    error("Field 'day' in job{schedule{start{month}}} is not day of week! Found "
                          + str(js["schedule"]["start"]["month"]["day"])
                          + ".\nPossible values: 'mon', 'tue', 'wed', 'thu', 'fri','sat', 'sun'.\nJob name: " + js[
                              "name"])
                if "each" in js["schedule"]["start"]["month"]:
                    if not isinstance(js["schedule"]["start"]["month"]["each"], int):
                        error("Field 'each' in job{schedule{start{month}}} is not int!\nJob name: " + js["name"])
                else:
                    error("Field 'each' is not found in job{schedule{start{month}}}!\nJob name: " + js["name"])
            elif not isinstance(js["schedule"]["start"]["month"]["day"], int):
                error("Field 'day' in job{schedule{start{month}}} is not int!\nJob name: " + js["name"])
            if "time" not in js["schedule"]["start"]["month"]:
                error("Field 'time' is not found in job{schedule{start{month}}}!\nJob name: " + js["name"])
            elif not is_time_format(js["schedule"]["start"]["month"]["time"]):
                error("Field 'time' has wrong pattern! Expected ##:##, actual " + str(
                    js["schedule"]["start"]["month"]["time"]) + "\nJob name: " + js["name"])
        else:
            error("Field 'month' in job{schedule{start}} is not defined! Define 'time' or 'month'\n"
                  "Job name: " + js["name"])
    else:
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
        if "month" in js["schedule"]["finish"]:
            if isinstance(js["schedule"]["finish"]["month"]["values"], str):
                if not is_month(js["schedule"]["finish"]["month"]["values"]):
                    error("Field 'values' in job{schedule{finish{month}}} is not month! Found "
                          + str(js["schedule"]["finish"]["month"]["values"])
                          + ".\nPossible values: 'jan', 'feb', 'mar', 'apr', 'may','jun', 'jul', 'aug', 'sep', "
                            "'oct', 'nov', 'dec'.\nJob name: " + js["name"])
            elif not isinstance(js["schedule"]["finish"]["month"]["values"], int):
                error("Field 'values' in job{schedule{finish{month}}} is not int!\nJob name: " + js["name"])
            if isinstance(js["schedule"]["finish"]["month"]["day"], str):
                if not is_dow(js["schedule"]["finish"]["month"]["day"]):
                    error("Field 'day' in job{schedule{finish{month}}} is not day of week! Found "
                          + str(js["schedule"]["finish"]["month"]["day"])
                          + ".\nPossible values: 'mon', 'tue', 'wed', 'thu', 'fri','sat', 'sun'.\nJob name: " + js[
                              "name"])
                if "each" in js["schedule"]["finish"]["month"]:
                    if not isinstance(js["schedule"]["finish"]["month"]["each"], int):
                        error("Field 'each' in job{schedule{finish{month}}} is not int!\nJob name: " + js["name"])
                else:
                    error("Field 'each' is not found in job{schedule{finish{month}}}!\nJob name: " + js["name"])
            elif not isinstance(js["schedule"]["finish"]["month"]["day"], int):
                error("Field 'day' in job{schedule{finish{month}}} is not int!\nJob name: " + js["name"])
            if "time" not in js["schedule"]["finish"]["month"]:
                error("Field 'time' is not found in job{schedule{finish{month}}}!\nJob name: " + js["name"])
            elif not is_time_format(js["schedule"]["finish"]["month"]["time"]):
                error("Field 'time' has wrong pattern! Expected ##:##, actual " + str(
                    js["schedule"]["finish"]["month"]["time"]) + "\nJob name: " + js["name"])
        else:
            error("Field 'month' in job{schedule{finish}} is not defined! Define 'time' or 'month'\n"
                  "Job name: " + js["name"])
    else:
        if not is_time_format(js["schedule"]["finish"]["time"]):
            if js["schedule"]["finish"]["time"] != "never":
                error("Field 'time' has wrong pattern! Expected ##:##, actual " + str(js["schedule"]["finish"]["time"])
                      + "\nJob name: " + js["name"])

    if "repeat" in js:
        if "unit" not in js["repeat"]:
            error("Field 'unit' is not found in job{repeat}!\nJob name: " + js["name"])
        if "val" not in js["repeat"]:
            error("Field 'val' is not found in job{repeat}!\nJob name: " + js["name"])
        if "wait_finished" not in js["repeat"]:
            error("Field 'wait_finished' is not found in job{repeat}!\nJob name: " + js["name"])

        jobs_r.append(JobRep(
            js["name"],
            js["cmd"],
            js["schedule"],
            is_shell,
            _when_finished,
            js["repeat"]))
    else:
        jobs.append(Job(
            js["name"],
            js["cmd"],
            js["schedule"],
            _when_finished,
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

