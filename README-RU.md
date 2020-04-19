# psd
Простой планировщик заданий на python.

Использование
-------------
- Linux:
<pre>python psd.py settings.json</pre>
- Windows (PowerShell):
<pre>python.exe psd.py settings.json</pre>
- Windows (cmd):
<pre>python.exe psd.py settings.json</pre>

Параметры
---------
psd.py <1>
1) <1> - Файл планировщика. Если не указан, то используется psd.json.

psd.json
--------
Этот файл содержит всю информация о задачах. Поместите его в ту же директорию, что и скрипт psd.py.<br>
Содержимое файла:
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

Описание полей:<br>
<code>*</code> - обязательное поле.
- <code>"is_shell"</code>: запуск через оболочку или нет [(что это?)](https://docs.python.org/3/library/subprocess.html#frequently-used-arguments).
                           Значение по умолчанию - <code>true</code>.
- <code>*"jobs"</code>: список задач:
    - <code>*"name"</code>: имя задачи;
    - <code>*"cmd"</code>: команда задачи;
    - <code>*"schedule"</code>: содержит информацию о начале и завершении задачи:
        - <code>*"start"</code>: содержит информацию о начале задачи:
            - <code>*"time"</code>: время начала задачи. Возможные значения:
                1) Время в формате <code>"hh:MM"</code>;
                2) <code>"now"</code>: задача начнется немедленно.
            - <code>"day"</code>: - количество дней, через которые необходимо начать задачу, после ее завершения. 
                                    Или день недели начала задачи [(значения)](#значения-дней-недели). 
                                    Если <code>"time"</code> имеет значение <code>"now"</code>, то это поле не 
                                    обязательно.
        - <code>*"finish"</code>: содержит информацию о завершении задачи:
            - <code>*"time"</code>: время завершения задачи. Возможные значения:
                1) Время в формате <code>"hh:MM"</code>;
                2) <code>"never"</code>: никогда не завершать задачу.
            - <code>"day"</code>: - количество дней, показывающих, сколько дней должна выполняться задача.
                                    Или день недели завершения задачи [(значения)](#значения-дней-недели).
                                    Если <code>"time"</code> имеет значение <code>"never"</code>, то это поле не 
                                    обязательно.
    - <code>"repeat"</code>: содержит информацию о повторении задачи после ее начала. Это подходит для задач, которые 
                             запускаются единожды:
        - <code>"unit"</code> - единица измерения времени повторения. Возможные значения:
            1) <code>"s"</code> - секунды;
            2) <code>"m"</code> - минуты;
            3) <code>"h"</code> - часы.
        - <code>"val"</code> - значение времени повторения задачи.

# Значения дней недели
1) <code>"mon"</code> - Понедельник;
2) <code>"tue"</code> - Вторник;
3) <code>"wed"</code> - Среда;
4) <code>"thu"</code> - Четверг;
5) <code>"fri"</code> - Пятница;
6) <code>"sat"</code> - Суббота;
7) <code>"sun"</code> - Воскресенье.

Пример
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
