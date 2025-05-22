import hashlib

from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import NameSearchFilter, RecipeFilter
from api.pagination import PageLimitPagination
from api.permissions import IsAuthor
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    PasswordSerializer,
    RecipeFavoriteAndShoppingCartSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscribeSerializer,
    SubscribeUserSerializer,
    TagSerializer,
    UserReadSerializer,
    UserWriteSerializer,
)
from recipes.constants import (
    AVATAR_URL,
    DOWNLOAD_SHOPPING_CART_URL,
    FAVORITE_URL,
    GET_LINK_URL,
    SELF_URL,
    SET_PASSWORD_URL,
    SHOPPING_CART_FILENAME,
    SHOPPING_CART_URL,
    SHORT_LINK_MAX_LENGTH,
    SUBSCRIBE_URL,
    SUBSCRIPTIONS_URL,
)
from recipes.models import Ingredient, Recipe, ShortLink, Tag, User


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
        if self.request.method == 'POST':
            return (AllowAny(),)
        return (IsAuthenticatedOrReadOnly(),)

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
        url_path=SUBSCRIBE_URL,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        subscribed_user = get_object_or_404(
            self.get_queryset(),
            pk=id
        )
        user = request.user
        serializer = SubscribeSerializer(
            data={
                'user': user.id,
                'subscribed_user': subscribed_user.id
            },
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if request.method == 'POST':
            queryset = self.get_recipes_annotated_queryset(
                queryset=self.get_queryset().filter(id=subscribed_user.id)
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
        url_path=SUBSCRIPTIONS_URL,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        queryset = self.get_recipes_annotated_queryset(
            queryset=User.objects.filter(
                id__in=request.user.subscriptions.all().values_list(
                    'user_id',
                    flat=True
                )
            )
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
        url_path=SELF_URL,
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
        url_path=AVATAR_URL,
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
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        url_path=SET_PASSWORD_URL,
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
        url_path=GET_LINK_URL,
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
        short_link = f'https://{settings.DOMAIN}/s/{short_link_object.code}'
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )

    def add_or_delete_from_special_list(
        self,
        request,
        recipe_id,
        serializer,
    ):
        recipe = get_object_or_404(
            self.get_queryset(),
            pk=recipe_id
        )
        user = request.user
        serializer = serializer(
            data={
                'user': user.id,
                'recipe': recipe.id,
            },
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
        url_path=SHOPPING_CART_URL,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, id=None):
        return self.add_or_delete_from_special_list(
            request=request,
            recipe_id=id,
            serializer=ShoppingCartSerializer,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path=FAVORITE_URL,
    )
    def favorite(self, request, id=None):
        return self.add_or_delete_from_special_list(
            request=request,
            recipe_id=id,
            serializer=FavoriteSerializer,
        )

    @action(
        detail=False,
        methods=['get'],
        url_path=DOWNLOAD_SHOPPING_CART_URL,
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        recipe_ids = request.user.shopping_cart.all().values_list(
            'recipe',
            flat=True
        )
        recipe_queryset = Recipe.objects.filter(id__in=recipe_ids)
        shopping_cart = dict()
        for recipe in recipe_queryset:
            for ingredient_recipe in recipe.recipe_ingredients.all():
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
            f'filename={SHOPPING_CART_FILENAME}'
        )
        return response
