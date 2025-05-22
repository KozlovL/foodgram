from django_filters import rest_framework as filter
from recipes.models import Recipe, Tag
from rest_framework import filters


class NameSearchFilter(filters.SearchFilter):
    search_param = 'name'


class RecipeFilter(filter.FilterSet):
    tags = filter.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        method='filter_tags'
    )

    def filter_tags(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(tags__in=value).distinct()

    is_favorited = filter.NumberFilter(method='filter_favorited')

    def filter_favorited(self, queryset, name, value):
        request = self.request
        is_favorited = request.GET.get('is_favorited')
        user = request.user
        if not is_favorited or not user.is_authenticated:
            return queryset
        favorite_recipe_ids = user.favorites.all().values_list(
            'recipe__id',
            flat=True
        )
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
        in_shopping_cart_recipe_ids = user.shopping_cart.all().values_list(
            'recipe__id',
            flat=True
        )
        return queryset.filter(id__in=in_shopping_cart_recipe_ids)

    class Meta:
        model = Recipe
        fields = {
            'author': ('exact',),
        }


def get_is_in_special_list(object, user, model, is_recipe):
    if is_recipe:
        return user.is_authenticated and (
            model.objects.filter(
                user=user,
                recipe=object,
            )
        ).exists()
    return user.is_authenticated and (
        model.objects.filter(
            user=user,
            subscribed_user=object,
        )
    ).exists()
