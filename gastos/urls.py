from django.urls import path
from . import views

urlpatterns = [
    # Inicio
    path('', views.inicio, name='inicio'),

    # Gastos
    path('gastos/', views.lista_gastos, name='lista_gastos'),
    path('gastos/nuevo/', views.nuevo_gasto, name='nuevo_gasto'),
    path('gastos/<int:pk>/pagar/', views.marcar_pagado, name='marcar_pagado'),
    path('gastos/<int:pk>/editar/', views.editar_gasto, name='editar_gasto'),
    path('gastos/<int:pk>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),

    # Compras
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/agregar/', views.agregar_compra, name='agregar_compra'),
    path('compras/<int:pk>/toggle/', views.toggle_compra, name='toggle_compra'),
    path('compras/limpiar/', views.limpiar_comprados, name='limpiar_comprados'),
    path('compras/exportar/', views.exportar_compras_excel, name='exportar_compras_excel'),  # Nueva ruta para exportar a Excel
    path('compras/<int:pk>/editar/', views.editar_compra, name='editar_compra'),

    # Recurrentes
    path('recurrentes/', views.lista_recurrentes, name='lista_recurrentes'),
    path('recurrentes/nuevo/', views.nuevo_recurrente, name='nuevo_recurrente'),
    path('recurrentes/<int:pk>/eliminar/', views.eliminar_recurrente, name='eliminar_recurrente'),
    path('recurrentes/<int:pk>/pagar-cuota/', views.pagar_cuota_mes, name='pagar_cuota_mes'),
    path('recurrentes/<int:pk>/editar/', views.editar_recurrente, name='editar_recurrente'),

    # Ingresos
    path('ingresos/', views.lista_ingresos, name='lista_ingresos'),
    path('ingresos/nuevo/', views.nuevo_ingreso, name='nuevo_ingreso'),
    path('ingresos/<int:pk>/eliminar/', views.eliminar_ingreso, name='eliminar_ingreso'),

    # Préstamos
    path('prestamos/', views.lista_prestamos, name='lista_prestamos'),
    path('prestamos/nuevo/', views.nuevo_prestamo, name='nuevo_prestamo'),
    path('prestamos/<int:pk>/pagar/', views.registrar_pago_prestamo, name='registrar_pago_prestamo'),
    path('prestamos/<int:pk>/eliminar/', views.eliminar_prestamo, name='eliminar_prestamo'),
    path('prestamos/<int:pk>/detalle/', views.detalle_prestamo, name='detalle_prestamo'),

    # Metas de ahorro
    path('metas/', views.lista_metas, name='lista_metas'),
    path('metas/nueva/', views.nueva_meta, name='nueva_meta'),
    path('metas/<int:pk>/aporte/', views.registrar_aporte, name='registrar_aporte'),
    path('metas/<int:pk>/eliminar/', views.eliminar_meta, name='eliminar_meta'),
    path('metas/<int:pk>/archivar/', views.archivar_meta, name='archivar_meta'),

    # Registro
    path('registro/', views.registro, name='registro'),

    #categorias 
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.nueva_categoria, name='nueva_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:pk>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
]
