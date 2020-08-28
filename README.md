# <img src=psd_logo.png weight="64" height="64"/> psd
Simple python script scheduler.

Usage
-----
- Linux:
<pre>python psd.py settings.json</pre>
- Windows (PowerShell):
<pre>python.exe psd.py settings.json</pre>
- Windows (cmd):
<pre>python.exe psd.py settings.json</pre>

Parameters
----------
psd.py <1>
1) <1> - Settings file. If not specified, then value is psd.json.

psd.json
--------
This file contains all about jobs. Place in the same directory as psd.py.<br>
File contents:
```json
{
  "is_shell": true,
  "wait_repeated_jobs": true,
  "working_dir": "/home/user/psd/",
  "jobs": [
    {
      "name": "ping1",
      "cmd": "ping 8.8.8.8",
      "schedule": {
        "start": {
          "time": "13:48",
          "day": 1
        },
        "finish": {
          "time": "18:41"
        }
      }
    },
    {
      "name": "ping2",
      "schedule": {
        "start": {
          "time": "now"
        },
        "finish": {
          "time": "never"
        }
      },
      "cmd": "ping 8.8.8.8"
    },
    {
      "name": "ls",
      "cmd": "ls",
      "schedule": {
        "start": {
          "time": "18:00",
          "day": 1
        },
        "finish": {
          "time": "18:50",
          "day": 2
        }
      },
      "repeat": {
        "unit": "m",
        "val": 1,
        "wait_finished": true
      }
    },
    {
      "name": "ls_2",
      "cmd": "ls",
      "schedule": {
        "start": {
          "time": "18:00",
          "day": "mon"
        },
        "finish": {
          "time": "18:50",
          "day": "wed"
        }
      }
    },
    {
      "name": "ls_3",
      "cmd": "ls",
      "schedule": {
        "start": {
          "month": {
            "values": ["jan", "may"],
            "day": "wed",
            "each": 2,
            "time": "18:00"
          }
        },
        "finish": {
          "month": {
            "values": 1,
            "day": 10,
            "time": "17:00"
          }
        }
      }
    },
    {
      "name": "ls_4",
      "cmd": "ls",
      "schedule": {
        "start": {
          "month": {
            "values": 1,
            "day": 23,
            "time": "15:00"
          }
        },
        "finish": {
          "month": {
            "values": "jan",
            "day": "wed",
            "each": 2,
            "time": "18:00"
          }
        }
      }
    },
    {
      "name": "ls_5",
      "cmd": "ls",
      "schedule": {
        "start": {
          "time": "18:40",
          "day": 1,
          "when_finished": true
        },
        "finish": {
          "month": {
            "values": 1,
            "day": 10,
            "time": "17:00"
          }
        }
      }
    },
    {
      "name": "ls_6",
      "cmd": "ls",
      "schedule": {
        "start": {
          "time": "18:40",
          "day": 1,
          "when_finished": true
        },
        "finish": {
          "month": {
            "values": "jan",
            "day": "wed",
            "each": 2,
            "time": "18:00"
          }
        }
      }
    },
    {
      "file": "whoami.json"
    }
  ]
}
```

Fields description:<br>
<code>*</code> - field required.
- <code>"is_shell"</code>: through the shell or not [(what is it?)](https://docs.python.org/3/library/subprocess.html#frequently-used-arguments).
                           Default value - <code>true</code>.
- <code>*"wait_repeated_jobs"</code>: wait to completing repeated jobs or not if psd get SIGINT signal 
                                      (ctrl+C, for example). <code>true</code> - wait, <code>false</code> - finished psd
                                      immediately.
- <code>*"working_dir"</code>: directory where task files are located. The default value is the directory from which psd
                               run.
- <code>*"jobs"</code>: the list that contains jobs:
    - <code>*"name"</code>: job name;
    - <code>*"cmd"</code>: command for job;
    - <code>*"schedule"</code>: contains information about job's start and finish:
        - <code>*"start"</code>: contains information about job's start:
            - <code>"time"</code>: job start time. Possible values:
                1) Time in format <code>"hh:MM"</code>;
                2) <code>"now"</code>: start job now.
                If <code>"start"</code> has field <code>"month"</code>, then this field is optional.
            - <code>"day"</code>: - the number of days after which it is necessary to start the job, after it's 
                                    completion. Or day of week when job is started [(values)](#days-of-week-values). 
                                    If <code>"time"</code> has value <code>"now"</code> or <code>"start"</code> has 
                                    field <code>"month"</code>, then this field is optional.
            - <code>"month"</code>: - job start month:
                 - <code>*"values"</code>: - the number of months which is necessary to start the job, after it's 
                                             completion. 
                                             Or list of months when job is started [(values)](#months-values).
                                             Job will start from the specified first month, then from the second, 
                                             and so on. When psd reaches the end of list, it will start from the first 
                                             month in list.
                 - <code>*"day"</code>: - the number of days after which it is necessary to start the job, after it's 
                                          completion. 
                                          Or day of week when job is started [(values)](#days-of-week-values).  
                 - <code>"each"</code>: - number of day of week of the month. <code>"day"</code> must be day of week. 
                 - <code>*"time"</code>: job start time in format <code>"hh:MM"</code>.
            - <code>"when_finished"</code>: - if the date of the next job start is before job finish date, then you can
                                              specify this parameter in order to calculate the next start of job started
                                              on the date job was completed. 
                                              Default value - <code>false</code>.
        - <code>*"finish"</code>: contains information about job's finish:
            - <code>"time"</code>: job finished time. Possible values:
                1) Time in format <code>"hh:MM"</code>;
                2) <code>"never"</code>: never finished job.
                If <code>"finish"</code> has field <code>"month"</code>, then this field is optional.
            - <code>"day"</code>: - the number of days indicating how many days the job must be completed.
                                    Or day of week when job is finished [(values)](#days-of-week-values).
                                    If <code>"time"</code> has value <code>"now"</code> or <code>"finish"</code> has 
                                    field <code>"month"</code>, then this field is optional.
            - <code>"month"</code>: - job finished month:
                 - <code>*"values"</code>: - the number of months indicating how many months the job must be completed.
                                             Or month when job is finished [(values)](#months-values).
                 - <code>*"day"</code>: - the number of days indicating how many days the job must be completed. 
                                          Or day of week when job is finished [(values)](#days-of-week-values).  
                 - <code>"each"</code>: - number of day of week of the month. <code>"day"</code> must be day of week. 
                 - <code>*"time"</code>: job finished time in format <code>"hh:MM"</code>.
            
    - <code>"repeat"</code>: contains information about job's repeated when it's must be repeated throughout its 
                             execution. It is suitable for jobs that are performed once:
        - <code>"unit"</code> - repeat time unit. Possible values:
            1) <code>"s"</code> - seconds;
            2) <code>"m"</code> - minutes;
            3) <code>"h"</code> - hours.
        - <code>"val"</code> - repeat time value.
        - <code>"wait_finished"</code> - wait to finished job before as repeating job. If <code>true</code>, then job is
                                         repeat after job finished, plus repeat time value. If <code>false</code>, then
                                         repeat after repeat time value.

## Job in file
Jobs can be defined in separate files. To do this, define the job in the jobs list as:
```json
{
  "file": "whoami.json"
}
```
File whoami.json:
```json
{
  "cmd": "whoami",
  "schedule": {
    "start": {
      "time": "12:00",
      "day": 1
    },
    "finish": {
      "time": "18:50",
      "day": "wed"
    }
  },
  "repeat": {
    "unit": "s",
    "val": 10,
    "wait_finished": false
  }
}
```
You can ignore field <code>"name"</code> in job file. In this case, job will have a name as file without extension.

If <code>"working_dir"</code> is defined in settings file, then the full file name is optional.

## Days of week values
1) <code>"mon"</code> - Monday;
2) <code>"tue"</code> - Tuesday;
3) <code>"wed"</code> - Wednesday;
4) <code>"thu"</code> - Thursday;
5) <code>"fri"</code> - Friday;
6) <code>"sat"</code> - Saturday;
7) <code>"sun"</code> - Sunday.

## Months values
1) <code>"jan"</code> - January;
2) <code>"feb"</code> - February;
3) <code>"mar"</code> - March;
4) <code>"apr"</code> - April;
5) <code>"may"</code> - May;
6) <code>"jun"</code> - June;
7) <code>"jul"</code> - July;
8) <code>"aug"</code> - August;
9) <code>"sep"</code> - September;
10) <code>"oct"</code> - October;
11) <code>"nov"</code> - November;
12) <code>"dec"</code> - December.


Example
-------
```shell script
$ python psd.py psd.json 
[ Schedule started at 2020-04-19 14:06:30.110551 ]
[ Job 'ping2' started at 2020-04-19 14:06:30.110607. Finished in: 2020-04-19 14:07:00. Next start: 2020-04-21 14:06:00 ]
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=35 time=211 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=35 time=234 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=35 time=154 ms
[ Job 'ping2' finished at 2020-04-19 14:07:00.147956 ]
[ Job 'ls' started at 2020-04-19 14:07:35.836019. Finished in: 2020-04-22 14:08:00. Next start: 2020-04-23 14:07:00 ]
LICENSE  psd.json  psd.py  README.md
LICENSE  psd.json  psd.py  README.md
```
