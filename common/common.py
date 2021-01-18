from requests.models import PreparedRequest


def is_valid_url(url):
    prepared_request = PreparedRequest()
    try:
        prepared_request.prepare_url(url, None)
        return True
    except Exception as e:
        return False


class Timestamp:  # a speedrun.com style timestamp e.g. "3h 53m 233s 380ms"
    def __init__(self, s):
        self.hours, self.minutes, self.seconds, self.milliseconds = 0, 0, 0, 0
        for arg in s.split():
            if arg.endswith("ms"):
                self.milliseconds += int(arg[:-2])
            elif arg.endswith("s"):
                self.seconds += int(arg[:-1])
            elif arg.endswith("m"):
                self.minutes += int(arg[:-1])
            elif arg.endswith("h"):
                self.hours += int(arg[:-1])

    @staticmethod
    def from_milliseconds(ms):
        t = Timestamp("0ms")
        temp = ms
        t.hours = temp // 3600000
        temp %= 3600000
        t.minutes = temp // 60000
        temp %= 60000
        t.seconds = temp // 1000
        t.milliseconds = temp % 1000
        return t


    def __str__(self):
        result = []
        if self.hours != 0:
            result.append("{}h".format(self.hours))
        if not (self.hours == 0 and self.minutes == 0):
            result.append("{}m".format(self.minutes))
        result.append("{}s".format(self.seconds))
        if self.milliseconds > 0:
            result.append("{}ms".format(self.milliseconds))
        return ' '.join(result)

    def __eq__(self, other):
        return self.hours == other.hours and self.minutes == other.minutes and self.seconds == other.seconds and self.milliseconds == other.milliseconds

    def __lt__(self, other):
        if self.hours < other.hours:
            return True
        elif self.hours > other.hours:
            return False
        if self.minutes < other.minutes:
            return True
        elif self.minutes > other.minutes:
            return False
        if self.seconds < other.seconds:
            return True
        elif self.seconds > other.seconds:
            return False
        return self.milliseconds < other.milliseconds
