import hashlib
import json
import time
from datetime import datetime
from time import sleep

import requests

TOKENS_TEMPLATE = {
    "accessToken": "",
    "refreshToken": "",
    "refreshTokenExpiry": None,
    "refreshTokenTtl": "",
    "userId": "",
    "orgId": "",
    "last_update": None,
    "api_hash": "",
    "time_stampv": "",
}

API_CALL_COUNT = 0
LAST_API_CALL_TIME = datetime.now()


def handle_rate_limit():
    global API_CALL_COUNT, LAST_API_CALL_TIME

    API_CALL_COUNT += 1
    if API_CALL_COUNT >= 300:
        time_diff = datetime.now() - LAST_API_CALL_TIME
        if time_diff.seconds < 60:
            time.sleep(60 - time_diff.seconds)
        API_CALL_COUNT = 0
        LAST_API_CALL_TIME = datetime.now()


def create_headers(access_token=None, refresh_token=None):
    """Returns headers with input parameters of the access token and refresh token
    to be filled in when calling the function"""

    if refresh_token and access_token:
        headers = {
            "Authorization": "Bearer " + access_token,
            "x-fv-sessionid": refresh_token,
            "Content-Type": "application/json",
        }
    else:
        headers = {"Content-Type": "application/json"}

    return headers


def handle_authentication(base_url, headers, api_key, api_secret, tokens):
    first_time = tokens["last_update"] is None
    retry = 0
    while retry < 4:
        if retry > 0 or first_time:
            time_stampv = datetime.utcnow().isoformat()[:-3] + "Z"
            join_str = "/".join([api_key, time_stampv, api_secret])
            api_hash = hashlib.md5(join_str.encode()).hexdigest()

            body = {
                "mode": "key",
                "apiKey": api_key,
                "apiHash": api_hash,
                "apiTimestamp": time_stampv,
            }
            response = requests.post(base_url + "/session", headers=headers, data=json.dumps(body))
            if response.status_code == 200:
                tokens.update(json.loads(response.text))
                tokens.update(
                    {
                        "last_update": time.perf_counter(),
                        "time_stampv": time_stampv,
                        "api_hash": api_hash,
                    }
                )
                return response.status_code, tokens["accessToken"], tokens["refreshToken"]
            else:
                retry += 1
                sleep(0.1)

        elif time.perf_counter() - tokens["last_update"] > 600:
            body = {
                "mode": "session",
                "apiKey": api_key,
                "apiHash": tokens["api_hash"],
                "apiTimestamp": tokens["time_stampv"],
                "sessionId": tokens["refreshToken"],
                "userId": tokens["userId"],
                "orgId": tokens["orgId"],
            }

            response = requests.post(base_url + "/session", headers=headers, data=json.dumps(body))

            if response.status_code != 200:
                retry += 1
                sleep(0.1)
            else:
                tokens.update(json.loads(response.text))
                tokens["last_update"] = time.perf_counter()

                return response.status_code, tokens["accessToken"], tokens["refreshToken"]
        else:
            return 200, tokens["accessToken"], tokens["refreshToken"]
    return None, None, None
