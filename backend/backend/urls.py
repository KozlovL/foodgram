from api.views import short_link_redirect
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:code>/', short_link_redirect, name='short_link_redirect'),
]
