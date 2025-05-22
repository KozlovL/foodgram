from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from recipes.models import (Favorite, Ingredient, Recipe, ShortLink, Subscribe,
                            Tag, User, IngredientRecipe)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
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


class IngredientRecipeInline(admin.StackedInline):
    model = IngredientRecipe
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'cooking_time',
        'favorites_count',
    )
    inlines = (
        IngredientRecipe,
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    empty_value_display = '-пусто-'

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return Favorite.objects.filter(
            recipe=obj
        ).count()


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'get_subscribed_user_recipes',
        'get_subscribed_user'
    )

    @admin.display(description='Кол-во рецептов')
    def get_subscribed_user_recipes(self, obj):
        return obj.subscribed_user.recipes.count()

    @admin.display(description='Подписан на пользователя')
    def get_subscribed_user(self, obj):
        return obj.subscribed_user.username


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'code')
