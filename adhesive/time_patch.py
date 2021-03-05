import logging
import time
from ctypes import cdll

LOG = logging.getLogger(__name__)

glibc = None


def _custom_sleep(t):
    glibc.usleep(int(t * 1000000))


def patch_time():
    global glibc
    try:
        glibc = cdll.LoadLibrary("libc.so.6")

        time.sleep = _custom_sleep
    except Exception as e:
        print(f"Failed to patch time.sleep: {e}. Performance might be worse.")
