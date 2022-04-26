from config.settings import es_settings

"""Схема индекса genres для Elastic"""
SCHEMA = {
    'settings': es_settings.ES_SETTINGS,
    'mappings': {
        'dynamic': 'strict',
        'properties': {
            'id': {
                'type': 'keyword'
            },
            'name': {
                'type': 'keyword'
            },
            'description': {
                'type': 'text',
                'analyzer': 'ru_en'
            },
        }
    }
}
