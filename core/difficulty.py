from core.dblog import DBLogger
from core.timestamp import Timestamp
import math
from typing import Iterator

DEFAULT_DIFFICULTY = 2
BLOCK_TIME_TARGET = 1 * 60 * 1000 # 1 minute

def difficulty_adjustment(block_times: Iterator[Timestamp], l: DBLogger) -> int:
    """Computes how much the difficulty should be adjusted by (up or down).

    Uses the difference of the log of the mean block time delta and the log of
    the target delta.

    If the mean block time is 2x the target, the adjustment should be -1.
    If the mean block time is 4x the target, the adjustment should be -2.
    If the mean block time ix 1/8th the target, the adjustment should be +3.
    """
    
    unix_times = list(map(lambda t: t.unix_millis, block_times))

    deltas = []
    prev = unix_times[0]
    for t in unix_times[1:]:
        deltas.append(t - prev)
        prev = t

    mean = sum(deltas) / len(deltas)
    l.debug("Segment mean ms:", mean)
    l.debug("Target ms:", BLOCK_TIME_TARGET)

    log_mean = math.log2(mean)
    log_target = math.log2(BLOCK_TIME_TARGET)
    log_difference = log_target - log_mean
    l.debug("Log difference:", log_difference)

    adjustment = int(round(log_target - log_mean))
    l.debug("Recommended adjustment:", adjustment)
    return adjustment
