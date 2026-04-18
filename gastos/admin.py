
from django.contrib import admin
from .models import (
    Gasto, Categoria, ItemCompra,
    PagoRecurrente, Ingreso,
    Prestamo, PagoPrestamo,
    MetaAhorro, AporteMeta,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'icono', 'color']


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'categoria', 'fecha', 'prioridad', 'estado']
    list_filter = ['estado', 'prioridad', 'categoria']
    search_fields = ['descripcion']


@admin.register(ItemCompra)
class ItemCompraAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cantidad', 'comprado', 'usuario']
    list_filter = ['comprado']


@admin.register(PagoRecurrente)
class PagoRecurrenteAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'frecuencia', 'dia_pago', 'activo']
    list_filter = ['frecuencia', 'activo']


@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'tipo', 'fecha', 'es_fijo']
    list_filter = ['tipo', 'es_fijo']


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ['persona', 'concepto', 'monto_total', 'monto_pagado', 'tipo', 'estado']
    list_filter = ['tipo', 'estado']
    search_fields = ['persona', 'concepto']


@admin.register(PagoPrestamo)
class PagoPrestamoAdmin(admin.ModelAdmin):
    list_display = ['prestamo', 'monto', 'fecha', 'notas']


@admin.register(MetaAhorro)
class MetaAhorroAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'monto_objetivo', 'icono', 'fecha_objetivo', 'activa']
    list_filter = ['activa']


@admin.register(AporteMeta)
class AporteMetaAdmin(admin.ModelAdmin):
    list_display = ['meta', 'monto', 'fecha']
