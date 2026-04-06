
#registra modelos en el panel de admin de Django 
# para que puedan ser gestionados fácilmente a través de la interfaz de administración.
# Esto incluye la personalización de cómo se muestran los modelos, qué campos se pueden buscar y filtrar, etc.
from django.contrib import admin
from .models import Gasto, Categoria, ItemCompra

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