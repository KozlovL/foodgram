from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Subscription, Tag, TagRecipe, User)
from rest_framework import serializers


def absolute_url_representation(representation, serializer, image):
    request = serializer.context['request']
    image_url = representation[image]
    representation[image] = request.build_absolute_uri(image_url)
    return representation


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

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
        request_user = self.context.get('request').user
        return request_user.is_authenticated and Subscription.objects.filter(
            user=request_user,
            object_id=user.id
        ).exists()


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


class SubscribeRecipeSerializer(serializers.ModelSerializer):

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

    def to_representation(self, user):
        representation = super().to_representation(user)
        return absolute_url_representation(representation, self, 'image')


class SubscribeUserSerializer(UserReadSerializer):
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
        request_user = self.context.get('request').user
        if not request_user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request_user,
            object_id=user.id
        ).exists()

    def to_representation(self, user):
        representation = super().to_representation(user)
        recipes_limit = self.context['recipes_limit']
        if recipes_limit:
            representation['recipes'] = (
                representation['recipes'][:int(recipes_limit)]
            )
        return absolute_url_representation(representation, self, 'avatar')


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, user):
        representation = super().to_representation(user)
        return absolute_url_representation(representation, self, 'avatar')


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


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    ingredients = IngredientRecipeReadSerializer(
        many=True,
        read_only=True,
        source='ingredientrecipe_set'
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
        user = self.context['request'].user
        return user.is_authenticated and Favorite.objects.filter(
            user=user,
            object_id=recipe.id
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return user.is_authenticated and ShoppingCart.objects.filter(
            user=user,
            object_id=recipe.id
        ).exists()

    def to_representation(self, recipe):
        representation = super().to_representation(recipe)
        return absolute_url_representation(representation, self, 'image')


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
        source='ingredientrecipe_set'
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context['request'].method == 'PATCH':
            self.fields['image'].required = False

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredientrecipe_set')
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

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientrecipe_set')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            tag = get_object_or_404(
                Tag,
                id=tag.id
            )
            TagRecipe.objects.create(
                recipe_id=recipe.id,
                tag_id=tag.id
            )
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

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientrecipe_set')
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()
        current_tags = (
            TagRecipe.objects.filter(recipe_id=recipe.id)
        )
        for current_tag in current_tags:
            if current_tag.tag.id not in tags:
                current_tag.delete()
        for tag in tags:
            tag = get_object_or_404(
                Tag,
                id=tag.id
            )
            TagRecipe.objects.create(
                recipe_id=recipe.id,
                tag_id=tag.id
            )
        current_ingredients = (
            IngredientRecipe.objects.filter(recipe_id=recipe.id)
        )
        for current_ingredient in current_ingredients:
            if current_ingredient.ingredient.id not in (
                ingredient_dict['id']
                for ingredient_dict in ingredients
            ):
                current_ingredient.delete()
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

    def to_representation(self, recipe):
        return RecipeReadSerializer(
            recipe,
            context=self.context,
        ).data


class RecipeFavoriteAndShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def to_representation(self, user):
        representation = super().to_representation(user)
        return absolute_url_representation(representation, self, 'image')
