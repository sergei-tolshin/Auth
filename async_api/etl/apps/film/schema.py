from config.settings import es_settings

"""Схема индекса movies для Elastic"""
SCHEMA = {
    'settings': es_settings.ES_SETTINGS,
    'mappings': {
        'dynamic': 'strict',
        'properties': {
            'id': {
                'type': 'keyword'
            },
            'imdb_rating': {
                'type': 'float'
            },
            'film_type': {
                'type': 'keyword'
            },
            'genre': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            },
            'title': {
                'type': 'text',
                'analyzer': 'ru_en',
                'fields': {
                    'raw': {
                        'type': 'keyword'
                    }
                }
            },
            'description': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'directors_names': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'actors_names': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'writers_names': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
            'directors': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            },
            'actors': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            },
            'writers': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'id': {
                        'type': 'keyword'
                    },
                    'name': {
                        'type': 'text',
                        'analyzer': 'ru_en'
                    }
                }
            }
        }
    }
}
