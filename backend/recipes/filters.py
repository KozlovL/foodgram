from django.contrib.contenttypes.models import ContentType
from django_filters import rest_framework as filter
from recipes.constants import LIST_NAME_CHOICES
from recipes.models import Recipe, SpecialListModel
from rest_framework import filters


class NameSearchFilter(filters.SearchFilter):
    search_param = 'name'


class RecipeFilter(filter.FilterSet):
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        to_field_name='slug',
    )

    is_favorited = filter.NumberFilter(method='filter_favorited')

    def filter_favorited(self, queryset, name, value):
        request = self.request
        is_favorited = request.GET.get('is_favorited')
        user = request.user
        if not is_favorited or not user.is_authenticated:
            return queryset
        recipe_content_type = ContentType.objects.get_for_model(queryset.model)
        favorite_recipe_ids = SpecialListModel.objects.filter(
            user=user,
            content_type=recipe_content_type,
            list_name=LIST_NAME_CHOICES[0],
        ).values_list('object_id', flat=True)
        return queryset.filter(id__in=favorite_recipe_ids)

    is_in_shopping_cart = filter.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        request = self.request
        is_in_shopping_cart = request.GET.get('is_in_shopping_cart')
        user = request.user
        if not is_in_shopping_cart or not user.is_authenticated:
            return queryset
        recipe_content_type = ContentType.objects.get_for_model(queryset.model)
        in_shopping_cart_recipe_ids = SpecialListModel.objects.filter(
            user=user,
            content_type=recipe_content_type,
            list_name=LIST_NAME_CHOICES[2],
        ).values_list('object_id', flat=True)
        return queryset.filter(id__in=in_shopping_cart_recipe_ids)

    class Meta:
        model = Recipe
        fields = {
            'author': ('exact',),
        }


def get_is_in_special_list(object, user, list_name_choice):
    return user.is_authenticated and (
        SpecialListModel.objects.filter(
            user=user,
            object_id=object.id,
            content_type_id=ContentType.objects.get_for_model(
                object.__class__
            ),
            list_name=list_name_choice,
        )
    ).exists()


def get_filtered_by_special_field_queryset(
    queryset,
    user,
    list_name_choice,
):
    return queryset.filter(
        id__in=SpecialListModel.objects.filter(
            user=user,
            content_type_id=ContentType.objects.get_for_model(
                queryset.model
            ),
            list_name=list_name_choice,
        ).values_list('object_id', flat=True)
    )
