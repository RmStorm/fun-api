import signal
import time
import asyncio
import logging
import os
from distutils.util import strtobool

from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator, metrics

echo_counter = Counter('my_echo_counter', 'Description of counter')
http_load_counter = Counter('roald_request_counter', 'attempts to request the cool api', labelnames=["status"])

app = FastAPI()
Instrumentator().instrument(app)

instrumentator = Instrumentator()
instrumentator.add(metrics.default(metric_namespace='roald'))
instrumentator.instrument(app)
app.mount("/metrics", make_asgi_app())


def _loglevel_signal_handler():
    fastapi_sigterm_handler = signal.getsignal(signal.SIGTERM)

    def handle_sigterm(signalnum, _frame):
        if not signalnum == signal.SIGTERM:
            raise RuntimeError('WTF is going on')
        print('Received SIGTERM now!!!!')
        fastapi_sigterm_handler(signalnum, _frame)

    signal.signal(signal.SIGTERM, handle_sigterm)


@app.on_event("startup")
async def startup_event():
    _loglevel_signal_handler()
    print(os.getpid())
    print(signal.getsignal(signal.SIGTERM))


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


async def deferred_get(address: str, i: int):
    logging.info(f"getting {i}")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(address)
            http_load_counter.labels(r.status_code).inc()
    except httpx.TimeoutException:
        http_load_counter.labels("504").inc()
    except httpx.ConnectError:
        http_load_counter.labels("502").inc()
    logging.info(f"completed {i}")


@app.post("/start_load")
async def start_load(seconds: float, address: str):
    start_time = time.time()
    logging.info(f"Starting load at: {start_time}")
    logging.info(f"hitting up: {address}")
    i = 0
    while time.time() < start_time+seconds:
        i += 1
        await asyncio.sleep(0.01)
        logging.info("sending")
        asyncio.create_task(deferred_get(address, i))
    logging.info(f"completed load at: {start_time}")
    return "Load completed"


@app.get("/proxy")
async def proxy(address: str):
    print("sleeping")
    await asyncio.sleep(1)
    async with httpx.AsyncClient() as client:
        r = await client.get(address)
        r.raise_for_status()
    return {'state': 'success', 'proxied_response': r.json()}


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
