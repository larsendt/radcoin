import apsw
import arrow
import traceback
from typing import Any, Optional, Tuple, Union
from types import TracebackType

TIME_FMT = "YYYY-MM-DDTHH:mm:ssZ"

CREATE_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS log (
    id INTEGER NOT NULL PRIMARY KEY,
    level TEXT,
    source TEXT,
    message TEXT,
    traceback TEXT
)"""

INSERT_LOG_SQL = """
INSERT INTO log(level, source, message, traceback) VALUES (
    :level, :source, :message, :traceback
)"""

class DBLogger(object):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

    def __init__(self, source: Union[str, object], db_path: str) -> None:
        if isinstance(source, str):
            self.source = source
        elif isinstance(source, object):
            self.source = source.__class__.__module__ + "." + source.__class__.__name__
        else:
            raise TypeError("Bad source type", type(source))

        self._db_path = db_path
        self._conn = apsw.Connection(db_path)
        with self._conn:
            c = self._conn.cursor()
            c.execute(CREATE_LOG_TABLE)
    
    def debug(self, *args: Any, tb: Optional[TracebackType] = None) -> None:
        self.log(self.DEBUG, args, tb)

    def info(self, *args: Any, tb: Optional[TracebackType] = None) -> None:
        self.log(self.INFO, args, tb)

    def warn(self, *args: Any, tb: Optional[TracebackType] = None) -> None:
        self.log(self.WARN, args, tb)

    def error(self, *args: Any, tb: Optional[TracebackType] = None) -> None:
        self.log(self.ERROR, args, tb)

    def log(self, level: str, msg_args: Tuple[Any, ...], tb: Optional[TracebackType] = None) -> None:
        now = arrow.utcnow()
        now_fmt = now.format(TIME_FMT)
        msg = " ".join(map(str, msg_args))
        print_msg = "[{}] [{}] [{}]: {}".format(level, now_fmt, self.source, msg)

        if tb is not None:
            tb_str = "\n".join(traceback.format_tb(tb))
            print_msg += "\n" + tb_str
        else:
            tb_str = None

        print(print_msg)

        log_args = {
            "unix_millis": int(now.timestamp * 1000),
            "level": level,
            "source": self.source,
            "message": msg,
            "traceback": tb_str,
        }

        with self._conn:
            c = self._conn.cursor()
            c.execute(INSERT_LOG_SQL, log_args)
