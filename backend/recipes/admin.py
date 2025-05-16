from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Ingredient, Recipe, ShoppingCart, ShortLink,
                     Subscription, Tag, User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar',
    )
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'cooking_time',
        'favorites_count',
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    empty_value_display = '-пусто-'

    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'В избранном'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('favorites'))


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_recipe')

    def get_recipe(self, obj):
        return obj.content_object
    get_recipe.short_description = 'Рецепт'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_recipe')

    def get_recipe(self, obj):
        return obj.content_object
    get_recipe.short_description = 'Рецепт'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_author')

    def get_author(self, obj):
        return obj.content_object
    get_author.short_description = 'Автор'


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'code')
