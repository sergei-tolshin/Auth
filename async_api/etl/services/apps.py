from datetime import datetime
from importlib import import_module

from utils.decorators import coroutine
from utils.utils import camel_to_snake


class BaseApps(object):
    @classmethod
    def get_classname(cls):
        return camel_to_snake(cls.__name__)

    def __init__(self, state, es_client, *args, **kwargs):
        self.apps_name = self.get_classname()
        self.es_client = es_client
        self.state = state
        self.states = self.state.get_state(self.apps_name) or {}
        self.last_modified = self._get_last_modified()

    def _get_last_modified(self):
        if not self.states.get('modified'):
            self.states['modified'] = f'{datetime.min}'
        return self.states.get('modified')

    def _get_states(self, state):
        state_name = f'{state}_modified'
        if not self.states.get(state_name):
            self.states[state_name] = f'{datetime.min}'
        return self.states.get(state_name)

    def _set_states(self, state, value):
        state_name = f'{state}_modified'
        self.states[state_name] = value
        return value

    def _update_relation(self, relation, name, ids):
        relation_apps_name = '%s.%s' % (f'apps.{relation}', 'apps')
        relation_models_name = '%s.%s' % (f'apps.{relation}', 'models')
        relation_apps = import_module(relation_apps_name)
        relation_models = import_module(relation_models_name)
        model = getattr(relation_models, f'{relation.title()}')
        apps = getattr(relation_apps, f'{relation.title()}Apps')
        index = apps.index
        schema = apps.schema
        transform = apps.transform

        if objects := model.objects.select_relation(name, ids=ids):
            obj_ids = [obj.id for obj in objects]
            obj_instances = model.objects.instances(ids=obj_ids)

            if obj_instances is not None:
                transform_data = transform(apps, obj_instances)
                inserter_obj = self.load(index=index, schema=schema)
                for _ in transform_data:
                    inserter_obj.send(_)
                inserter_obj.close()
            self.save_state()

    def save_state(self):
        self.state.set_state(self.apps_name, self.states)

    def run(self):
        pass

    def extract(self) -> None:
        """Получает измененные данные"""
        pass

    def transform(self, data) -> None:
        """Трансформирует полученные данные"""
        pass

    @coroutine
    def load(self, target_db=None, index=None, schema=None, batch_size=100):
        """Формирует пакеты и загружает их в Elasticsearch"""
        target_db = target_db or self.es_client
        target_db.index = index
        target_db.schema = schema
        actions: list = []
        try:
            while True:
                data = (yield)
                actions.append(data)
                if len(actions) == batch_size:
                    target_db.transfer_data(actions=actions)
                    actions.clear()
        except GeneratorExit:
            target_db.transfer_data(actions=actions)
