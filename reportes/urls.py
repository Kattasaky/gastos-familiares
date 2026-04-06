# En este archivo defino las rutas de la aplicación reportes, que es donde se generan los reportes de gastos y estadísticas.
# Cada ruta apunta a una función en views.py que se encarga de generar el reporte correspondiente
from django.urls import path
from . import views

urlpatterns = [
    path('excel/', views.exportar_excel, name='exportar_excel'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]