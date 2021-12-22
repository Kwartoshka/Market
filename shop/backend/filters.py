import django_filters
from django_filters import FilterSet, Filter
from backend.models import ProductInfo


class CategoryFilter(Filter):
    def filter(self, qs, value):
        if value is None:
            return qs
        query = qs.filter(product_id__category_id=value)
        return query


class ProductInfoFilter(FilterSet):

    shop_id = django_filters.NumberFilter()
    category_id = CategoryFilter(field_name='product_id')

    class Meta:
        model = ProductInfo
        fields = ['shop_id', 'product_id']
