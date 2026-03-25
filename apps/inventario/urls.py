from django.urls import path

from apps.inventario.views import (
    inventarioReadView,
    inventarioCreateView,
)

app_name = 'inventario'
urlpatterns = [
    path('',inventarioReadView, name='inventario'),
    path('crear', inventarioCreateView, name='crear_inventario'),
]
