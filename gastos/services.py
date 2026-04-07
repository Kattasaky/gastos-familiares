#quí vive toda la lógica de negocio — crear gastos, marcarlos como pagados, calcular resúmenes.
#Las vistas solo llaman estas funciones, no calculan nada solas.

from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Gasto, Categoria, ItemCompra


def crear_gasto(usuario, descripcion, monto, categoria_id=None,
                fecha=None, fecha_vencimiento=None,
                prioridad='normal', notas=''):
    if not descripcion or not descripcion.strip():
        raise ValueError("La descripción no puede estar vacía.")
    if Decimal(str(monto)) <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    gasto = Gasto.objects.create(
        usuario=usuario,
        descripcion=descripcion.strip(),
        monto=monto,
        categoria_id=categoria_id,
        fecha=fecha or timezone.now().date(),
        fecha_vencimiento=fecha_vencimiento,
        prioridad=prioridad,
        notas=notas,
    )
    return gasto


def marcar_pagado(gasto_id, usuario):
    gasto = Gasto.objects.get(id=gasto_id, usuario=usuario)
    gasto.estado = 'pagado'
    gasto.save(update_fields=['estado', 'actualizado_en'])
    return gasto


def actualizar_estados_vencidos():
    hoy = timezone.now().date()
    actualizados = Gasto.objects.filter(
        estado='pendiente',
        fecha_vencimiento__lt=hoy
    ).update(estado='vencido')
    return actualizados


def resumen_mensual(usuario, año, mes):
    gastos = Gasto.objects.filter(
        usuario=usuario,
        fecha__year=año,
        fecha__month=mes,
    )
    total = gastos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    por_categoria = (
        gastos.values('categoria__nombre', 'categoria__icono')
        .annotate(subtotal=Sum('monto'), cantidad=Count('id'))
        .order_by('-subtotal')
    )
    return {
        'año': año,
        'mes': mes,
        'total': total,
        'por_categoria': list(por_categoria),
        'cantidad_gastos': gastos.count(),
    }


def gastos_proximos_a_vencer(usuario, dias=7):
    hoy = timezone.now().date()
    limite = hoy + timezone.timedelta(days=dias)
    return Gasto.objects.filter(
        usuario=usuario,
        estado='pendiente',
        fecha_vencimiento__range=(hoy, limite),
    ).order_by('fecha_vencimiento')


def gastos_urgentes(usuario):
    return Gasto.objects.filter(
        usuario=usuario,
        prioridad='urgente',
        estado__in=['pendiente', 'vencido'],
    ).order_by('fecha_vencimiento')


def agregar_item_compra(usuario, nombre, cantidad=1, valor_aprox=None, categoria_id=None):
    if not nombre or not nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
    return ItemCompra.objects.create(
        usuario=usuario,
        nombre=nombre.strip(),
        cantidad=cantidad,
        valor_aprox=valor_aprox,
        categoria_id=categoria_id,
    )


def marcar_comprado(item_id, usuario):
    item = ItemCompra.objects.get(id=item_id, usuario=usuario)
    item.comprado = not item.comprado
    item.save(update_fields=['comprado'])
    return item


def limpiar_comprados(usuario):
    eliminados, _ = ItemCompra.objects.filter(usuario=usuario, comprado=True).delete()
    return eliminados