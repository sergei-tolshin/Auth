import factory


class ObjFactoryMixin(factory.Factory):

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        schema = model_class()
        results = schema.load(kwargs)

        return results
