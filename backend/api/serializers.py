from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import (
    AVATAR_FIELD_NAME,
    FAVORITE_FOR_SERIALIZER,
    IMAGE_FIELD_NAME,
    SHOPPING_CART_FOR_SERIALIZER,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Subscribe,
    Tag,
    User,
)


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


def absolute_url_representation(representation, serializer, image_name):
    request = serializer.context['request']
    image_url = representation[image_name]
    representation[image_name] = request.build_absolute_uri(image_url)
    return representation


class ToRepresentationImageSerializer(serializers.Serializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context['request']
        image_url = representation.get(self.image_name)
        if image_url:
            representation[self.image_name] = request.build_absolute_uri(
                image_url
            )
        return representation


class UserReadSerializer(
    serializers.ModelSerializer,
    ToRepresentationImageSerializer,
):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    image_name = AVATAR_FIELD_NAME

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, user):
        return get_is_in_special_list(
            object=user,
            user=self.context['request'].user,
            model=Subscribe,
            is_recipe=False
        )


class UserWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class SubscribeRecipeSerializer(
    serializers.ModelSerializer,
    ToRepresentationImageSerializer,
):
    image_name = AVATAR_FIELD_NAME

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscribeUserSerializer(
    UserReadSerializer,
):
    image_name = AVATAR_FIELD_NAME
    recipes = SubscribeRecipeSerializer(
        many=True,
        read_only=True
    )
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserReadSerializer.Meta):
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, user):
        return get_is_in_special_list(
            object=user,
            user=self.context['request'].user,
            model=Subscribe,
            is_recipe=False
        )

    def to_representation(self, user):
        representation = super().to_representation(user)
        recipes_limit = self.context['recipes_limit']
        if recipes_limit:
            representation['recipes'] = (
                representation['recipes'][:int(recipes_limit)]
            )
        return representation


class AvatarSerializer(
    serializers.ModelSerializer,
    ToRepresentationImageSerializer,
):
    image_name = AVATAR_FIELD_NAME
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    current_password = serializers.CharField(write_only=True)

    def validate_current_password(self, current_password):
        user = self.context['request'].user
        if not user.check_password(current_password):
            raise serializers.ValidationError('Текущий пароль неверен.')
        return current_password

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'amount',
        )


class RecipeReadSerializer(
    serializers.ModelSerializer,
    ToRepresentationImageSerializer,
):
    image_name = IMAGE_FIELD_NAME
    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    ingredients = IngredientRecipeReadSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, recipe):
        return get_is_in_special_list(
            object=recipe,
            user=self.context['request'].user,
            model=Favorite,
            is_recipe=True
        )

    def get_is_in_shopping_cart(self, recipe):
        return get_is_in_special_list(
            object=recipe,
            user=self.context['request'].user,
            model=ShoppingCart,
            is_recipe=True
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
        source='recipe_ingredients'
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('recipe_ingredients')
        image = data.get('image')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно указать хотя бы один тег'
            })
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны повторяться'
            })
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужно указать хотя бы один ингредиент'
            })
        ingredient_ids = set()
        for item in ingredients:
            ing_id = item.get('id')
            amount = item.get('amount')
            if ing_id in ingredient_ids:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты не должны повторяться'
                })
            ingredient_ids.add(ing_id)
            if not Ingredient.objects.filter(id=ing_id).exists():
                raise serializers.ValidationError({
                    'ingredients': f'Ингредиент с id={ing_id} не найден'
                })
            if amount <= 0:
                raise serializers.ValidationError({
                    'ingredients': 'Количество должно быть больше 0'
                })
        if not image:
            raise serializers.ValidationError({
                'image': 'Поле image обязательно'
            })
        return data

    def create_or_update(self, validated_data, recipe=None):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        if recipe:
            for attr, value in validated_data.items():
                setattr(recipe, attr, value)
            recipe.save()
            current_tags = recipe.tags.all()
            for current_tag in current_tags:
                if current_tag.id not in tags:
                    current_tag.delete()
            current_ingredients = (
                IngredientRecipe.objects.filter(recipe_id=recipe.id)
            )
            for current_ingredient in current_ingredients:
                if current_ingredient.ingredient.id not in (
                    ingredient_dict['id']
                    for ingredient_dict in ingredients
                ):
                    current_ingredient.delete()
        else:
            recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            tag = get_object_or_404(
                Tag,
                id=tag.id
            )
            recipe.tags.add(tag)
        for ingredient_dict in ingredients:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_dict['id']
            )
            IngredientRecipe.objects.create(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                amount=ingredient_dict['amount']
            )
        return recipe

    def create(self, validated_data):
        return self.create_or_update(validated_data=validated_data)

    def update(self, recipe, validated_data):
        return self.create_or_update(
            validated_data=validated_data,
            recipe=recipe,
        )

    def to_representation(self, recipe):
        return RecipeReadSerializer(
            recipe,
            context=self.context,
        ).data


class RecipeFavoriteAndShoppingCartSerializer(
    serializers.ModelSerializer,
    ToRepresentationImageSerializer,
):
    image_name = IMAGE_FIELD_NAME

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ValidatedSpecialListSerializer(serializers.Serializer):

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if self.favorite:
            recipes = Recipe.objects.filter(
                in_favorites__user=user
            )
        else:
            recipes = Recipe.objects.filter(
                in_shopping_cart__user=user
            )
        if self.context['request'].method == 'POST':
            if recipe in recipes:
                raise serializers.ValidationError(
                    f'Данный рецепт уже в {self.list_name}'
                )
            return super().validate(data)
        if recipe not in recipes:
            raise serializers.ValidationError(
                f'Данный рецепт отсутствует в {self.list_name}'
            )
        return super().validate(data)


class FavoriteSerializer(
    ValidatedSpecialListSerializer,
    serializers.ModelSerializer
):
    list_name = FAVORITE_FOR_SERIALIZER
    favorite = True

    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe',
        )


class ShoppingCartSerializer(
    ValidatedSpecialListSerializer,
    serializers.ModelSerializer
):
    list_name = SHOPPING_CART_FOR_SERIALIZER
    favorite = False

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe',
        )


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscribe
        fields = (
            'user',
            'subscribed_user',
        )

    def validate(self, data):
        user = data.get('user')
        subscribed_user = data.get('subscribed_user')
        request = self.context['request']
        if user == subscribed_user:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя'
            )
        subscriptions = User.objects.filter(
            subscribers__user=user
        )
        if request.method == 'POST':
            if subscribed_user in subscriptions:
                raise serializers.ValidationError(
                    'Данный пользователь уже в подписках'
                )
            return super().validate(data)
        if subscribed_user not in subscriptions:
            raise serializers.ValidationError(
                'Данного пользователя нет в подписках'
            )
        return super().validate(data)
