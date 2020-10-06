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
from os import environ
from os import path
from os import mkdir

DOW = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,  "fri": 4, "sat": 5, "sun": 6}

MONTHS = {"dec": 12, "jan": 1,  "feb": 2,
          "mar": 3,  "apr": 4,  "may": 5,
          "jun": 6,  "jul": 7,  "aug": 8,
          "sep": 9,  "oct": 10, "nov": 11}

RED = 160
GREEN = 28
BLUE = 44
LIGHT_BLUE = 45
YELLOW = 136
PURPLE = 134

LOG = False
LOG_FOLDER = "logs/"
LOG_PREFIX = "log_"
ENCODING = sys.getdefaultencoding()
DEBUG = False

DEBUG_SECTION_BEGIN = "[BEGIN]"
DEBUG_SECTION_END = "[END]"
DEBUG_BANNER = "[DEBUG]"


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
        self.cmd = cmd.split(" ")
        self.schedule = schedule
        self.is_shell = is_sh
        self.when_finished = when_finished
        self.job = None
        self.start_datetime = None
        self.stop_datetime = None
        self.dt_month = None
        self.init_start_dt()
        self.init_stop_dt()

        try_debug("job: name:" + self.name)
        try_debug("job: cmd:" + str(self.cmd))
        try_debug("job: schedule:" + str(self.schedule))
        try_debug("job: is_shell:" + str(self.is_shell))
        try_debug("job: when_finished:" + str(self.when_finished))
        try_debug("job: start_datetime:" + str(self.start_datetime))
        try_debug("job: stop_datetime:" + str(self.stop_datetime))
        try_debug("job: dt_month:" + str(self.dt_month))

    def init_start_dt(self):
        try_debug("job: '" + self.name + "', section: 'def init_start_dt(self)'", DEBUG_SECTION_BEGIN)
        if self.start_datetime is None:
            if "month" in self.schedule["start"]:
                start_h_m = int_time(self.schedule["start"]["month"]["time"])
                try_debug("job: '" + self.name + "', section: "
                                                 "'if self.start_datetime is None: if 'month' in self.schedule['start']"
                                                 "': start_h_m:" + str(start_h_m))
            else:
                if self.schedule["start"]["time"] == "now":
                    start_h_m = [0, 0]
                    try_debug("job: '" + self.name + "', section: "
                                                     "'if self.schedule['start']['time'] == 'now''"
                                                     ": start_h_m:" + str(start_h_m))
                else:
                    start_h_m = int_time(self.schedule["start"]["time"])
                    try_debug("job: '" + self.name + "', section: "
                                                     "'if self.schedule['start']['time'] == 'now': else: '"
                                                     ": start_h_m:" + str(start_h_m))

            if "month" in self.schedule["finish"]:
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                try_debug("job: '" + self.name + "', section: "
                                                 "'if 'month' in self.schedule['finish']'"
                                                 ": stop_h_m:" + str(stop_h_m))
            else:
                if self.schedule["finish"]["time"] == "never":
                    stop_h_m = [0, 0]
                    try_debug("job: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never'': "
                                                     "stop_h_m:" + str(stop_h_m))
                else:
                    stop_h_m = int_time(self.schedule["finish"]["time"])
                    try_debug("job: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never': else:"
                                                     " ': stop_h_m:" + str(stop_h_m))

            dt_start = datetime.datetime.today()
            dt_actual_start = datetime.datetime(year=dt_start.year,
                                                month=dt_start.month,
                                                day=dt_start.day,
                                                hour=start_h_m[0],
                                                minute=start_h_m[1])
            dt_actual_finish = datetime.datetime(year=dt_start.year,
                                                 month=dt_start.month,
                                                 day=dt_start.day,
                                                 hour=stop_h_m[0],
                                                 minute=stop_h_m[1])

            try_debug("job: '" + self.name + "', section: 'if self.start_datetime is None': dt_start: " + str(dt_start)
                      + ", dt_actual_start: " + str(dt_actual_start) + ", dt_actual_finish: " + str(dt_actual_finish))

            if dt_actual_start > dt_actual_finish:
                dt_actual_finish += timedelta(days=1)
                try_debug("job: '" + self.name + "', section: 'dt_actual_start > dt_actual_finish': dt_actual_finish: "
                          + str(dt_actual_finish))

            if not(dt_actual_start < dt_start < dt_actual_finish):
                if not(dt_start < dt_actual_start and dt_start < dt_actual_finish):
                    dt_start += timedelta(days=1)
                    try_debug("job: '" + self.name +
                              "', section: 'if not(dt_actual_start < dt_start < dt_actual_finish): "
                              "if not(dt_start < dt_actual_start and dt_start < dt_actual_finish): "
                              "dt_actual_finish: " + str(dt_actual_finish))

            if "month" in self.schedule["start"]:
                start_h_m = int_time(self.schedule["start"]["month"]["time"])
                try_debug("job: '" + self.name + "', section: 'if 'month' in self.schedule['start']': "
                                                 "start_h_m: " + str(start_h_m))
                if isinstance(self.schedule["start"]["month"]["values"], list):
                    self.dt_month = DateTimeMonthsJob(dt_start,
                                                      self.schedule["start"]["month"]["values"])
                    start_date = self.dt_month.next_date_time()
                    try_debug("job: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['month']['values'], list)': "
                              "dt_month: " + str(self.dt_month) + ", start_date: " + str(start_date))
                else:
                    start_date = add_months(dt_start, self.schedule["start"]["month"]["values"])
                    try_debug("job: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['month']['values'], list): else: ':"
                              ", start_date: " + str(start_date))
                if isinstance(self.schedule["start"]["month"]["day"], str):
                    for i in range(self.schedule["start"]["month"]["each"]):
                        start_date = next_weekday(start_date, DOW[self.schedule["start"]["month"]["day"]])
                    try_debug("job: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['month']['day'], str)'"
                              ": start_date: " + str(start_date))
                else:
                    start_date = datetime.date(year=start_date.year,
                                               month=start_date.month,
                                               day=self.schedule["start"]["month"]["day"])
                    try_debug("job: '" + self.name
                              + "', section: 'if isinstance(self.schedule['start']['month']['day'], str): else: '"
                                ": start_date: " + str(start_date))
            else:
                if self.schedule["start"]["time"] == "now":
                    try_debug("job: '" + self.name
                              + "', section: 'if self.schedule['start']['time'] == 'now'': return None")
                    return None
                if isinstance(self.schedule["start"]["day"], str):
                    start_date = next_weekday(dt_start, DOW[self.schedule["start"]["day"]])
                    try_debug("job: '" + self.name
                              + "', section: 'if isinstance(self.schedule['start']['day'], str)': "
                                "start_date: " + str(start_date))
                else:
                    start_date = dt_start
                    try_debug("job: '" + self.name
                              + "', section: 'if isinstance(self.schedule['start']['day'], str): else: '"
                                ": start_date: " + str(start_date))

            self.start_datetime = datetime.datetime.combine(
                start_date,
                datetime.time(start_h_m[0], start_h_m[1], 0))

            try_debug("job: '" + self.name + "', section: 'if 'month' in self.schedule['start']: else: '"
                                             ": start_datetime: " + str(self.start_datetime))
        try_debug("job: '" + self.name + "', section: 'def init_start_dt(self)'", DEBUG_SECTION_END)

    def init_stop_dt(self):
        try_debug("job: '" + self.name + "', section: 'def init_stop_dt(self)' [BEGIN]", DEBUG_SECTION_BEGIN)
        if self.start_datetime is None:
            dt_start = datetime.date.today()
            try_debug("job: '" + self.name + "', section: 'if self.start_datetime is None': dt_start: " + str(dt_start))
        else:
            if "month" in self.schedule["finish"]:
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                try_debug("job: '" + self.name + "', section: 'if 'month' in self.schedule['finish']'"
                                                 ": dt_start: " + str(stop_h_m))
            else:
                if self.schedule["finish"]["time"] == "never":
                    stop_h_m = [0, 0]
                    try_debug("job: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never''"
                                                     ": stop_h_m: " + str(stop_h_m))
                else:
                    stop_h_m = int_time(self.schedule["finish"]["time"])
                    try_debug("job: '" + self.name
                              + "', section: 'if self.schedule['finish']['time'] == 'never': else: '"
                                ": stop_h_m: " + str(stop_h_m))

            dt_start = self.start_datetime
            dt_actual_finish = datetime.datetime(year=dt_start.year,
                                                 month=dt_start.month,
                                                 day=dt_start.day,
                                                 hour=stop_h_m[0],
                                                 minute=stop_h_m[1])

            try_debug("job: '" + self.name
                      + "', section: 'if self.start_datetime is None: else: ': dt_start: " +
                      str(dt_start) + ", dt_actual_finish: " + str(dt_actual_finish))

            if dt_start > dt_actual_finish:
                dt_start += timedelta(days=1)
                try_debug("job: '" + self.name + "', " + str(dt_start) + ">" + str(dt_actual_finish))
                try_debug("job: '" + self.name + "', section: 'if dt_start > dt_actual_finish'"
                                                 ": dt_start: " + str(dt_start))
        if "month" in self.schedule["finish"]:
            if isinstance(self.schedule["finish"]["month"]["values"], str):
                stop_date = add_months(dt_start, self.schedule["finish"]["month"]["values"])
                try_debug("job: '" + self.name +
                          "', section: 'if 'month' in self.schedule['finish']: "
                          "if isinstance(self.schedule['finish']['month']['values'], str)'"
                          ": stop_date: " + str(stop_date))
            else:
                stop_date = add_months(dt_start, self.schedule["finish"]["month"]["values"])
                try_debug("job: '" + self.name +
                          "', section: 'if 'month' in self.schedule['finish']: "
                          "if isinstance(self.schedule['finish']['month']['values'], str): else'"
                          ": stop_date: " + str(stop_date))
            if isinstance(self.schedule["finish"]["month"]["day"], str):
                for i in range(self.schedule["finish"]["month"]["each"]):
                    stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
                try_debug("job: '" + self.name +
                          "', section: 'if isinstance(self.schedule['finish']['month']['day'], str)'"
                          ": stop_date: " + str(stop_date))
            else:
                stop_date = datetime.date(year=stop_date.year,
                                          month=stop_date.month,
                                          day=self.schedule["finish"]["month"]["day"])
                try_debug("job: '" + self.name +
                          "', section: 'if isinstance(self.schedule['finish']['month']['day'], str): else: '"
                          ": stop_date: " + str(stop_date))
            stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
            self.stop_datetime = datetime.datetime.combine(
                stop_date,
                datetime.time(stop_h_m[0], stop_h_m[1], 0))
            try_debug("job: '" + self.name +
                      "', section: 'if 'month' in self.schedule['finish']': stop_h_m: " + str(stop_h_m) +
                      ", stop_datetime: " + str(self.stop_datetime))
        else:
            if self.schedule["finish"]["time"] == "never":
                try_debug("job: '" + self.name +
                          "', section: 'if self.schedule['finish']['time'] == 'never'': return None")
                return None

            if self.stop_datetime is None:
                stop_h_m = int_time(self.schedule["finish"]["time"])
                stop_day = 0
                try_debug("job: '" + self.name + "', section: 'if self.stop_datetime is None': stop_h_m: " +
                          str(stop_h_m) + ", stop_day:" + str(stop_day))
                if "day" in self.schedule["finish"]:
                    if isinstance(self.schedule["finish"]["day"], str):
                        stop_day = DOW[self.schedule["finish"]["day"]]
                        self.stop_datetime = next_weekday(
                            datetime.datetime.combine(
                                dt_start,
                                datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                            stop_day)
                        try_debug("job: '" + self.name + "', section: 'if 'day' in self.schedule['finish']': stop_day: "
                                  + str(stop_day) + ", stop_datetime:" + str(self.stop_datetime))
                    else:
                        stop_day = self.schedule["finish"]["day"]
                        self.stop_datetime = datetime.datetime.combine(
                            dt_start + timedelta(days=stop_day),
                            datetime.time(stop_h_m[0], stop_h_m[1], 0))
                        try_debug("job: '" + self.name +
                                  "', section: 'if 'day' in self.schedule['finish']: else: ': stop_day: " +
                                  str(stop_day) + ", stop_datetime:" + str(self.stop_datetime))
                else:
                    self.stop_datetime = datetime.datetime.combine(
                        dt_start + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))
                    try_debug("job: '" + self.name +
                              "', section: 'if 'day' in self.schedule['finish']: else: ': stop_datetime:"
                              + str(self.stop_datetime))
        try_debug("job: '" + self.name + "', section: 'def init_stop_dt(self)'", DEBUG_SECTION_END)

    def try_start(self):  # True - job is running, False - job is not running
        try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_BEGIN)
        if "month" in self.schedule["start"]:
            if self.job is None:
                try_debug("job: '" + self.name + "', section: 'if self.job is None'")
                now = datetime.datetime.now()
                if self.start_datetime <= now <= self.stop_datetime:
                    try_debug("job: '" + self.name +
                              "', section: 'if self.start_datetime <= now <= self.stop_datetime'")
                    try_debug(str(self.start_datetime) + "<=" + str(now) + "<=" + str(self.stop_datetime))
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

                    try_debug("job: " + self.name + "start_date: " + str(start_date))
                    try_debug("job: " + self.name + "start_h_m: " + str(start_h_m))

                    self.start_datetime = datetime.datetime.combine(
                        start_date,
                        datetime.time(start_h_m[0], start_h_m[1], 0))

                    try_debug("job: " + self.name + "start_datetime: " + str(self.start_datetime))

                    if self.when_finished:
                        try_debug("job: " + self.name + "section: start_date: 'if self.when_finished'")

                        if self.start_datetime < self.stop_datetime:
                            try_debug("job: " + self.name + ": " + str(self.start_datetime) + "<" +
                                      str(self.stop_datetime))
                            temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                            month=self.stop_datetime.month,
                                                            day=self.stop_datetime.day)
                            try_debug("job: " + self.name + " temp_start_date: " + temp_start_date)
                            if isinstance(self.schedule["start"]["day"], str):
                                temp_start_date += next_weekday(temp_start_date,
                                                                DOW[self.schedule["start"]["day"]])
                                try_debug("job: " + self.name +
                                          "section: 'if isinstance(self.schedule['start']['day'], str)'"
                                          ": temp_start_date: " + temp_start_date)
                            else:
                                temp_start_date += timedelta(days=self.schedule["start"]["day"])
                                try_debug(
                                    "job: " + self.name +
                                    "section: 'if isinstance(self.schedule['start']['day'], str)': else:"
                                    " temp_start_date: " + temp_start_date)
                            self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                    month=temp_start_date.month,
                                                                    day=temp_start_date.day,
                                                                    hour=self.start_datetime.hour,
                                                                    minute=self.start_datetime.minute,
                                                                    second=self.start_datetime.second)
                            try_debug("job: " + self.name +
                                      "section: 'if self.start_datetime < self.stop_datetime'"
                                      ": start_datetime: " + self.start_datetime)

                    print(start_msg_full(self.name, str(now), self.stop_datetime, self.start_datetime))
                    try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_END)
                    return True
                else:
                    try_debug("job: '" + self.name + "', section: 'if self.start_datetime <= now <= self.stop_datetime'"
                                                     ": return False")
                    try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_END)
                    return False
            else:
                try_debug("job: '" + self.name + "', section: 'if self.job is None': return True")
                try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_END)
                return True
        else:
            if self.schedule["start"]["time"] == "now":
                if self.job is None:
                    try_debug("job: '" + self.name + "', section: 'if self.schedule['start']['time'] == 'now'")
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    print(start_msg_short(self.name, datetime.datetime.now()))
                try_debug("job: '" + self.name + "', section: 'if self.schedule['start']['time'] == 'now''"
                                                 ": return True")
                try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_END)
                return True
            else:
                if self.job is None:
                    try_debug("job: '" + self.name + "', section: 'if self.job is None'")
                    now = datetime.datetime.now()
                    if self.start_datetime <= now <= self.stop_datetime:
                        try_debug("job: '" + self.name +
                                  "', section: 'if self.start_datetime <= now <= self.stop_datetime'")
                        try_debug(str(self.start_datetime) + "<=" + str(now) + "<=" + str(self.stop_datetime))
                        self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                        try_debug("job: '" + self.name + ": " + str(self.job))
                        start_h_m = int_time(self.schedule["start"]["time"])
                        start_day = self.schedule["start"]["day"]
                        start_date = datetime.datetime.now()

                        try_debug("job: '" + self.name + ", start_h_m " + str(start_h_m))
                        try_debug("job: '" + self.name + ", start_day" + str(start_day))
                        try_debug("job: '" + self.name + ", start_date" + str(start_date))

                        if "day" in self.schedule["finish"]:
                            try_debug("job: '" + self.name + "', section: 'if 'day' in self.schedule['finish']'")
                            if isinstance(self.schedule["finish"]["day"], str):
                                start_date = next_weekday(datetime.date.today(), DOW[self.schedule["finish"]["day"]])
                                try_debug("job: '" + self.name +
                                          "', section: 'if 'day' in self.schedule['finish']'"
                                          ": start_date: " + str(start_date))
                            else:
                                start_day += self.schedule["finish"]["day"]
                                try_debug("job: '" + self.name +
                                          "', section: 'if 'day' in self.schedule['finish']': else:"
                                          " start_date: " + str(start_day))
                        self.start_datetime = datetime.datetime.combine(
                            start_date + timedelta(days=start_day),
                            datetime.time(start_h_m[0], start_h_m[1], 0))
                        try_debug("job: '" + self.name + "start_datetime: " + str(self.start_datetime))

                        if self.when_finished:
                            try_debug("job: '" + self.name + "', section: if self.when_finished")
                            if self.start_datetime < self.stop_datetime:
                                temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                                month=self.stop_datetime.month,
                                                                day=self.stop_datetime.day)
                                try_debug("job: '" + self.name +
                                          "', section: 'if self.start_datetime < self.stop_datetime'")
                                try_debug("job: '" + self.name + "', " + str(self.start_datetime) + "<" +
                                          str(self.stop_datetime))

                                if isinstance(self.schedule["start"]["day"], str):
                                    temp_start_date += next_weekday(temp_start_date,
                                                                    DOW[self.schedule["start"]["day"]])
                                    try_debug(
                                        "job: '" + self.name +
                                        "', section: 'if isinstance(self.schedule['start']['day'], str)'"
                                        ": temp_start_date: " + str(temp_start_date))
                                else:
                                    temp_start_date += timedelta(days=self.schedule["start"]["day"])
                                    try_debug("job: '" + self.name +
                                              "', section: 'if isinstance(self.schedule['start']['day'], str)': else:"
                                              " temp_start_date: " + str(temp_start_date))

                                self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                        month=temp_start_date.month,
                                                                        day=temp_start_date.day,
                                                                        hour=self.start_datetime.hour,
                                                                        minute=self.start_datetime.minute,
                                                                        second=self.start_datetime.second)
                                try_debug("job: '" + self.name +
                                          "', section: 'if self.start_datetime < self.stop_datetime'"
                                          ": start_datetime: " + str(self.start_datetime))

                        print(start_msg_full(self.name, str(now), self.stop_datetime, self.start_datetime))
                        try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_END)
                        return True
                    else:
                        try_debug("job: '" + self.name +
                                  "', section: 'if self.start_datetime <= now <= self.stop_datetime': return False")
                        try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_END)
                        return False
                else:
                    try_debug("job: '" + self.name + "', section: 'if self.job is None': return True")
                    try_debug("job: '" + self.name + "', section: 'def try_start(self)'", DEBUG_SECTION_END)
                    return True

    def try_stop(self):  # true - job is finished, false - job is not finished
        try_debug("job: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_BEGIN)
        now = datetime.datetime.now()
        if "month" in self.schedule["finish"]:
            try_debug("job: '" + self.name + "', section: 'if 'month' in self.schedule['finish']'")
            if now > self.stop_datetime:
                try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime'")
                if platform.system() == 'Windows':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.job.pid)])
                    try_debug("job: '" + self.name + "', section: 'if platform.system() == 'Windows'")
                else:
                    self.job.kill()
                    try_debug("job: '" + self.name + "', section: 'if platform.system() == 'Windows': else")
                self.job = None
                try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime', job:" + str(self.job))
                print(stop_msg(self.name, str(now)))

                if isinstance(self.schedule["finish"]["month"]["values"], str):
                    stop_date = add_months(self.stop_datetime, MONTHS[self.schedule["finish"]["month"]["values"]])
                    try_debug("job: '" + self.name +
                              "', section: 'if isinstance(self.schedule['finish']['month']['values'], str)'"
                              ", stop_date:" + str(stop_date))
                else:
                    stop_date = add_months(self.stop_datetime, self.schedule["finish"]["month"]["values"])
                try_debug("job: '" + self.name +
                          "', section: 'if isinstance(self.schedule['finish']['month']['values'], str): else'"
                          ", stop_date:" + str(stop_date))
                if isinstance(self.schedule["finish"]["month"]["day"], str):
                    for i in range(self.schedule["finish"]["month"]["each"]):
                        stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
                        try_debug("job: '" + self.name +
                                  "', section: 'if isinstance(self.schedule['finish']['month']['day'], str)'"
                                  ", stop_date:" + str(stop_date))
                else:
                    stop_date = datetime.date(year=stop_date.year,
                                              month=stop_date.month,
                                              day=self.schedule["finish"]["month"]["day"])
                    try_debug("job: '" + self.name +
                              "', section: 'if isinstance(self.schedule['finish']['month']['day'], str): else'"
                              ", stop_date:" + str(stop_date))
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime', stop_h_m:" + str(stop_h_m))

                self.stop_datetime = datetime.datetime.combine(
                    stop_date,
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))
                try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime'"
                                                 ", stop_datetime:" + str(self.stop_datetime))
                try_debug("job: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                return True
        else:
            if self.schedule["finish"]["time"] == "never":
                try_debug("job: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never''"
                                                 ": return False")
                try_debug("job: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                return False
            else:
                if self.start_datetime is None:
                    start_dt = datetime.date.today()
                    try_debug("job: '" + self.name + "', section: 'if self.start_datetime is None'"
                                                     ": start_dt:" + start_dt)
                else:
                    start_dt = self.start_datetime
                    try_debug("job: '" + self.name + "', section: 'if self.start_datetime is None: else'"
                                                     ": start_dt:" + start_dt)

                if now > self.stop_datetime:
                    try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime'")
                    if platform.system() == 'Windows':
                        try_debug("job: '" + self.name + "', section: 'if platform.system() == 'Windows'")
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.job.pid)])
                    else:
                        try_debug("job: '" + self.name + "', section: 'if platform.system() == 'Windows: else'")
                        self.job.kill()
                    self.job = None
                    try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime': job: " + str(self.job))
                    print(stop_msg(self.name, str(now)))

                    stop_h_m = int_time(self.schedule["finish"]["time"])
                    try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime'"
                                                     ": stop_h_m: " + str(stop_h_m))
                    stop_day = 0
                    if "day" in self.schedule["finish"]:
                        try_debug("job: '" + self.name + "', section: 'if 'day' in self.schedule['finish']'")
                        if isinstance(self.schedule["finish"]["day"], str):
                            stop_day = DOW[self.schedule["finish"]["day"]]
                            try_debug("job: '" + self.name +
                                      "', section: 'if isinstance(self.schedule['finish']['day'], str)'"
                                      ": stop_day: " + stop_day)
                            self.stop_datetime = next_weekday(
                                datetime.datetime.combine(
                                    start_dt,
                                    datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                                stop_day)
                            try_debug("job: '" + self.name +
                                      "', section: 'if isinstance(self.schedule['finish']['day'], str)'"
                                      ": stop_datetime: " + self.stop_datetime)
                            return True
                        else:
                            stop_day += self.schedule["finish"]["day"]
                            try_debug("job: '" + self.name +
                                      "', section: 'if isinstance(self.schedule['finish']['day'], str): else'"
                                      ": stop_day: " + stop_day)

                    self.stop_datetime = datetime.datetime.combine(
                        start_dt + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))
                    try_debug("job: '" + self.name + "', section: 'if 'day' in self.schedule['finish']'"
                                                     ": stop_datetime: " + self.stop_datetime)
                    try_debug("job: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                    return True
                else:
                    try_debug("job: '" + self.name + "', section: 'if now > self.stop_datetime: else': return False")
                    try_debug("job: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                    return False

    def stop_immediately(self):
        try_debug("job: '" + self.name + "', section: 'def stop_immediately(self)", DEBUG_SECTION_BEGIN)
        if self.job is not None:
            if platform.system() == 'Windows':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.job.pid)])
            else:
                self.job.kill()
            print(stop_msg(self.name, str(datetime.datetime.now())))
        try_debug("job: '" + self.name + "', section: 'def stop_immediately(self)", DEBUG_SECTION_END)


class JobRep:
    def __init__(self, name, cmd, schedule, when_finished, is_sh, repeat):
        self.name = name
        self.cmd = cmd.split(" ")
        self.schedule = schedule
        self.when_finished = when_finished
        self.is_shell = is_sh
        self.repeat = repeat
        self.job = None
        self.start_datetime = None
        self.stop_datetime = None
        self.dt_month = None
        self.next_repeat = None
        self.is_start = False
        self.is_stop = False
        self.init_start_dt()
        self.init_stop_dt()

        try_debug("jobRep: name:" + self.name)
        try_debug("jobRep: cmd:" + str(self.cmd))
        try_debug("jobRep: schedule:" + str(self.schedule))
        try_debug("jobRep: is_shell:" + str(self.is_shell))
        try_debug("jobRep: when_finished:" + str(self.when_finished))
        try_debug("jobRep: start_datetime:" + str(self.start_datetime))
        try_debug("jobRep: stop_datetime:" + str(self.stop_datetime))
        try_debug("jobRep: dt_month:" + str(self.dt_month))

    def init_start_dt(self):
        try_debug("jobRep: '" + self.name + "', section: 'def init_start_dt(self)", DEBUG_SECTION_BEGIN)
        if self.start_datetime is None:
            if "month" in self.schedule["start"]:
                start_h_m = int_time(self.schedule["start"]["month"]["time"])
                try_debug("jobRep: '" + self.name + "', section: 'if 'month' in self.schedule['start']'"
                                                    ": start_h_m: " + str(start_h_m))
            else:
                if self.schedule["start"]["time"] == "now":
                    start_h_m = [0, 0]
                    try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['start']['time'] == 'now''"
                                                        ": start_h_m: " + str(start_h_m))
                else:
                    start_h_m = int_time(self.schedule["start"]["time"])
                try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['start']['time'] == 'now': else'"
                                                    ": start_h_m: " + str(start_h_m))
            if "month" in self.schedule["finish"]:
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                try_debug("jobRep: '" + self.name + "', section: 'if 'month' in self.schedule['finish']'"
                                                    ": start_h_m: " + str(stop_h_m))
            else:
                if self.schedule["finish"]["time"] == "never":
                    stop_h_m = [0, 0]
                    try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never''"
                                                        ": start_h_m: " + str(stop_h_m))
                else:
                    stop_h_m = int_time(self.schedule["finish"]["time"])
                    try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never'"
                                                        ": else': start_h_m: " + str(stop_h_m))

            dt_start = datetime.datetime.today()
            dt_actual_start = datetime.datetime(year=dt_start.year,
                                                month=dt_start.month,
                                                day=dt_start.day,
                                                hour=start_h_m[0],
                                                minute=start_h_m[1])
            dt_actual_finish = datetime.datetime(year=dt_start.year,
                                                 month=dt_start.month,
                                                 day=dt_start.day,
                                                 hour=stop_h_m[0],
                                                 minute=stop_h_m[1])
            try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None': "
                                                "dt_start: " + str(dt_start))
            try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None': "
                                                "dt_actual_start: " + str(dt_actual_start))
            try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None': "
                                                "dt_actual_finish: " + str(dt_actual_finish))

            if dt_actual_start > dt_actual_finish:
                dt_actual_finish += timedelta(days=1)
                try_debug("jobRep: '" + self.name + "', section: 'if dt_actual_start > dt_actual_finish'"
                                                    ": dt_actual_finish: " + str(dt_actual_finish))
                try_debug("jobRep: '" + self.name + str(dt_actual_start) + ">" + str(dt_actual_finish))
            if not(dt_actual_start < dt_start < dt_actual_finish):
                if not(dt_start < dt_actual_start and dt_start < dt_actual_finish):
                    dt_start += timedelta(days=1)
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if not(dt_start < dt_actual_start and dt_start < dt_actual_finish)'"
                              ": dt_start: " + str(dt_start))

            if "month" in self.schedule["start"]:
                start_h_m = int_time(self.schedule["start"]["month"]["time"])
                try_debug("jobRep: '" + self.name + "', section: 'if 'month' in self.schedule['start']'"
                                                    ": start_h_m: " + str(start_h_m))
                if isinstance(self.schedule["start"]["month"]["values"], list):
                    self.dt_month = DateTimeMonthsJob(dt_start,
                                                      self.schedule["start"]["month"]["values"])
                    start_date = self.dt_month.next_date_time()
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['month']['values'], list)'"
                              ": dt_month: " + str(self.dt_month) + ", start_date: " + str(start_date))
                else:
                    start_date = add_months(dt_start, self.schedule["start"]["month"]["values"])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['month']['values'], list): else'"
                              ": start_date: " + str(start_date))
                if isinstance(self.schedule["start"]["month"]["day"], str):
                    for i in range(self.schedule["start"]["month"]["each"]):
                        start_date = next_weekday(start_date, DOW[self.schedule["start"]["month"]["day"]])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['month']['day'], str)'"
                              ": start_date: " + str(start_date))
                else:
                    start_date = datetime.date(year=start_date.year,
                                               month=start_date.month,
                                               day=self.schedule["start"]["month"]["day"])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['month']['day'], str): else'"
                              ": start_date: " + str(start_date))
            else:
                if self.schedule["start"]["time"] == "now":
                    try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['start']['time'] == 'now''"
                                                        ": return None")
                    return None
                if isinstance(self.schedule["start"]["day"], str):
                    start_date = next_weekday(dt_start, DOW[self.schedule["start"]["day"]])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['start']['day'], str)'"
                              ": start_date: " + str(start_date))
                else:
                    start_date = dt_start
                    try_debug("jobRep: '" + self.name + "', section: 'if isinstance(self.schedule['start']['day'], str)"
                                                        ": else': start_date: " + str(start_date))
            self.start_datetime = datetime.datetime.combine(
                start_date,
                datetime.time(start_h_m[0], start_h_m[1], 0))
            try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None'"
                                                ": start_datetime: " + str(self.start_datetime))
        try_debug("jobRep: '" + self.name + "', section: 'def init_start_dt(self)", DEBUG_SECTION_END)

    def init_stop_dt(self):
        try_debug("jobRep: '" + self.name + "', section: 'def init_stop_dt(self)", DEBUG_SECTION_BEGIN)
        if self.start_datetime is None:
            dt_start = datetime.date.today()
            try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None'"
                                                ": dt_start: " + str(dt_start))
        else:
            if "month" in self.schedule["finish"]:
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                try_debug("jobRep: '" + self.name + "', section: 'if 'month' in self.schedule['finish']'"
                                                    ": stop_h_m: " + str(stop_h_m))
            else:
                if self.schedule["finish"]["time"] == "never":
                    stop_h_m = [0, 0]
                    try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never''"
                                                        ": stop_h_m: " + str(stop_h_m))
                else:
                    stop_h_m = int_time(self.schedule["finish"]["time"])
                    try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never'"
                                                        ": else': stop_h_m: " + str(stop_h_m))

            dt_start = self.start_datetime
            dt_actual_finish = datetime.datetime(year=dt_start.year,
                                                 month=dt_start.month,
                                                 day=dt_start.day,
                                                 hour=stop_h_m[0],
                                                 minute=stop_h_m[1])

            if dt_start > dt_actual_finish:
                dt_start += timedelta(days=1)
                try_debug("jobRep: '" + self.name +
                          "', section: 'dt_start > dt_actual_finish': dt_start: " + str(dt_start))
                try_debug("jobRep: '" + self.name + "', section: '" + str(dt_start) + ">" + str(dt_actual_finish) +
                          ": dt_start: " + str(dt_start))

            try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None: else': dt_start: " +
                      str(dt_start) + ", dt_actual_finish: " + str(dt_actual_finish))

        if "month" in self.schedule["finish"]:
            if isinstance(self.schedule["finish"]["month"]["values"], str):
                stop_date = add_months(dt_start, self.schedule["finish"]["month"]["values"])
                try_debug("jobRep: '" + self.name +
                          "', section: 'if isinstance(self.schedule['finish']['month']['values'], str)': "
                          "stop_date: " + str(stop_date))
            else:
                stop_date = add_months(dt_start, self.schedule["finish"]["month"]["values"])
                try_debug("jobRep: '" + self.name +
                          "', section: 'if isinstance(self.schedule['finish']['month']['values'], str): else': "
                          "stop_date: " + str(stop_date))
            if isinstance(self.schedule["finish"]["month"]["day"], str):
                for i in range(self.schedule["finish"]["month"]["each"]):
                    stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
                try_debug("jobRep: '" + self.name +
                          "', section: 'if isinstance(self.schedule['finish']['month']['day'], str)'"
                          ": stop_date: " + str(stop_date))
            else:
                stop_date = datetime.date(year=stop_date.year,
                                          month=stop_date.month,
                                          day=self.schedule["finish"]["month"]["day"])
                try_debug("jobRep: '" + self.name +
                          "', section: 'if isinstance(self.schedule['finish']['month']['day'], str): else'"
                          ": stop_date: " + str(stop_date))
            stop_h_m = int_time(self.schedule["finish"]["month"]["time"])

            self.stop_datetime = datetime.datetime.combine(
                stop_date,
                datetime.time(stop_h_m[0], stop_h_m[1], 0))

            try_debug("jobRep: '" + self.name +
                      "', section: 'if 'month' in self.schedule['finish']': stop_date: " + str(stop_h_m) +
                      ", stop_datetime: " + str(self.stop_datetime))
        else:
            if self.schedule["finish"]["time"] == "never":
                try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never'"
                                                    ": return None")
                try_debug("jobRep: '" + self.name + "', section: 'def init_stop_dt(self)", DEBUG_SECTION_END)
                return None

            if self.stop_datetime is None:
                stop_h_m = int_time(self.schedule["finish"]["time"])
                stop_day = 0
                try_debug("jobRep: '" + self.name +
                          "', section: 'if self.schedule['finish']['time'] == 'never': stop_h_m: " + str(stop_h_m))
                if "day" in self.schedule["finish"]:
                    if isinstance(self.schedule["finish"]["day"], str):
                        stop_day = DOW[self.schedule["finish"]["day"]]
                        self.stop_datetime = next_weekday(
                            datetime.datetime.combine(
                                dt_start,
                                datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                            stop_day)
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if isinstance(self.schedule['finish']['day'], str)': stop_day: " +
                                  str(stop_day) + ", stop_datetime: " + str(self.stop_datetime))
                    else:
                        stop_day = self.schedule["finish"]["day"]
                        self.stop_datetime = datetime.datetime.combine(
                            dt_start + timedelta(days=stop_day),
                            datetime.time(stop_h_m[0], stop_h_m[1], 0))
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if isinstance(self.schedule['finish']['day'], str): else': stop_day: " +
                                  str(stop_day) + ", stop_datetime: " + str(self.stop_datetime))
                else:
                    self.stop_datetime = datetime.datetime.combine(
                        dt_start + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if 'day' in self.schedule['finish']: else': stop_datetime: " +
                              str(self.stop_datetime))
        try_debug("jobRep: '" + self.name + "', section: 'def init_stop_dt(self)", DEBUG_SECTION_END)

    def try_start(self):  # True - job is running, False - job is not running
        try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_BEGIN)
        if self.is_stop:
            try_debug("jobRep: '" + self.name + "', section: 'if self.is_stop: return False")
            try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
            return False
        if self.is_start:
            try_debug("jobRep: '" + self.name + "', section: 'if self.is_start: return True")
            try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
            return True
        elif "month" in self.schedule["start"]:
            if self.job is None:
                now = datetime.datetime.now()
                try_debug("jobRep: '" + self.name + "', section: 'if self.job is None': now: " + str(now))
                if self.start_datetime <= now <= self.stop_datetime:
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    self.is_start = True
                    self.next_repeat = calc_repeat(now, self.repeat)
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if self.start_datetime <= now <= self.stop_datetime': job: " +
                              str(self.job) + ", is_start: " + str(self.is_start) + ", next_repeat: " +
                              str(self.next_repeat))
                    try_debug("jobRep: '" + self.name + "', " + str(self.start_datetime) + "<=" + str(now) + "<=" +
                              str(self.stop_datetime))
                    if isinstance(self.schedule["start"]["month"]["values"], list):
                        start_date = self.dt_month.next_date_time()
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if isinstance(self.schedule['start']['month']['values'], list)'"
                                  ": start_date: " + str(start_date))
                    else:
                        start_date = add_months(self.start_datetime, self.schedule["start"]["month"]["values"])
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if isinstance(self.schedule['start']['month']['values'], list): else'"
                                  ": start_date: " + str(start_date))
                    if isinstance(self.schedule["start"]["month"]["day"], str):
                        for i in range(self.schedule["start"]["month"]["each"]):
                            start_date = next_weekday(start_date, DOW[self.schedule["start"]["month"]["day"]])
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if isinstance(self.schedule['start']['month']['day'], str)'"
                                  ": start_date: " + str(start_date))
                    else:
                        start_date = datetime.date(year=start_date.year,
                                                   month=start_date.month,
                                                   day=self.schedule["start"]["month"]["day"])
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if isinstance(self.schedule['start']['month']['day'], str): else'"
                                  ": start_date: " + str(start_date))
                    start_h_m = int_time(self.schedule["start"]["month"]["time"])

                    self.start_datetime = datetime.datetime.combine(
                        start_date,
                        datetime.time(start_h_m[0], start_h_m[1], 0))

                    try_debug("jobRep: '" + self.name +
                              "', section: 'if self.start_datetime <= now <= self.stop_datetime:'"
                              ": start_h_m: " + str(start_h_m) + ", start_datetime: " + str(self.start_datetime))

                    if self.when_finished:
                        if self.start_datetime < self.stop_datetime:
                            temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                            month=self.stop_datetime.month,
                                                            day=self.stop_datetime.day)
                            try_debug("jobRep: '" + self.name +
                                      "', section: 'if self.start_datetime < self.stop_datetime'"
                                      ": temp_start_date: " + str(temp_start_date))
                            if isinstance(self.schedule["start"]["day"], str):
                                temp_start_date += next_weekday(temp_start_date,
                                                                DOW[self.schedule["start"]["day"]])
                                try_debug("jobRep: '" + self.name +
                                          "', section: 'if isinstance(self.schedule['start']['day'], str)'"
                                          ": temp_start_date: " + str(temp_start_date))
                            else:
                                temp_start_date += timedelta(days=self.schedule["start"]["day"])
                                try_debug("jobRep: '" + self.name +
                                          "', section: 'if isinstance(self.schedule['start']['day'], str): else'"
                                          ": temp_start_date: " + str(temp_start_date))
                            self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                    month=temp_start_date.month,
                                                                    day=temp_start_date.day,
                                                                    hour=self.start_datetime.hour,
                                                                    minute=self.start_datetime.minute,
                                                                    second=self.start_datetime.second)
                            try_debug("jobRep: '" + self.name +
                                      "', section: 'if self.start_datetime < self.stop_datetime'"
                                      ": start_datetime: " + str(self.start_datetime))
                    print(start_msg_full(self.name, str(now), self.stop_datetime, self.start_datetime))
                    try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
                    return True
                else:
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if self.start_datetime <= now <= self.stop_datetime': return False")
                    try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
                    return False
            else:
                try_debug("jobRep: '" + self.name + "', section: 'if self.job is None': return True")
                try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
                return True
        else:
            if self.schedule["start"]["time"] == "now":
                if self.job is None:
                    self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if self.schedule['start']['time'] == 'now'': job: " + str(self.job))
                    print(start_msg_short(self.name, datetime.datetime.now()))
                try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
                return True
            else:
                if self.job is None:
                    now = datetime.datetime.now()
                    try_debug("jobRep: '" + self.name + "', section: 'if self.job is None': now: " + str(now))
                    if self.start_datetime <= now <= self.stop_datetime:
                        self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                        self.is_start = True
                        self.next_repeat = calc_repeat(now, self.repeat)
                        start_h_m = int_time(self.schedule["start"]["time"])
                        start_day = self.schedule["start"]["day"]
                        start_date = datetime.datetime.now()
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if self.start_datetime <= now <= self.stop_datetime': job: " +
                                  str(self.job) + ", self.is_start: " + str(self.is_start) +
                                  ", self.next_repeat: " + str(self.next_repeat) + ", start_h_m: " + str(start_h_m) +
                                  ", start_day" + str(start_day) + ", start_date: " + str(start_date))
                        if "day" in self.schedule["finish"]:
                            if isinstance(self.schedule["finish"]["day"], str):
                                start_date = next_weekday(datetime.date.today(), DOW[self.schedule["finish"]["day"]])
                                try_debug("jobRep: '" + self.name +
                                          "', section: 'if isinstance(self.schedule['finish']['day'], str)'"
                                          ": start_date: " + str(start_date))
                            else:
                                start_day += self.schedule["finish"]["day"]
                                try_debug("jobRep: '" + self.name +
                                          "', section: 'if isinstance(self.schedule['finish']['day'], str): else'"
                                          ": start_day: " + str(start_day))
                        self.start_datetime = datetime.datetime.combine(
                            start_date + timedelta(days=start_day),
                            datetime.time(start_h_m[0], start_h_m[1], 0))

                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if self.start_datetime <= now <= self.stop_datetime'"
                                  ": start_datetime: " + str(self.start_datetime))

                        if self.when_finished:
                            if self.start_datetime < self.stop_datetime:
                                temp_start_date = datetime.date(year=self.stop_datetime.year,
                                                                month=self.stop_datetime.month,
                                                                day=self.stop_datetime.day)
                                try_debug("jobRep: '" + self.name +
                                          "', section: 'if self.start_datetime < self.stop_datetime'"
                                          ": temp_start_date: " + str(temp_start_date))
                                if isinstance(self.schedule["start"]["day"], str):
                                    temp_start_date += next_weekday(temp_start_date,
                                                                    DOW[self.schedule["start"]["day"]])
                                    try_debug("jobRep: '" + self.name +
                                              "', section: 'if isinstance(self.schedule['start']['day'], str)'"
                                              ": temp_start_date: " + str(temp_start_date))
                                else:
                                    temp_start_date += timedelta(days=self.schedule["start"]["day"])
                                    try_debug("jobRep: '" + self.name +
                                              "', section: 'if isinstance(self.schedule['start']['day'], str): else'"
                                              ": temp_start_date: " + str(temp_start_date))
                                self.start_datetime = datetime.datetime(year=temp_start_date.year,
                                                                        month=temp_start_date.month,
                                                                        day=temp_start_date.day,
                                                                        hour=self.start_datetime.hour,
                                                                        minute=self.start_datetime.minute,
                                                                        second=self.start_datetime.second)
                                try_debug("jobRep: '" + self.name +
                                          "', section: 'if self.start_datetime < self.stop_datetime'"
                                          ": start_datetime" + str(self.start_datetime))

                        print(start_msg_full(self.name, str(now), self.stop_datetime, self.start_datetime))
                        try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
                        return True
                    else:
                        try_debug("jobRep: '" + self.name +
                                  "', section: 'if self.start_datetime <= now <= self.stop_datetime': return False")
                        try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
                        return False
                else:
                    try_debug("jobRep: '" + self.name + "', section: 'if self.job is None': return True")
                    try_debug("jobRep: '" + self.name + "', section: 'def try_start(self)", DEBUG_SECTION_END)
                    return True

    def try_stop(self):  # true - job is finished, false - job is not finished
        try_debug("jobRep: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_BEGIN)
        if self.is_stop:
            try_debug("jobRep: '" + self.name + "', section: 'if self.is_stop': return True")
            try_debug("jobRep: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
            return True
        if not self.is_start:
            try_debug("jobRep: '" + self.name + "', section: 'if not self.is_start'")
            if self.job.poll() is not None:  # if process is terminated
                self.job = None
                try_debug("jobRep: '" + self.name + "', section: 'if self.job.poll() is not None'"
                                                    ": job: " + str(self.job))
            try_debug("jobRep: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
            return True

        now = datetime.datetime.now()
        if "month" in self.schedule["finish"]:
            try_debug("jobRep: '" + self.name +
                      "', section: 'if 'month' in self.schedule['finish']': now: " + str(now) +
                      ", stop_datetime: " + str(self.stop_datetime))

            if now > self.stop_datetime:
                self.is_start = False
                print(stop_msg(self.name, str(now)))

                if isinstance(self.schedule["finish"]["month"]["values"], str):
                    stop_date = add_months(self.stop_datetime, MONTHS[self.schedule["finish"]["month"]["values"]])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['finish']['month']['values'], str)'"
                              ": stop_date: " + str(stop_date))
                else:
                    stop_date = add_months(self.stop_datetime, self.schedule["finish"]["month"]["values"])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['finish']['month']['values'], str): else'"
                              ": stop_date: " + str(stop_date))
                if isinstance(self.schedule["finish"]["month"]["day"], str):
                    for i in range(self.schedule["finish"]["month"]["each"]):
                        stop_date = next_weekday(stop_date, DOW[self.schedule["finish"]["month"]["day"]])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['finish']['month']['day'], str)'"
                              ": stop_date: " + str(stop_date))
                else:
                    stop_date = datetime.date(year=stop_date.year,
                                              month=stop_date.month,
                                              day=self.schedule["finish"]["month"]["day"])
                    try_debug("jobRep: '" + self.name +
                              "', section: 'if isinstance(self.schedule['finish']['month']['day'], str): else'"
                              ": stop_date: " + str(stop_date))
                stop_h_m = int_time(self.schedule["finish"]["month"]["time"])
                self.stop_datetime = datetime.datetime.combine(
                    stop_date,
                    datetime.time(stop_h_m[0], stop_h_m[1], 0))
                try_debug("jobRep: '" + self.name + "', section: 'if now > self.stop_datetime': stop_h_m " +
                          str(stop_h_m) + ", stop_datetime: " + str(self.stop_datetime))
                try_debug("jobRep: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                return True
        else:
            if self.schedule["finish"]["time"] == "never":
                try_debug("jobRep: '" + self.name + "', section: 'if self.schedule['finish']['time'] == 'never''"
                                                    ": return False")
                try_debug("jobRep: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                return False
            else:
                if self.start_datetime is None:
                    start_dt = datetime.date.today()
                    try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None:'"
                                                        ": start_dt: " + str(start_dt))
                else:
                    start_dt = self.start_datetime
                    try_debug("jobRep: '" + self.name + "', section: 'if self.start_datetime is None: else:'"
                                                        ": start_dt: " + str(start_dt))

                if now > self.stop_datetime:
                    self.is_start = False
                    print(stop_msg(self.name, str(now)))

                    stop_h_m = int_time(self.schedule["finish"]["time"])
                    stop_day = 0

                    try_debug("jobRep: '" + self.name + "', section: 'if now > self.stop_datetime': is_start: " +
                              str(self.is_start) + ", stop_h_m: " + str(stop_h_m) + ", stop_day: " + str(stop_day))
                    if "day" in self.schedule["finish"]:
                        if isinstance(self.schedule["finish"]["day"], str):
                            stop_day = DOW[self.schedule["finish"]["day"]]
                            self.stop_datetime = next_weekday(
                                datetime.datetime.combine(
                                    start_dt,
                                    datetime.time(stop_h_m[0], stop_h_m[1], 0)),
                                stop_day)
                            try_debug("jobRep: '" + self.name +
                                      "', section: 'if isinstance(self.schedule['finish']['day'], str)': stop_day: " +
                                      str(stop_day) + ", stop_datetime: " + str(self.stop_datetime))
                            return True
                        else:
                            stop_day += self.schedule["finish"]["day"]
                            try_debug("jobRep: '" + self.name +
                                      "', section: 'if isinstance(self.schedule['finish']['day'], str): else': "
                                      "stop_day: " + str(stop_day))

                    self.stop_datetime = datetime.datetime.combine(
                        start_dt + timedelta(days=stop_day),
                        datetime.time(stop_h_m[0], stop_h_m[1], 0))
                    try_debug("jobRep: '" + self.name + "', section: 'if now > self.stop_datetime': stop_datetime: " +
                              str(self.stop_datetime))
                    try_debug("jobRep: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                    return True
                else:
                    try_debug("jobRep: '" + self.name + "', section: 'if now > self.stop_datetime: else: '"
                                                        ": return False")
                    try_debug("jobRep: '" + self.name + "', section: 'def try_stop(self)", DEBUG_SECTION_END)
                    return False

    def try_repeat(self):
        try_debug("jobRep: '" + self.name + "', section: 'def try_repeat(self)", DEBUG_SECTION_BEGIN)
        if not self.is_stop:
            if self.is_start:
                now = datetime.datetime.now()
                try_debug("jobRep: '" + self.name + "', section: 'self.is_start': now: " + str(now) + ", next_repeat: "
                          + str(self.next_repeat))
                if now > self.next_repeat:
                    if self.repeat["wait_finished"]:
                        if self.job is None:
                            self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                            self.next_repeat = calc_repeat(now, self.repeat)
                            try_debug("jobRep: '" + self.name + "', section: 'if self.job is None': job: " +
                                      str(self.job) + ", next_repeat: " + str(self.next_repeat))
                        elif self.job.poll() is not None:  # if process is terminated
                            self.next_repeat = calc_repeat(now, self.repeat)
                            self.job = None
                            try_debug("jobRep: '" + self.name + "', section: 'if self.job is None': job: " +
                                      str(self.job) + ", next_repeat: " + str(self.next_repeat))
                    else:
                        self.job = subprocess.Popen(self.cmd, shell=self.is_shell)
                        self.next_repeat = calc_repeat(now, self.repeat)
                        try_debug("jobRep: '" + self.name + "', section: 'if self.repeat['wait_finished']: else': job: "
                                  + str(self.job) + ", next_repeat: " + str(self.next_repeat))
        try_debug("jobRep: '" + self.name + "', section: 'def try_repeat(self)", DEBUG_SECTION_END)

    def try_stop_immediately(self):
        try_debug("jobRep: '" + self.name + "', section: 'def try_stop_immediately(self)", DEBUG_SECTION_BEGIN)
        if not self.is_start:
            self.is_stop = True
            try_debug("jobRep: '" + self.name + "', section: 'if not self.is_start': is_stop: " + str(self.is_stop))

        if not self.is_stop:
            if self.job is None:
                self.is_stop = True
                print(stop_msg(self.name, datetime.datetime.now()))
                try_debug("jobRep: '" + self.name + "', section: 'if not self.is_stop: if self.job is None': is_stop: "
                          + str(self.is_stop))
            elif self.job.poll() is not None:  # if process is terminated
                self.is_stop = True
                print(stop_msg(self.name, datetime.datetime.now()))
                try_debug("jobRep: '" + self.name + "', section: 'if not self.is_stop: if self.job is None: else': "
                                                    "is_stop: " + str(self.is_stop))
        try_debug("jobRep: '" + self.name + "', section: 'def try_stop_immediately(self)", DEBUG_SECTION_END)


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


def compatible_shell():
    if "aterm" in environ["SHELL"].lower():
        return False
    elif "rxvt" in environ["SHELL"].lower():
        return False
    elif "tilda" in environ["SHELL"].lower():
        return False
    elif "xvt" in environ["SHELL"].lower():
        return False
    elif "tty" in environ["SHELL"].lower():
        return False
    else:
        return True


def start_msg_full(job_name, started_dt, stop_dt, next_dt):
    if LOG:
        log("[STARTED ] ['" + str(job_name) + "'] [Started: " +
            str(started_dt) + "] [Finished: " + str(stop_dt) +
            "] [Next start: " + str(next_dt) + "]")

    if platform.system() == "Linux":
        if compatible_shell():
            return color_msg(GREEN, "[STARTED ]") + " ['" + str(job_name) + "']" + " " + \
                   color_msg(BLUE, "[Started: " + str(started_dt) + "]") + " " + \
                   color_msg(YELLOW, "[Finished: " + str(stop_dt) + "]") + " " + \
                   color_msg(GREEN, "[Next start: " + str(next_dt) + "]")
    return "[STARTED ] ['" + str(job_name) + "'] [Started: " +\
           str(started_dt) + "] [Finished: " + str(stop_dt) +\
           "] [Next start: " + str(next_dt) + "]"


def start_msg_short(job_name, started_dt):
    if LOG:
        log("[STARTED ] ['" + str(job_name) + "'] [Started: " + str(started_dt) + "]")

    if platform.system() == "Linux":
        if compatible_shell():
            return color_msg(GREEN, "[STARTED ]") + " ['" + str(job_name) + "']" + " " + \
                   color_msg(BLUE, "[Started: " + str(started_dt) + "]")
    return "[STARTED ] ['" + str(job_name) + "'] [Started: " + str(started_dt) + "]"


def stop_msg(job_name, stop_dt):
    if LOG:
        log("[FINISHED] ['" + job_name + "'] [Finished: " + str(stop_dt) + "]")

    if platform.system() == "Linux":
        if compatible_shell():
            return color_msg(YELLOW, "[FINISHED]") + " ['" + str(job_name) + "']" + " " + \
                   color_msg(YELLOW, "[Finished: " + str(stop_dt) + "]")
    return "[FINISHED] ['" + job_name + "'] [Finished: " + str(stop_dt) + "]"


def color_msg(color, msg):
    return "\033[38;5;" + str(color) + "m" + msg + "\033[0m"


def log(message):
    log_filename = LOG_FOLDER + LOG_PREFIX + str(datetime.date.today())
    new_line = "\n"
    if platform.system() == 'Windows':
        new_line = "\r\n"
    with open(log_filename, 'a', encoding=ENCODING) as lg_file:
        lg_file.write(message + new_line)
        lg_file.close()


def debug(message, section=''):
    debug_banner = DEBUG_BANNER
    debug_msg = debug_banner + " " + message + " " + section
    if LOG:
        log(DEBUG_BANNER + " " + message)
    if platform.system() == "Linux":
        if compatible_shell():
            debug_banner = color_msg(LIGHT_BLUE, DEBUG_BANNER)
            if section == DEBUG_SECTION_BEGIN:
                color_section = color_msg(PURPLE, DEBUG_SECTION_BEGIN)
            elif section == DEBUG_SECTION_END:
                color_section = color_msg(PURPLE, DEBUG_SECTION_END)
            else:
                color_section = ''
            debug_msg = debug_banner + " " + message + " " + color_section
    print(debug_msg)


def try_debug(message, section=''):
    if DEBUG:
        debug(message, section)


def error(message):
    if LOG:
        log(message)

    if compatible_shell():
        print(color_msg(RED, message))
    else:
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


working_path = path.realpath(__file__)[:-6]  # remove psd.py

f_name = None
if len(sys.argv) == 1:
    f_name = working_path + "psd.json"
else:
    for arg in sys.argv:
        if arg == "psd.py":
            continue
        if arg == '--debug':
            DEBUG = True
        else:
            f_name = arg

if f_name is None:
    f_name = working_path + "psd.json"
if f_name == '':
    f_name = working_path + "psd.json"

try_debug("debug mode on")
try_debug("working_path: '" + working_path + "'")
try_debug("f_name: " + f_name)

jobs = []
jobs_r = []

settings = json.load(open(f_name, encoding=ENCODING))
if "is_shell" not in settings:
    is_shell = True
else:
    is_shell = settings["is_shell"]
try_debug("is_shell: " + str(is_shell))
if "wait_repeated_jobs" not in settings:
    error("Field 'wait_repeated_jobs' not found in " + str(f_name) + "!")
else:
    wait_rep_jobs = settings["wait_repeated_jobs"]
    try_debug("wait_repeated_jobs: " + str(wait_rep_jobs))

working_dir = working_path
if "working_dir" in settings:
    working_dir = settings["working_dir"]
try_debug("working_dir: " + working_dir)

if "encoding" in settings:
    ENCODING = settings["encoding"]
try_debug("encoding: " + ENCODING)

if "log" in settings:
    LOG = settings["log"]["enabled"]
    if "folder" in settings["log"]:
        LOG_FOLDER = settings["log"]["folder"]
    if "prefix" in settings["log"]:
        LOG_PREFIX = settings["log"]["prefix"]

    try_debug("log: " + str(LOG))
    try_debug("log_folder: " + LOG_FOLDER)
    try_debug("log_prefix: " + LOG_PREFIX)

    if LOG:
        if not path.isdir(LOG_FOLDER):
            try:
                mkdir(LOG_FOLDER)
            except OSError:
                error("Creation of the log directory '" + LOG_FOLDER + "' failed")
            else:
                print("The log directory '" + LOG_FOLDER + "' is created.")
                try_debug("log_folder: " + LOG_FOLDER)

for js in settings["jobs"]:
    _when_finished = False
    js_f_name = None
    if "file" in js:
        js_f_name = path.splitext(js["file"])[0]
        js = json.load(open(working_dir + js["file"], encoding=ENCODING))

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
