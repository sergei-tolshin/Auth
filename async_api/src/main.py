import logging

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import films, genres, persons
from core import config, logger
from db import cache, elastic, redis, storage

app = FastAPI(
    title='Read-only API для онлайн-кинотеатра',
    description=("Информация о фильмах, жанрах и людях, "
                 "участвовавших в создании произведения"),
    version='1.0.0',
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    redoc_url='/api/redoc',
    default_response_class=ORJSONResponse,
)


@app.on_event('startup')
async def startup():
    cache.cache = await redis.RedisCache.create(
        (config.REDIS_HOST, config.REDIS_PORT))

    storage.db = await elastic.ElasticStorage.create(
        hosts=[f'{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'])


@app.on_event('shutdown')
async def shutdown():
    await cache.cache.close()
    await storage.db.close()


app.include_router(films.router, prefix='/api/v1', tags=['Фильмы'])
app.include_router(genres.router, prefix='/api/v1', tags=['Жанры'])
app.include_router(persons.router, prefix='/api/v1', tags=['Люди'])

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        log_config=logger.LOGGING,
        log_level=logging.DEBUG,
    )
