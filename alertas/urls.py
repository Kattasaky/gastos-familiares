# En este archivo defino las rutas de la aplicación alertas, 
# que es donde se muestran las alertas de gastos próximos a vencer o que ya vencieron.

from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_alertas, name='alertas'),
]