# psd
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
  "jobs": [
    {
      "name": "ping1",
      "cmd": "ping 8.8.8.8",
      "schedule": {
        "start": {
          "time": "18:39",
          "day": 1
        },
        "finish": {
          "time": "18:40"
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
        "val": 1
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
    }
  ]
}
```

Fields description:<br>
<code>*</code> - field required.
- <code>"is_shell"</code>: through the shell or not [(what is it?)](https://docs.python.org/3/library/subprocess.html#frequently-used-arguments).
                           Default value - <code>true</code>.
- <code>*"jobs"</code>: the list that contains jobs:
    - <code>*"name"</code>: job name;
    - <code>*"cmd"</code>: command for job;
    - <code>*"schedule"</code>: contains information about job's start and finish:
        - <code>*"start"</code>: contains information about job's start:
            - <code>*"time"</code>: job start time. Possible values:
                1) Time in format <code>"hh:MM"</code>;
                2) <code>"now"</code>: start job now.
            - <code>"day"</code>: - the number of days after which it is necessary to start the job, after it's 
                                    completion. Or day of week when job is started [(values)](#days-of-week-values). 
                                    If <code>"time"</code> has value <code>"now"</code>, then this field is optional.
        - <code>*"finish"</code>: contains information about job's finish:
            - <code>*"time"</code>: job finished time. Possible values:
                1) Time in format <code>"hh:MM"</code>;
                2) <code>"never"</code>: never finished job.
            - <code>"day"</code>: - the number of days indicating how many days the job must be completed.
                                    Or day of week when job is finished [(values)](#days-of-week-values).
                                    If <code>"time"</code> has value <code>"never"</code>, then this field is optional.
    - <code>"repeat"</code>: contains information about job's repeated when it's must be repeated throughout its 
                             execution. It is suitable for jobs that are performed once:
        - <code>"unit"</code> - repeat time unit. Possible values:
            1) <code>"s"</code> - seconds;
            2) <code>"m"</code> - minutes;
            3) <code>"h"</code> - hours.
        - <code>"val"</code> - repeat time value.

# Days of week values
1) <code>"mon"</code> - Monday;
2) <code>"tue"</code> - Tuesday;
3) <code>"wed"</code> - Wednesday;
4) <code>"thu"</code> - Thursday;
5) <code>"fri"</code> - Friday;
6) <code>"sat"</code> - Saturday;
7) <code>"sun"</code> - Sunday.

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
