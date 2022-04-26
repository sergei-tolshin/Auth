from . import mixins


class ViewSet(
    mixins.RetrieveViewMixin,
    mixins.BaseListViewMixin,
    mixins.SearchViewMixin,
):
    pass


class ReadOnlyViewSet(
    mixins.RetrieveViewMixin,
    mixins.ListViewMixin,
):
    pass
