import arrow
from core.config import Config
import os
import sqlite3
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

LEVEL = "DEBUG"

TIME_FMT = "YYYY-MM-DDTHH:mm:ssZ"

CREATE_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS log (
    id INTEGER NOT NULL PRIMARY KEY,
    level TEXT,
    source TEXT,
    pid INTEGER,
    message TEXT,
    traceback TEXT
)"""

INSERT_LOG_SQL = """
INSERT INTO log(level, source, pid, message, traceback) VALUES (
    :level, :source, :pid, :message, :traceback
)"""

class DBLogger(object):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    LOG_LEVELS: List[str] = [DEBUG, INFO, WARN, ERROR]
    LOG_ORDER: Dict[str, int] = {DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3}

    def __init__(self, source: Union[str, object], cfg: Config) -> None:
        if isinstance(source, str):
            self.source = source
        elif isinstance(source, object):
            self.source = source.__class__.__module__ + "." + source.__class__.__name__
        else:
            raise TypeError("Bad source type", type(source))

        self._conn = sqlite3.connect(cfg.log_db_path())
        self.log_level = cfg.log_level()
        with self._conn:
            c = self._conn.cursor()
            c.execute(CREATE_LOG_TABLE)
    
    def debug(self, *args: Any, exc: Optional[Exception] = None) -> None:
        self.log(self.DEBUG, args, exc)

    def info(self, *args: Any, exc: Optional[Exception] = None) -> None:
        self.log(self.INFO, args, exc)

    def warn(self, *args: Any, exc: Optional[Exception] = None) -> None:
        self.log(self.WARN, args, exc)

    def error(self, *args: Any, exc: Optional[Exception] = None) -> None:
        self.log(self.ERROR, args, exc)

    def log(self, level: str, msg_args: Tuple[Any, ...], exc: Optional[Exception] = None) -> None:
        pid = os.getpid()
        now = arrow.utcnow()
        now_fmt = now.format(TIME_FMT)
        msg = " ".join(map(str, msg_args))
        print_msg = "[{}] [{}] [{}] [pid{}]: {}".format(level, now_fmt, self.source, pid, msg)

        if exc is not None:
            exc_str = "".join(traceback.format_exception(None, exc, None))
            print_msg += "\n" + exc_str
        else:
            exc_str = None

        if self.LOG_ORDER[level] >= self.LOG_ORDER[self.log_level]:
            print(print_msg)

        log_args = {
            "unix_millis": int(now.timestamp * 1000),
            "level": level,
            "source": self.source,
            "pid": pid,
            "message": msg,
            "traceback": exc_str,
        }

        with self._conn:
            c = self._conn.cursor()
            c.execute(INSERT_LOG_SQL, log_args)
