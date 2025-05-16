from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from recipes.constants import (AVATAR_IMAGE_FOLDER, EMAIL_MAX_LENGTH,
                               MEASUREMENT_UNIT_MAX_LENGTH, MIN_COOKING_TIME,
                               NAME_MAX_LENGTH, NAME_STR_WIDTH,
                               RECIPE_IMAGE_FOLDER, SHORT_LINK_MAX_LENGTH,
                               TAG_SLUG_MAX_LENGTH)


class User(AbstractUser):
    username = models.CharField(
        unique=True,
        max_length=NAME_MAX_LENGTH,
        validators=[
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
        default=None,
        verbose_name='Аватар'
    )
    subscriptions = GenericRelation('Subscription')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


class SpecialListModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )

    class Meta:
        abstract = True
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'user',
                    'object_id',
                    'content_type'
                ],
                name='unique_user_%(class)s_object_id'
            )
        ]


class Favorite(SpecialListModel):

    class Meta(SpecialListModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class Subscription(SpecialListModel):

    class Meta(SpecialListModel.Meta):
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class ShoppingCart(SpecialListModel):

    class Meta(SpecialListModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


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
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    image = models.ImageField(
        upload_to=RECIPE_IMAGE_FOLDER,
        verbose_name='Картинка'
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        verbose_name='Тэги'
    )
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        verbose_name='Время приготовления'
    )
    favorites = GenericRelation(
        'Favorite'
    )
    shopping_carts = GenericRelation(
        'ShoppingCart'
    )

    class Meta(NameModel.Meta):
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        verbose_name='Количество',
    )


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE
    )
    code = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH,
        unique=True,
        verbose_name='Код',
    )
