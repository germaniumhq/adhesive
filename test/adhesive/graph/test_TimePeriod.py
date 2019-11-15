import unittest

from adhesive.graph.TimePeriod import TimePeriod


class TimePeriodTest(unittest.TestCase):
    def test_parsing(self):
        time_period = TimePeriod.from_str("P1Y2M3DT4H5M6S")

        self.assertEqual(1, time_period.year)
        self.assertEqual(2, time_period.month)
        self.assertEqual(3, time_period.day)
        self.assertEqual(4, time_period.hour)
        self.assertEqual(5, time_period.minute)
        self.assertEqual(6, time_period.second)

    def test_parsing_only_month(self):
        time_period = TimePeriod.from_str("P1M")

        self.assertEqual(0, time_period.year)
        self.assertEqual(1, time_period.month)
        self.assertEqual(0, time_period.day)
        self.assertEqual(0, time_period.hour)
        self.assertEqual(0, time_period.minute)
        self.assertEqual(0, time_period.second)

    def test_parsing_only_minute(self):
        time_period = TimePeriod.from_str("PT1M")

        self.assertEqual(0, time_period.year)
        self.assertEqual(0, time_period.month)
        self.assertEqual(0, time_period.day)
        self.assertEqual(0, time_period.hour)
        self.assertEqual(1, time_period.minute)
        self.assertEqual(0, time_period.second)
