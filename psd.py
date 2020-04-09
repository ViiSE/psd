import datetime
import subprocess
import sys
import time
import platform
import os
import signal
from datetime import timedelta

global job

job_prg = str(sys.argv[1])
start_hour = int(sys.argv[2])
start_minutes = int(sys.argv[3])
stop_hour = int(sys.argv[4])
stop_minutes = int(sys.argv[5])
day_count = int(sys.argv[6])
isShell = sys.argv[7].lower() == 'true'

start_date_time = datetime.datetime.combine(datetime.date.today(), datetime.time(start_hour, start_minutes, 0))
stop_date_time = datetime.datetime.combine(datetime.date.today(), datetime.time(stop_hour, stop_minutes, 0))

print("[ Schedule started at " + str(datetime.datetime.now()) + " ]")
print("[ Job: " + job_prg + " ]")
print("[ Start time: " + str(start_hour) + ":" + str(start_minutes) + " ]")
print("[ Stop time:  " + str(stop_hour) + ":" + str(stop_minutes) + " ]")
print("[ Repeat every " + str(day_count) + " days ]")
print("[ Through the shell: " + str(isShell) + " ]")
print("[ Waiting for job starting... ]")

while True:
    now = datetime.datetime.now()
    if now > start_date_time:
        job = subprocess.Popen(job_prg, shell=isShell)
        print("[ Job started at " + str(now) + " ]")
        # Calculate new start date
        next_start_day_job = datetime.date.today() + timedelta(days=day_count)
        start_date_time = datetime.datetime.combine(next_start_day_job, datetime.time(start_hour, start_minutes, 0))

    if now > stop_date_time:
        if platform.system() == 'Windows':
            subprocess.call(['taskkill', '/F', '/T', '/PID',  str(job.pid)])
        else:
            job.kill()
        print("[ Job stopped at + " + str(now) + " ]")
        # Calculate new stop date
        next_stop_day_job = datetime.date.today() + timedelta(days=day_count)
        stop_date_time = datetime.datetime.combine(next_stop_day_job, datetime.time(stop_hour, stop_minutes, 0))
    time.sleep(1)
