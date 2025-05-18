from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from recipes.constants import LIST_NAME_CHOICES
from recipes.models import (Ingredient, Recipe, ShortLink, SpecialListModel,
                            Tag, User)


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
        return SpecialListModel.objects.filter(
            content_type=ContentType.objects.get_for_model(obj.__class__),
            object_id=obj.id,
            list_name=LIST_NAME_CHOICES[0]
        ).count()
    favorites_count.short_description = 'В избранном'


@admin.register(SpecialListModel)
class SpecialListAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'get_recipe',
        'get_user'
    )

    def get_recipe(self, obj):
        return obj.content_object
    get_recipe.short_description = 'Рецепт'

    def get_user(self, obj):
        return obj.content_object
    get_user.short_description = 'Пользователь в подписках'


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'code')
