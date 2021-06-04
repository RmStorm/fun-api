import logging
import os
import asyncio
from distutils.util import strtobool

from typing import Optional

import aiohttp
from fastapi import FastAPI, HTTPException
import google.auth
import google.auth.transport.requests as gauth_requests
from google.auth import compute_engine


app = FastAPI()


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


async def alma_heartbeat():
    try:
        credentials, _ = google.auth.default()
        credentials.refresh(gauth_requests.Request())
        if getattr(credentials, 'id_token', None) is None:
            credentials = compute_engine.IDTokenCredentials(gauth_requests.Request(), 'my-audience',
                                                            use_metadata_identity_endpoint=True)
            credentials.refresh(gauth_requests.Request())
            headers = {"authorization": f"Bearer {credentials.token}"}
        else:
            headers = {"authorization": f"Bearer {credentials.id_token}"}
    except Exception as e:
        headers = {}

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get('https://alma.osl1.staging.nube.tech/api/foo', headers=headers) as resp:
                if resp.status == 200:
                    logging.info('successfully reached Alma')
                else:
                    logging.info(f'could not reach Alma, auth status= {resp.status}')
            await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(alma_heartbeat())


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/echo/")
async def echo(echo_string: Optional[str] = None):
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
async def echo(value: bool):
    CONFIGURABLE_CHECKS.healthy = value


@app.get("/setready/")
async def echo(value: bool):
    CONFIGURABLE_CHECKS.ready = value
