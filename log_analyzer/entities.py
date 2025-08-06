import re
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import NamedTuple, TypedDict, Union


class JsonConfig(TypedDict):
    LOG_DIR: str | None
    REPORT_DIR: str | None
    REPORT_SIZE: int | None
    REPORT_TEMPLATE_PATH: str | None


@dataclass
class Config:
    log_dir: str | None
    report_dir: str | None
    report_size: int | None
    report_template_path: str | None

    @classmethod
    def from_dict(cls, data: JsonConfig) -> "Config":
        return cls(
            log_dir=data.get("LOG_DIR"),
            report_dir=data.get("REPORT_DIR"),
            report_size=data.get("REPORT_SIZE"),
            report_template_path=data.get("REPORT_TEMPLATE_PATH"),
        )

    @classmethod
    def get_default_config(cls) -> "Config":
        return cls(
            log_dir="./log",
            report_dir="./report",
            report_size=1000,
            report_template_path="./data/report.html",
        )


@dataclass
class RawLog:
    """
    log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
                    '$request_time';
    """

    LOG_FORMAT_TEMPLATE = r"""
    ^
    (?P<remote_addr>\S+) \s+                           # $remote_addr
    (?P<remote_user>\S+) \s+                           # $remote_user
    (?P<http_x_real_ip>\S+) \s+                        # $http_x_real_ip
    \[(?P<time_local>[^\]]+)\] \s+                     # [$time_local]
    "(?P<request>[^"]+)" \s+                           # "$request"
    (?P<status>\d+) \s+                                # $status
    (?P<body_bytes_sent>\d+) \s+                       # $body_bytes_sent
    "(?P<http_referer>[^"]*)" \s+                      # "$http_referer"
    "(?P<http_user_agent>[^"]*)" \s+                   # "$http_user_agent"
    "(?P<http_x_forwarded_for>[^"]*)" \s+              # "$http_x_forwarded_for"
    "(?P<http_X_REQUEST_ID>[^"]*)" \s+                 # "$http_X_REQUEST_ID"
    "(?P<http_X_RB_USER>[^"]*)" \s+                    # "$http_X_RB_USER"
    (?P<request_time>[\d.]+)                           # $request_time
    $
"""

    remote_addr: str
    remote_user: str
    http_x_real_ip: str
    time_local: str
    request: str
    status: int
    body_bytes_sent: int
    http_referer: str
    http_user_agent: str
    http_x_forwarded_for: str
    http_X_REQUEST_ID: str
    http_X_RB_USER: str
    request_time: float

    @classmethod
    def from_str(cls, data: str) -> "RawLog":
        try:
            log_fields = re.match(cls.LOG_FORMAT_TEMPLATE, data, re.VERBOSE)
            if not log_fields:
                raise ValueError(f"Invalid log format: {data}")
            log_fields = log_fields.groupdict()  # type: ignore
            return cls(
                remote_addr=log_fields["remote_addr"],
                remote_user=log_fields["remote_user"],
                http_x_real_ip=log_fields["http_x_real_ip"],
                time_local=log_fields["time_local"],
                request=log_fields["request"],
                status=int(log_fields["status"]),
                body_bytes_sent=int(log_fields["body_bytes_sent"]),
                http_referer=log_fields["http_referer"],
                http_user_agent=log_fields["http_user_agent"],
                http_x_forwarded_for=log_fields["http_x_forwarded_for"],
                http_X_REQUEST_ID=log_fields["http_X_REQUEST_ID"],
                http_X_RB_USER=log_fields["http_X_RB_USER"],
                request_time=float(log_fields["request_time"]),
            )
        except (TypeError, ValueError) as e:
            raise e


@dataclass
class UriStatistics:
    uri: str
    log_count: int
    log_count_perc: float
    time_sum: float
    time_perc: float
    time_avg: float
    time_max: float
    request_times: list[float]

    @property
    def time_med(self) -> float:
        return median(self.request_times)

    def to_dict(self) -> dict[str, str | int]:
        return {
            "uri": self.uri,
            "log_count": self.log_count,
            "log_count_perc": f"{self.log_count_perc:.3f}",
            "time_sum": f"{self.time_sum:.3f}",
            "time_perc": f"{self.time_perc:.3f}",
            "time_avg": f"{self.time_avg:.3f}",
            "time_max": f"{self.time_max:.3f}",
            "time_med": f"{self.time_med:.3f}",
        }

    @classmethod
    def update_statistics(
        cls,
        statistics: Union["UriStatistics", None],
        log_entry: RawLog,
        total_count: int,
        total_request_time: float,
    ) -> tuple[bool, Union["UriStatistics", None]]:
        try:
            if not statistics:
                return True, cls(
                    uri=log_entry.request.split()[1],
                    log_count=1,
                    log_count_perc=(1 / total_count) * 100,
                    time_sum=log_entry.request_time,
                    time_perc=(log_entry.request_time / total_request_time) * 100,
                    time_avg=log_entry.request_time,
                    time_max=log_entry.request_time,
                    request_times=[log_entry.request_time],
                )
            else:
                statistics.log_count += 1
                statistics.log_count_perc = (statistics.log_count / total_count) * 100
                statistics.time_sum += log_entry.request_time
                statistics.time_perc = (statistics.time_sum / total_request_time) * 100
                statistics.time_avg = statistics.time_sum / statistics.log_count
                statistics.time_max = (
                    statistics.time_max
                    if statistics.time_max > log_entry.request_time
                    else log_entry.request_time
                )
                statistics.request_times.append(log_entry.request_time)
                return True, statistics
        except Exception:
            return False, None


class LogInfo(NamedTuple):
    log_date: datetime
    file_name: str
    file_ext: str | None
