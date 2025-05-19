import hashlib

from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from recipes.constants import LIST_NAME_CHOICES, SHORT_LINK_MAX_LENGTH
from recipes.filters import (NameSearchFilter, RecipeFilter,
                             get_filtered_by_special_field_queryset)
from recipes.models import (Ingredient, Recipe, ShortLink, Tag, User,
                            toggle_special)
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
    return redirect(
        f'https://{settings.DOMAIN}/recipes/{short_link.recipe.id}/'
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    lookup_field = 'id'
    ordering = ('username',)
    pagination_class = PageLimitPagination
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_permissions(self):
        if self.request.method == 'GET':
            return (IsAuthenticatedOrReadOnly,)
        return (IsAuthenticated,)

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

    def get_recipes_annotated_queryset(
            self,
            queryset,
    ):
        return queryset.annotate(
            recipes_count=Count('recipes')
        ).order_by(*User._meta.ordering)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = get_object_or_404(
            self.get_queryset(),
            pk=id
        )
        if request.user == user:
            return Response(
                {'message': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not toggle_special(
            request=request,
            instance=user,
            list_name_choice=LIST_NAME_CHOICES[1],
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
            queryset = self.get_recipes_annotated_queryset(
                queryset=self.get_queryset()
            )
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
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        queryset = self.get_recipes_annotated_queryset(
            queryset=self.get_queryset()
        )
        queryset = get_filtered_by_special_field_queryset(
            queryset=self.get_queryset(),
            user=request.user,
            list_name_choice=LIST_NAME_CHOICES[1],
        )
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
        serializer = self.get_serializer(request.user)
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
                context=self.get_serializer_context()
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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ['get']
    permission_classes = (AllowAny,)
    lookup_field = 'id'
    ordering = ('name',)
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'id'
    ordering = ('-pub_date',)
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

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
            self.get_queryset(),
            id=id
        )
        short_link_object, created = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'code': hashlib.md5(
                str(recipe.id).encode()
            ).hexdigest()[:SHORT_LINK_MAX_LENGTH]}
        )
        short_link = f'{settings.DOMAIN}/s/{short_link_object.code}'
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )

    def add_or_delete_from_special_list(
        self,
        request,
        id,
        list_name_choice,
    ):
        recipe = get_object_or_404(
            self.get_queryset(),
            pk=id
        )
        if not toggle_special(
            request=request,
            instance=recipe,
            list_name_choice=list_name_choice
        ):
            if request.method == 'POST':
                message = (
                    f'Данный рецепт уже добавлен в '
                    f'{list_name_choice[1]}'
                )
            else:
                message = (
                    f'Данный рецепт отсутствует в '
                    f'{list_name_choice[1]}'
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
    )
    def shopping_cart(self, request, id=None):
        return self.add_or_delete_from_special_list(
            request=request,
            id=id,
            list_name_choice=LIST_NAME_CHOICES[2],
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
    )
    def favorite(self, request, id=None):
        return self.add_or_delete_from_special_list(
            request=request,
            id=id,
            list_name_choice=LIST_NAME_CHOICES[0],
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        queryset = get_filtered_by_special_field_queryset(
            queryset=self.get_queryset(),
            user=request.user,
            list_name_choice=LIST_NAME_CHOICES[2],
        ).order_by(*Recipe._meta.ordering)
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
