# psd
Simple python script scheduler for one task.

Usage
-----
- Linux:
<pre>python psd.py 'your task here' 7 50 23 50 1 true</pre>
- Windows (PowerShell):
<pre>python.exe psd.py 'your task here' 7 50 23 50 1 false</pre>
- Windows (cmd):
<pre>python.exe psd.py "your task here" 7 50 23 50 1 false</pre>

Parameters
----------
psd.py <1> <2> <3> <4> <5> <6> <7>
1) <1> - Your task, for example 'ping 8.8.8.8'
2) <2> - Task start hour
3) <3> - Task start minutes
4) <4> - Task stop hour
5) <5> - Task stop minutes
6) <6> - After how many days need to repeat the task
7) <7> - Through the shell or not [(what is it?)](https://docs.python.org/3/library/subprocess.html#frequently-used-arguments)

In this way, this command <code>python psd.py 'ping 8.8.8.8' 7 50 23 50 1 true</code> means the following:</br>
start command 'ping 8.8.8.8' today at 7:50 am, finish command today at 23:50, run again this task tommorow (today + 1 day) at the same time, through the shell. 

Example
-------
<pre>
$ python psd.py 'ping 8.8.8.8' 21 56 21 57 1 true   
[ Schedule started at 2020-04-09 21:56:55.908238 ]
[ Job: ping 8.8.8.8 ]
[ Start time: 21:56 ]
[ Stop time:  21:57 ]
[ Repeat every 1 days ]
[ Through the shell: True ]
[ Waiting for job starting... ]
[ Job started at 2020-04-09 21:56:55.908286 ]
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=43 time=153 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=43 time=177 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=43 time=201 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=43 time=224 ms
64 bytes from 8.8.8.8: icmp_seq=5 ttl=43 time=145 ms
[ Job finished at + 2020-04-09 21:57:00.962440 ]
</pre>
