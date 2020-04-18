# psd
Simple python script scheduler.

Usage
-----
- Linux:
<pre>python psd.py true</pre>
- Windows (PowerShell):
<pre>python.exe psd.py false</pre>
- Windows (cmd):
<pre>python.exe psd.py false</pre>

Parameters
----------
psd.py <1>
1) <1> - Through the shell or not [(what is it?)](https://docs.python.org/3/library/subprocess.html#frequently-used-arguments)

psd.json
--------
This file contains all about jobs. Place in the same directory as psd.py.<br>
File contents:
<pre>
{
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
    }
  ]
}
</pre>

Fields description:<br>
<code>*</code> - Field required.
- <code>*"jobs"</code>: the list that contains task;
    - <code>*"name"</code>: job name;
    - <code>*"cmd"</code>: command for job;
    - <code>*"schedule"</code>: contains information about job's start and finish:
        - <code>*"start"</code>: contains information about job's start:
            - <code>*"time"</code>: Task start time. Possible values:
                1) Time in format <code>"hh:MM"</code>;
                2) <code>"now"</code>: Start job now.
            - <code>"day"</code>: - The number of days after which it is necessary to start the job, after it's 
                                    completion. If <code>"time"</code> has value <code>"now"</code>, then this field is 
                                    optional.
        - <code>*"finish"</code>: contains information about job's finish:
            - <code>*"time"</code>: Task finished time. Possible values:
                1) Time in format <code>"hh:MM"</code>;
                2) <code>"never"</code>: Never finished job.
            - <code>"day"</code>: - The number of days indicating how many days the job must be completed.
            If <code>"time"</code> has value <code>"never"</code>, then this field is optional.
    - <code>"repeat"</code>: contains information about job's repeated when it's must be repeated throughout its 
                             execution. It is suitable for jobs that are performed once:
        - <code>"unit"</code> - Repeat time unit. Possible values:
            1) <code>"s"</code> - seconds;
            2) <code>"m"</code> - minutes;
            3) <code>"h"</code> - hours.
        - <code>"val"</code> - Repeat time value.

Example
-------
<pre>
$ python psd.py true   
[ Schedule started at 2020-04-09 21:56:55.908238 ]
[ Job 'ping' started at 2020-04-09 21:56:55.908286 ]
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=43 time=153 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=43 time=177 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=43 time=201 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=43 time=224 ms
64 bytes from 8.8.8.8: icmp_seq=5 ttl=43 time=145 ms
[ Job 'ping' finished at + 2020-04-09 21:57:00.962440 ]
[ Job 'ls' started at 2020-04-09 21:58:55.968286 ]
LICENSE psd.json psd.py README.md
</pre>
