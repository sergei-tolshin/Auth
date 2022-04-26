
class BaseManager:
    """Базовый менеджер моделей"""
    connection = None
    limit = 100

    @classmethod
    def set_connection(cls, conn=None):
        cls.connection = conn

    @classmethod
    def set_limit(cls, limit=None):
        cls.limit = limit

    @classmethod
    def _get_cursor(cls):
        return cls.connection.cursor()

    def __init__(self, model_class):
        self.model_class = model_class
        self.object_model = self.model_class.object_model
        self.instance_model = self.model_class.instance_model

    @property
    def table_name(self):
        return self.model_class.table_name

    @property
    def fields(self):
        return self.object_model.__fields__.keys()

    @property
    def relations(self):
        return self.model_class.relations

    def _model_objects(self, query, model=dict, batch_size=100):
        batch_size = batch_size or self.limit
        model_objects = list()
        cursor = self._get_cursor()
        cursor.execute(query)

        is_fetching_completed = False
        while not is_fetching_completed:
            result = cursor.fetchmany(size=batch_size)
            for row_values in result:
                model_objects.append(model(**row_values))
            is_fetching_completed = len(result) < batch_size

        return model_objects

    """Получает изменные данные"""

    def select_modified(self, modified=None, batch_size=100):
        batch_size = batch_size or self.limit
        fields_format = ', '.join(self.fields)

        query = f"""
            SELECT {fields_format}
            FROM {self.table_name}
            WHERE modified > '{modified}'
            ORDER BY modified
            LIMIT {batch_size};
        """

        return self._model_objects(query=query, model=self.object_model)

    """Получает связанные данные"""

    def select_relation(self, relation, ids):
        relation_table = self.relations[relation]['table']
        relation_field = self.relations[relation]['field']
        relation_model = self.relations[relation]['model']
        condition = f"IN {tuple(ids)}" if len(ids) > 1 else f"= '{ids[0]}'"

        query = f"""
            SELECT tn.id, tn.modified
            FROM {self.table_name} tn
            LEFT JOIN {relation_table} rt ON rt.{self.table_name}_id = tn.id
            WHERE rt.{relation_field} {condition}
            ORDER BY tn.modified;
        """

        return self._model_objects(query=query, model=relation_model)
