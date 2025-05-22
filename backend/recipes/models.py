from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from recipes.constants import (
    AVATAR_IMAGE_FOLDER,
    EMAIL_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    MIN_COOKING_TIME,
    NAME_MAX_LENGTH,
    NAME_STR_WIDTH,
    RECIPE_IMAGE_FOLDER,
    SHORT_LINK_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
    USERNAME_STR_WIDTH,
)


class User(AbstractUser):
    username = models.CharField(
        unique=True,
        max_length=NAME_MAX_LENGTH,
        validators=[
            UnicodeUsernameValidator,
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
            )
        ],
        verbose_name='Никнейм'
    )
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH
    )
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH
    )
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Почта'
    )
    avatar = models.ImageField(
        upload_to=AVATAR_IMAGE_FOLDER,
        null=True,
        default='',
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        default_related_name = 'users'

    def __str__(self):
        return self.username[:USERNAME_STR_WIDTH]


class NameModel(models.Model):
    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        verbose_name='Название'
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name[:NAME_STR_WIDTH]


class Ingredient(NameModel):
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta(NameModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'name',
                    'measurement_unit',
                ],
                name='unique_ingredient_measurement_unit'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Tag(NameModel):
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        verbose_name='Слаг'
    )

    class Meta(NameModel.Meta):
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'


class Recipe(NameModel):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    image = models.ImageField(
        upload_to=RECIPE_IMAGE_FOLDER,
        verbose_name='Картинка'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        verbose_name='Время приготовления'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta(NameModel.Meta):
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        verbose_name='Количество',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'recipe',
                    'ingredient',
                ],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'Рецепт - {self.recipe}. '
            f'Ингредиент - {self.ingredient}. '
            f'Кол-во - {self.amount}.'
        )


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    code = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH,
        unique=True,
        verbose_name='Код',
    )

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        default_related_name = 'short_links'

    def __str__(self):
        return f'https://{settings.DOMAIN}/s/{self.code}'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписывающийся пользователь'
    )

    subscribed_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписываемый пользователь'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (
            f'Подписывающийся пользователь - {self.user}. '
            f'Подписываемый пользователь - {self.subscribed_user}.'
        )


class SpecialListRecipeModel(models.Model):

    class Meta:
        abstract = True
        verbose_name = 'Специальный список с полем "рецепт"'
        verbose_name_plural = 'Специальные списки с полем "рецепт"'

    def __str__(self):
        return (
            f'Пользователь - {self.user}. '
            f'Рецепт - {self.recipe}.'
        )


class Favorite(SpecialListRecipeModel):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='in_favorites'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )

    class Meta(SpecialListRecipeModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(SpecialListRecipeModel):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='in_shopping_cart'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )

    class Meta(SpecialListRecipeModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
