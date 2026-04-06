# Defino las rutas de la aplicación gastos, el int:pk es el id del gasto
# es un numero entero
from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('gastos/', views.lista_gastos, name='lista_gastos'),
    path('gastos/nuevo/', views.nuevo_gasto, name='nuevo_gasto'),
    path('gastos/<int:pk>/pagar/', views.marcar_pagado, name='marcar_pagado'),
    path('gastos/<int:pk>/editar/', views.editar_gasto, name='editar_gasto'),
    path('gastos/<int:pk>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/agregar/', views.agregar_compra, name='agregar_compra'),
    path('compras/<int:pk>/toggle/', views.toggle_compra, name='toggle_compra'),
    path('compras/limpiar/', views.limpiar_comprados, name='limpiar_comprados'),
]