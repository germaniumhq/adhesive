import re


TIME_PERIOD_RE = re.compile(r'P((\d+)Y)?((\d)M)?((\d)D)?(T((\d)H)?((\d)M)?((\d)S)?)?')


class TimePeriod:
    def __init__(self,
                 *,
                 year: int = 0,
                 month: int = 0,
                 day: int = 0,
                 hour: int = 0,
                 minute: int = 0,
                 second: int = 0) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

    @staticmethod
    def from_str(s: str) -> 'TimePeriod':
        m = TIME_PERIOD_RE.match(s)

        if not m:
            raise Exception(f"Unable to parse time period {s}")

        result = TimePeriod()

        result.year = int(m.group(2)) if m.group(2) else 0
        result.month = int(m.group(4)) if m.group(4) else 0
        result.day = int(m.group(6)) if m.group(6) else 0
        result.hour = int(m.group(9)) if m.group(9) else 0
        result.minute = int(m.group(11)) if m.group(11) else 0
        result.second = int(m.group(13)) if m.group(13) else 0

        return result
