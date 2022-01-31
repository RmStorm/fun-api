import logging
import os
from distutils.util import strtobool

from typing import Optional

from fastapi import FastAPI, HTTPException, Request
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


@app.get("/tell_groups/")
async def group_teller(request: Request):
    print("\nadditional x-user headers:")
    for k, v in request.headers.items():
        if k.startswith("x-user"):
            if k != "x-user-groups":
                print(f"{k} - {v}")
    return [g[:-7] for g in request.headers["x-user-groups"].split(',')]
