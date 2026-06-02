from time import time

from fastapi import HTTPException, status

requests = {}
MAX_REQUESTS = 10
WINDOW_SECONDS = 60


def check_rate(ip: str, route: str):
    if not ip:
        return

    now = int(time())
    window_start = now - WINDOW_SECONDS
    key = (ip, route)
    history = requests.get(key, [])
    history = [timestamp for timestamp in history if timestamp > window_start]
    history.append(now)
    requests[key] = history

    if len(history) > MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests, please wait a minute"
        )
