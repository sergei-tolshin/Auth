from config.settings import es_settings

"""Схема индекса persons для Elastic"""
SCHEMA = {
    'settings': es_settings.ES_SETTINGS,
    'mappings': {
        'dynamic': 'strict',
        'properties': {
            'id': {
                'type': 'keyword'
            },
            'full_name': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
            'roles': {
                'type': 'keyword'
            },
            'film_ids': {
                'type': 'keyword'
            },
            'actor_film_ids': {
                'type': 'keyword'
            },
            'director_film_ids': {
                'type': 'keyword'
            },
            'writer_film_ids': {
                'type': 'keyword'
            },
        }
    }
}
