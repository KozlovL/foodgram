import hashlib

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from recipes.constants import SHORT_LINK_MAX_LENGTH
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            ShortLink, Subscription, Tag, User)
from recipes.pagination import PageLimitPagination
from recipes.permissions import IsAuthor
from recipes.serializers import (AvatarSerializer, IngredientSerializer,
                                 PasswordSerializer,
                                 RecipeFavoriteAndShoppingCartSerializer,
                                 RecipeReadSerializer, RecipeWriteSerializer,
                                 SubscribeUserSerializer, TagSerializer,
                                 UserReadSerializer, UserWriteSerializer)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response


def short_link_redirect(request, code):
    short_link = get_object_or_404(ShortLink, code=code)
    return redirect(f'https://localhost/recipes/{short_link.recipe.id}/')


class SpecialListManager:
    def toggle_special(
        self,
        request,
        instance,
        special_list_model,
    ):
        content_type = ContentType.objects.get_for_model(instance)
        if request.method == 'POST':
            object, created = special_list_model.objects.get_or_create(
                user=request.user,
                content_type=content_type,
                object_id=instance.id
            )
            if created:
                return True
            return False
        else:
            object = special_list_model.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=instance.id
            )
            if object.exists():
                object.delete()
                return True
            return False

    def annotate_queryset_is_special_field(
        self,
        request,
        special_list_model,
        queryset,
        field_name
    ):
        user = request.user if request.user.is_authenticated else None
        is_special_subquery = special_list_model.objects.filter(
            object_id=OuterRef('pk'),
            user=user,
            content_type=ContentType.objects.get_for_model(queryset.model)
        )
        queryset = queryset.annotate(**{
            field_name: Exists(is_special_subquery)
        })
        return queryset


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    lookup_field = 'id'
    ordering = ('username',)
    pagination_class = PageLimitPagination
    http_method_names = ['get', 'post', 'put', 'delete']

    special_list_helper = SpecialListManager()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserWriteSerializer
        return UserReadSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['recipes_limit'] = (
            self.request.query_params.get('recipes_limit')
        )
        return context

    def get_queryset(self):
        queryset = User.objects.all()
        queryset = (
            self.special_list_helper.annotate_queryset_is_special_field
        )(
            special_list_model=Subscription,
            queryset=queryset,
            field_name='is_subscribed',
            request=self.request
        )
        return queryset

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        user = get_object_or_404(
            User,
            pk=id
        )
        if request.user == user:
            return Response(
                {'message': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not self.special_list_helper.toggle_special(
            request=request,
            instance=user,
            special_list_model=Subscription,
        ):
            if request.method == 'POST':
                message = 'Данный пользователь уже добавлен в подписки'
            else:
                message = 'Данный пользователь отсутствует в подписках'
            return Response(
                {
                    'message': message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            queryset = self.get_queryset().filter(id=user.id).annotate(
                recipes_count=Count('recipes')
            ).order_by(*User._meta.ordering)
            serializer = SubscribeUserSerializer(
                queryset.first(),
                context=self.get_serializer_context(),
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        queryset = self.get_queryset().filter(is_subscribed=True).annotate(
            recipes_count=Count('recipes')
        ).order_by(*User._meta.ordering)
        page = self.paginate_queryset(queryset)
        serializer = SubscribeUserSerializer(
            page if page is not None else queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        if page:
            return self.get_paginated_response(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        queryset = self.get_queryset().filter(id=request.user.id).first()
        serializer = self.get_serializer(queryset)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        url_path='set_password',
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        user = request.user
        serializer = PasswordSerializer(
            user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']
    permission_classes = (AllowAny,)
    lookup_field = 'id'
    ordering = ('name',)


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    http_method_names = ['get']
    permission_classes = (AllowAny,)
    lookup_field = 'id'
    ordering = ('name',)

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'id'
    ordering = ('name',)
    pagination_class = PageLimitPagination

    special_list_helper = SpecialListManager()

    def get_permissions(self):
        if self.request.method in ('PATCH', 'DELETE'):
            return (IsAuthor(),)
        return (IsAuthenticatedOrReadOnly(),)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        request = self.request
        context['request'] = request
        return context

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        request = self.request
        queryset = (
            self.special_list_helper.annotate_queryset_is_special_field
        )(
            special_list_model=Favorite,
            queryset=queryset,
            field_name='is_favorited',
            request=request
        )
        queryset = (
            self.special_list_helper.annotate_queryset_is_special_field
        )(
            special_list_model=ShoppingCart,
            queryset=queryset,
            field_name='is_in_shopping_cart',
            request=request
        )
        if self.action == 'list':
            query_params = request.query_params
            bool_query_filters = ('is_favorited', 'is_in_shopping_cart')
            filters = {}
            for field in bool_query_filters:
                value = query_params.get(field)
                if value is not None:
                    filters[field] = value == '1'
            author_filter = query_params.get('author')
            if author_filter is not None:
                filters['author'] = int(author_filter)
            tags_filter = query_params.getlist('tags')
            if tags_filter:
                queryset = queryset.filter(tags__slug__in=tags_filter)
            if filters:
                queryset = queryset.filter(**filters)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, id=None):
        recipe = get_object_or_404(
            Recipe,
            id=id
        )
        short_link_object, created = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'code': hashlib.md5(
                str(recipe.id).encode()
            ).hexdigest()[:SHORT_LINK_MAX_LENGTH]}
        )
        domain = 'localhost'
        short_link = f"{domain}/s/{short_link_object.code}"
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )

    def add_or_delete_from_special_list(
        self,
        request,
        id,
        special_list_model
    ):
        recipe = get_object_or_404(
            Recipe,
            pk=id
        )
        if not self.special_list_helper.toggle_special(
            request=request,
            instance=recipe,
            special_list_model=special_list_model,
        ):
            if request.method == 'POST':
                message = (
                    f'Данный рецепт уже добавлен в '
                    f'{special_list_model._meta.verbose_name}'
                )
            else:
                message = (
                    f'Данный рецепт отсутствует в '
                    f'{special_list_model._meta.verbose_name}'
                )
            return Response(
                {
                    'message':
                    message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            serializer = RecipeFavoriteAndShoppingCartSerializer(
                recipe,
                context=self.get_serializer_context()
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, id=None):
        return self.add_or_delete_from_special_list(
            request,
            id,
            ShoppingCart,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, id=None):
        return self.add_or_delete_from_special_list(
            request,
            id,
            Favorite,
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        queryset = self.get_queryset().filter(is_in_shopping_cart=True)
        shopping_cart = dict()
        for recipe in queryset:
            for ingredient_recipe in recipe.ingredientrecipe_set.all():
                name = ingredient_recipe.ingredient.name
                if name not in shopping_cart.keys():
                    shopping_cart[name] = {
                        'Количество': 0,
                        'Единица измерения': (
                            ingredient_recipe.ingredient.measurement_unit
                        )
                    }
                shopping_cart[name]['Количество'] += (
                    ingredient_recipe.amount
                )
        shop_list = ''
        for name, value in shopping_cart.items():
            count = value['Количество']
            measurement_unit = value['Единица измерения']
            shop_list += f'{name}: {count} {measurement_unit}\n'
        response = HttpResponse(shop_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment;'
            'filename="shopping_cart.txt"'
        )
        return response
