# Python скрипт, предназначенный для анализа NGINX логов.

## Описание

Данный скрипт принимает файл логов в plain или .gz формате, собирает статистику и выводит ее в html отчет.

Собираемая статистика:
* count - сколько раз встречается URL, абсолютное значение
* count_perc - сколько раз встречается URL, в процентнах относительно общего числа запросов
* time_sum - суммарный \$request_time для данного URL'а, абсолютное значение
* time_perc - суммарный \$request_time для данного URL'а, в процентах относительно общего $request_time всех запросов
* time_max - максимальный \$request_time для данного URL'а
* time_med - медиана \$request_time для данного URL'а
* time_avg - средний \$request_time для данного URL'а

## Конфигурация

По умолчанию скрипт будет искать входные данные в папке ./data/log , а отчет будет помещен в папку ./data/report .
Можно сконфигурировать работу скрипта, указав путь к внешнему config-файлу аргументов --config:
python -m log_analyzer --config <path_to_config>

Поддерживаемые параметры в конфиге:
* LOG_DIR - путь к папке с логами NGINX;
* REPORT_DIR - путь к папке для сохранения отчета;
* REPORT_SIZE - количество строк в отчете. В отчет попадают REPORT_SIZE строк статистики, отсортированных по суммарному времени выполнения запроса;
* REPORT_TEMPLATE_PATH - путь к шаблону отчета;
* LOGGING_PATH - путь к файлу для логирования;
* FAILURE_THRESHOLD - пороговое значение для количества ошибок, при котором скрипт завершит работу.

### Пример конфига:
```
{
"LOG_DIR": "/data/log",
"REPORT_DIR": "/data/report",
"REPORT_SIZE": 1000,
"REPORT_TEMPLATE_PATH": "/data/report.html",
"LOGGING_PATH": "/logs",
"FAILURE_THRESHOLD": 0.3
}
```

## Запуск скрипта

Скрипт поддерживает запуск следующим образом:
* Минимальный запуск с параметрами по умолчанию:
```
python -m log_analyzer
```
* Запуск с указанием конфига:
```
python -m log_analyzer --config <path_to_config>
```
* Запуск с помощью Makefile:
```
make run
```
* Запуск с помощью makefile и указанием конфига:
```
make run PARAMS="--config <config_path>"
```
* Запуск в docker с указанием volume для конфига, логов и отчета:
```
docker run -v <path_to_log_dir>:/app/data/log -v <path_to_report_dir>:/app/data/report -v <path_to_logging_file>:/app/data/log.log -v <path_to_config>:/app/config log_analyzer --config /app/config log_analyzer --config /app/config/<config_name>.json
```



