from django.contrib import admin
from django.urls import include, path
from recipes.views import (RecipeViewSet, TagViewSet, UserViewSet,
                           short_link_redirect, IngredientViewSet)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include(router.urls))
]

urlpatterns += [
    path('s/<str:code>/', short_link_redirect, name='short_link_redirect'),
]
