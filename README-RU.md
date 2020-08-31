# <img src=psd_logo.png weight="64" height="64"/> psd
Простой планировщик задач на python.

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

Описание полей:<br>
<code>*</code> - обязательное поле.
- <code>"is_shell"</code>: запуск через оболочку или нет [(что это?)](https://docs.python.org/3/library/subprocess.html#frequently-used-arguments).
                           Значение по умолчанию - <code>true</code>.
- <code>*"wait_repeated_jobs"</code>: ждать завершения повторяющейся задачи или нет, когда psd получает SIGINT сигнал 
                                      (например, ctrl+C). <code>true</code> - ждать, <code>false</code> - завершить psd
                                      немедленно.
- <code>*"working_dir"</code>: директория, в которой находятся файлы задач. Значение по умолчанию - директория, из 
                                           которой запускается скрипт.
- <code>"encoding"</code>: кодировка для атрибута <code>"file"</code>. Значение по умолчанию - текущая кодировка ОС.
- <code>"log"</code>: лог psd, записывающий весь терминальный вывод в файлы. Формат файла: 
                      <code>LOG_PREFIX_yyyy-mm-dd</code>:
    - <code>"enabled"</code>: - включен лог или нет. Значение по умолчанию - <code>false</code>.
    - <code>"prefix"</code>: - префикс файла лога. Значение по умолчанию - <code>"log_"</code>.
    - <code>"folder"</code>: - папка лога, где находятся файлы лога. Значение по умолчанию - папка <code>logs/</code> в
                               текущей директории. 
- <code>*"jobs"</code>: список задач:
    - <code>*"name"</code>: имя задачи;
    - <code>*"cmd"</code>: команда задачи;
    - <code>*"schedule"</code>: содержит информацию о начале и завершении задачи:
        - <code>*"start"</code>: содержит информацию о начале задачи:
            - <code>"time"</code>: время начала задачи. Возможные значения:
                1) Время в формате <code>"hh:MM"</code>;
                2) <code>"now"</code>: задача начнется немедленно.
                Если <code>"start"</code> имеет поле <code>"month"</code>, то это поле не обязательно.
            - <code>"day"</code>: - количество дней, через которые необходимо начать задачу, после ее завершения. 
                                    Или день недели начала задачи [(значения)](#значения-дней-недели). 
                                    Если <code>"time"</code> имеет значение <code>"now"</code> или <code>"start"</code> 
                                    имеет поле <code>"month"</code>, то это поле не обязательно.
            - <code>"month"</code>: - месяц начала задачи:
                 - <code>*"values"</code>: - количество месяцев, через которые необходимо начать задачу, после ее 
                                             завершения. 
                                             Или список месяцев начала задачи [(значения)](#значения-месяцев). Задача
                                             будет начинаться с указанного первого месяца, потом со второго, и так 
                                             далее. Когда psd пройдет все значения, то он начнет с первого.
                 - <code>*"day"</code>: - количество дней, через которые необходимо начать задачу, после ее завершения. 
                                          Или день недели начала задачи [(значения)](#значения-дней-недели). 
                 - <code>"each"</code>: - номер дня недели месяца. Значение поля <code>"day"</code> должно быть днем 
                                          недели. 
                 - <code>*"time"</code>: время начала задачи в формате <code>"hh:MM"</code>.
            - <code>"when_finished"</code>: - если дата следующего старта задачи до даты завершения задачи, то можно 
                                              указать данный параметр для того, чтобы расчет следующего старта задачи 
                                              начинался с даты завершения задачи. 
                                              Значение по умолчанию - <code>false</code>.
        - <code>*"finish"</code>: содержит информацию о завершении задачи:
            - <code>"time"</code>: время завершения задачи. Возможные значения:
                1) Время в формате <code>"hh:MM"</code>;
                2) <code>"never"</code>: никогда не завершать задачу.
                Если <code>"finish"</code> имеет поле <code>"month"</code>, то это поле не обязательно.
            - <code>"day"</code>: - количество дней, показывающих, сколько дней должна выполняться задача.
                                    Или день недели завершения задачи [(значения)](#значения-дней-недели).
                                    Если <code>"time"</code> имеет значение <code>"never"</code> или 
                                    <code>"finish"</code> имеет поле <code>"month"</code>, то это поле не обязательно.
            - <code>"month"</code>: - месяц завершения задачи:
                 - <code>*"values"</code>: - количество месяцев, через которые необходимо завершить задачу, после ее 
                                             завершения. 
                                             Или месяц начала задачи [(значения)](#значения-месяцев).
                                          Или день недели завершения задачи [(значения)](#значения-дней-недели). 
                 - <code>"each"</code>: - номер дня недели месяца. Значение поля <code>day</code> должно быть днем 
                                          недели. 
                 - <code>*"time"</code>: время начала задачи в формате <code>"hh:MM"</code>.
    - <code>"repeat"</code>: содержит информацию о повторении задачи после ее начала. Это подходит для задач, которые 
                             запускаются единожды:
        - <code>"unit"</code> - единица измерения времени повторения. Возможные значения:
            1) <code>"s"</code> - секунды;
            2) <code>"m"</code> - минуты;
            3) <code>"h"</code> - часы.
        - <code>"val"</code> - значение времени повторения задачи.
        - <code>"wait_finished"</code> - ждать завершение задачи перед тем, как ее повторить. Если <code>true</code>, то
                                         задача повторится после того, как она завершится, с учетом времени повторения. 
                                         Если <code>false</code>, то задача повторится после времени повторения.

## Задача в файле
Задачи могут быть определены в отдельных файлах. Для этого определите задачу в списке задач (jobs) как:
```json
{
  "file": "whoami.json"
}
```
Файл whoami.json:
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
Вы можете проигнорировать поле <code>"name"</code> в файле задачи. В этом случае имя задачи будет именем файла без 
расширения. 

Если в файле планировщика будет определено поле <code>"working_dir"</code>, то указывать полное имя файла не нужно. 

## Подсветка терминального вывода
psd поддерживает цветной вывод в терминал. 
[Список поддерживаемых терминалов](#список-поддерживаемых-подсветку-терминалов).
<img src=psd-highlight.png/>

## Значения дней недели
1) <code>"mon"</code> - Понедельник;
2) <code>"tue"</code> - Вторник;
3) <code>"wed"</code> - Среда;
4) <code>"thu"</code> - Четверг;
5) <code>"fri"</code> - Пятница;
6) <code>"sat"</code> - Суббота;
7) <code>"sun"</code> - Воскресенье.

## Значения месяцев
1) <code>"jan"</code> - Январь;
2) <code>"feb"</code> - Февраль;
3) <code>"mar"</code> - Март;
4) <code>"apr"</code> - Апрель;
5) <code>"may"</code> - Май;
6) <code>"jun"</code> - Июнь;
7) <code>"jul"</code> - Июль;
8) <code>"aug"</code> - Август;
9) <code>"sep"</code> - Сентябрь;
10) <code>"oct"</code> - Октябрь;
11) <code>"nov"</code> - Ноябрь;
12) <code>"dec"</code> - Декабрь.

## Список поддерживаемых подсветку терминалов
1) [Eterm](https://github.com/mej/Eterm)
2) [GNOME Terminal](https://help.gnome.org/users/gnome-terminal/)
3) [Guake](http://guake.org)
4) [Konsole](https://konsole.kde.org/)
5) [Nautilus Terminal](https://github.com/flozz/nautilus-terminal)
6) [Terminator](https://code.google.com/archive/p/jessies/wikis/Terminator.wiki)
7) [Tilda](http://tilda.sourceforge.net/tildaabout.php)
8) [XFCE4 Terminal](https://docs.xfce.org/apps/terminal/start)
9) [XTerm](https://invisible-island.net/xterm/xterm.html)
10) [VTE Terminal](https://developer.gnome.org/vte/)

Пример
-------
```shell script
$ python psd.py psd.json 
[ Schedule started at 2020-04-19 14:06:30.110551 ]
[ Schedule started at 2020-04-19 14:06:30.110551 ]
[STARTED] ['ping2'] [Started: 2020-04-19 14:06:30.110607] [Finished: 2020-04-19 14:07:00] [Next start: 2020-04-21 14:06:00]
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=35 time=211 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=35 time=234 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=35 time=154 ms
[FINISHED] ['ping2'] [Finished: 2020-04-19 14:07:00.147956]
[STARTED] ['ls'] [Started: 2020-04-19 14:07:35.836019] [Finished: 2020-04-22 14:08:00] [Next start: 2020-04-23 14:07:00]
LICENSE  psd.json  psd.py  README.md
LICENSE  psd.json  psd.py  README.md
```
