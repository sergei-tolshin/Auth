from functional.settings import config

SCHEMA = {
    "settings": config.ELASTIC_SETTINGS,
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {
                "type": "keyword"
            },
            "name": {
                "type": "keyword"
            },
            "description": {
                "type": "text",
                "analyzer": "ru_en"
            }
        }
    }
}
