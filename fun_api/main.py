import asyncio
import logging
import os
import time
from distutils.util import strtobool
import datetime as dt

from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from starlette.responses import HTMLResponse
from prometheus_client import Counter, make_asgi_app

echo_counter = Counter('my_echo_counter', 'Description of counter')

app = FastAPI()
app.mount("/metrics", make_asgi_app())


class ConfigurableChecks:
    def __init__(self):
        self.healthy = self.set_to_env_bool("HEALTHY")
        self.ready = self.set_to_env_bool("READY")

    @staticmethod
    def set_to_env_bool(env_var) -> bool:
        try:
            return strtobool(os.getenv(env_var, "true"))
        except ValueError:
            logging.info(f"Supplied invalid value for env var: '{env_var}', defaulting to 'True'")
            return True


CONFIGURABLE_CHECKS = ConfigurableChecks()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/echo/")
async def echo(echo_string: Optional[str] = None):
    echo_counter.inc()
    if echo_string is None:
        return 'You said Nothing!'
    return f'You said: {echo_string}!'


@app.get("/health/")
async def health():
    if CONFIGURABLE_CHECKS.healthy:
        return 'OK'
    else:
        raise HTTPException(status_code=503, detail="This service is not ready")


@app.get("/ready/")
async def ready():
    if CONFIGURABLE_CHECKS.ready:
        return 'OK'
    else:
        raise HTTPException(status_code=503, detail="This service is not ready")


@app.get("/sethealth/")
async def sethealth(value: bool):
    CONFIGURABLE_CHECKS.healthy = value


@app.get("/setready/")
async def echo(value: bool):
    CONFIGURABLE_CHECKS.ready = value


# @app.get("/who-am-i/")
# async def who_am_i():
#     return os.getenv('POD_NAME', "no env var 'POD_NAME' found")
#
#
# @app.get("/blow-up-cpu/")
# async def blow_up_cpu(duration: float):
#     duration = dt.timedelta(seconds=duration)
#     now = dt.datetime.now()
#     x = 0
#     while dt.datetime.now()-now < duration:
#         while x < 1000:
#             x += 1
#         await asyncio.sleep(.00001)
#         while x > 0:
#             x -= 1
#         print('were goinngnggg')
#
#
# @app.get("/auth")
# async def auth(request: Request):
#     print("\nHEADERS:")
#     for k, v in request.headers.items():
#         print(f"{k} - {v}")
#     print('\nHitted auth!')
#     headers = {'X-User-HIYA': 'waza'}
#     response = PlainTextResponse("OK", 200, {k: v for k, v in headers.items() if v})
#     now = time.time()
#     response.set_cookie(
#         "fakesessionsecret",
#         'a dope cookie!!',
#         max_age=now + 3600,  # type: ignore[operator]
#         expires=now + 3600,  # type: ignore[operator]
#         path="/",
#         domain='demo.local',
#         secure=False,
#         httponly=True,
#         samesite="lax",
#     )
#     return response


# @app.get("/{rest_of_path:path}", response_class=HTMLResponse)
# async def catch_all(rest_of_path: str, request: Request):
#     print("\nHEADERS:")
#     for k, v in request.headers.items():
#         print(f"{k} - {v}")
#     return f"""
#     <html>
#         <head>
#             <title>Some HTML in here</title>
#         </head>
#         <body>
#             <h1>Currently hitting: '{os.getenv('SERVICE_NAME', 'no service')}'</h1>
#             <p>You tried to navigate to: '{rest_of_path}'</p>
#         </body>
#     </html>
#     """
