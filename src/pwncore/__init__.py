from fastapi import FastAPI
from contextlib import asynccontextmanager

from tortoise import Tortoise

import pwncore.docs as docs
import pwncore.routes as routes
from pwncore.container import docker_client
from pwncore.config import config
from pwncore.models import Container


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup
    await Tortoise.init(
        db_url=config.db_url,
        modules={"models": ["pwncore.models"]}
    )
    await Tortoise.generate_schemas()

    yield
    # Shutdown
    # Stop and remove all running containers
    containers = await Container.all().values()
    await Container.all().delete()
    for db_container in containers:
        container = await docker_client.containers.get(db_container["docker_id"])
        await container.stop()
        await container.delete()

    await Tortoise.close_connections()  # Deprecated, not sure how to use connections.close_all()
    await docker_client.close()


app = FastAPI(
    title="Pwncore",
    openapi_tags=docs.tags_metadata,
    description=docs.description,
    lifespan=app_lifespan,
)
app.include_router(routes.router)
