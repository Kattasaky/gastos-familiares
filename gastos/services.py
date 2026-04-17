#quí vive toda la lógica de negocio — crear gastos, marcarlos como pagados, calcular resúmenes.
#Las vistas solo llaman estas funciones, no calculan nada solas.

from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Gasto, Categoria, ItemCompra, PagoRecurrente, Ingreso, Prestamo, PagoPrestamo, MetaAhorro, AporteMeta


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
        fecha_vencimiento__isnull=False,
        fecha_vencimiento__range=(hoy, limite),
    ).order_by('fecha_vencimiento')


def gastos_urgentes(usuario):
    return Gasto.objects.filter(
        usuario=usuario,
        prioridad__in=['urgente', 'alta'],
        estado__in=['pendiente', 'vencido'],
    ).order_by('prioridad', 'fecha_vencimiento')
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

from .models import Gasto, Categoria, ItemCompra, PagoRecurrente, Ingreso

def crear_pago_recurrente(usuario, descripcion, dia_pago=None, monto=None,
                           categoria_id=None, frecuencia='mensual',
                           total_cuotas=None, prioridad='normal',
                           dia_semana=None):
    if not descripcion or not descripcion.strip():
        raise ValueError("La descripción no puede estar vacía.")
    if frecuencia == 'mensual' or frecuencia == 'cuotas':
        if not dia_pago:
            raise ValueError("Debes indicar el día del mes.")
        if not 1 <= int(dia_pago) <= 31:
            raise ValueError("El día debe estar entre 1 y 31.")
    return PagoRecurrente.objects.create(
        usuario=usuario,
        descripcion=descripcion.strip(),
        monto=monto or None,
        categoria_id=categoria_id,
        frecuencia=frecuencia,
        dia_pago=int(dia_pago) if dia_pago else None,
        dia_semana=int(dia_semana) if dia_semana else None,
        total_cuotas=total_cuotas or None,
        prioridad=prioridad,
    )

def generar_gastos_del_mes(usuario):
    from django.utils import timezone
    hoy = timezone.now().date()
    generados = 0

    pagos = PagoRecurrente.objects.filter(usuario=usuario, activo=True)
    for pago in pagos:
        if pago.total_cuotas and pago.cuotas_pagadas >= pago.total_cuotas:
            pago.activo = False
            pago.save()
            continue

        if pago.frecuencia == 'semanal':
            if pago.dia_semana is None:
                continue
            fecha_vencimiento = hoy
        else:
            if pago.dia_pago is None:
                continue
            dia = min(pago.dia_pago, 28)
            fecha_vencimiento = hoy.replace(day=dia)

        ya_existe = Gasto.objects.filter(
            usuario=usuario,
            descripcion=pago.descripcion,
            fecha__year=hoy.year,
            fecha__month=hoy.month,
        ).exists()

        if not ya_existe:
            Gasto.objects.create(
                usuario=usuario,
                descripcion=pago.descripcion,
                monto=pago.monto,
                categoria=pago.categoria,
                fecha=hoy,
                fecha_vencimiento=fecha_vencimiento,
                prioridad=pago.prioridad,
            )
            if pago.total_cuotas:
                pago.cuotas_pagadas += 1
                pago.save()
            generados += 1

    return generados

def crear_ingreso(usuario, descripcion, monto, tipo='sueldo',
                  fecha=None, es_fijo=False):
    if not descripcion or not descripcion.strip():
        raise ValueError("La descripción no puede estar vacía.")
    if float(monto) <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    from django.utils import timezone
    return Ingreso.objects.create(
        usuario=usuario,
        descripcion=descripcion.strip(),
        monto=monto,
        tipo=tipo,
        fecha=fecha or timezone.now().date(),
        es_fijo=es_fijo,
    )


def resumen_ingresos_mes(usuario, año, mes):
    from django.db.models import Sum
    ingresos = Ingreso.objects.filter(
        usuario=usuario,
        fecha__year=año,
        fecha__month=mes,
    )
    total = ingresos.aggregate(total=Sum('monto'))['total'] or 0
    por_tipo = ingresos.values('tipo').annotate(subtotal=Sum('monto'))
    return {
        'total': total,
        'por_tipo': list(por_tipo),
        'cantidad': ingresos.count(),
    }

def pagar_cuota_mes(usuario, pago_recurrente_id):
    from django.utils import timezone
    hoy = timezone.now().date()
    pago = PagoRecurrente.objects.get(id=pago_recurrente_id, usuario=usuario)
    gasto = Gasto.objects.filter(
        usuario=usuario,
        descripcion=pago.descripcion,
        fecha__year=hoy.year,
        fecha__month=hoy.month,
    ).first()
    if gasto:
        gasto.estado = 'pagado'
        gasto.save(update_fields=['estado', 'actualizado_en'])
    return gasto



def crear_prestamo(usuario, persona, concepto, monto_total,
                   tipo='recibido', fecha_prestamo=None,
                   fecha_vencimiento=None, notas=''):
    """
    Crea un préstamo nuevo.
    Validamos antes de tocar la base de datos — fail fast.
    """
    if not persona or not persona.strip():
        raise ValueError("El nombre de la persona no puede estar vacío.")
    if not concepto or not concepto.strip():
        raise ValueError("El concepto no puede estar vacío.")
    
    from decimal import Decimal
    if Decimal(str(monto_total)) <= 0:
        raise ValueError("El monto debe ser mayor a cero.")

    return Prestamo.objects.create(
        usuario=usuario,
        persona=persona.strip(),
        concepto=concepto.strip(),
        monto_total=monto_total,
        tipo=tipo,
        fecha_prestamo=fecha_prestamo or timezone.now().date(),
        fecha_vencimiento=fecha_vencimiento or None,
        notas=notas,
    )


def registrar_pago_prestamo(usuario, prestamo_id, monto, fecha=None, notas=''):
    """
    Registra un pago parcial o total de un préstamo.
    
    ¿Qué hace internamente?
    1. Busca el préstamo (y verifica que pertenezca al usuario — seguridad)
    2. Valida que no se pague más de lo adeudado
    3. Crea el registro de pago (historial)
    4. Actualiza el monto_pagado en el préstamo
    5. Si ya está saldado, cambia el estado automáticamente
    """
    from decimal import Decimal
    
    prestamo = Prestamo.objects.get(id=prestamo_id, usuario=usuario)
    monto = Decimal(str(monto))
    
    if monto <= 0:
        raise ValueError("El monto del pago debe ser mayor a cero.")
    
    if monto > prestamo.monto_adeudado:
        raise ValueError(
            f"El pago (${monto:,.0f}) supera el monto adeudado (${prestamo.monto_adeudado:,.0f})."
        )
    
    # Crear el registro histórico del pago
    PagoPrestamo.objects.create(
        prestamo=prestamo,
        monto=monto,
        fecha=fecha or timezone.now().date(),
        notas=notas,
    )
    
    # Actualizar el acumulado en el préstamo
    prestamo.monto_pagado += monto
    
    # ¿Quedó saldado?
    if prestamo.monto_pagado >= prestamo.monto_total:
        prestamo.estado = 'saldado'
    
    # update_fields es más eficiente: solo actualiza esas columnas en BD
    prestamo.save(update_fields=['monto_pagado', 'estado', 'actualizado_en'])
    
    return prestamo


def resumen_prestamos(usuario):
    """
    Devuelve un resumen de todos los préstamos del usuario.
    Útil para la página de inicio y el dashboard.
    """
    from django.db.models import Sum
    
    prestamos = Prestamo.objects.filter(usuario=usuario, estado='vigente')
    
    # Lo que yo debo
    debo = prestamos.filter(tipo='recibido').aggregate(
        total=Sum('monto_total'), pagado=Sum('monto_pagado')
    )
    
    # Lo que me deben
    me_deben = prestamos.filter(tipo='otorgado').aggregate(
        total=Sum('monto_total'), pagado=Sum('monto_pagado')
    )
    
    def adeudado(agg):
        total = agg['total'] or 0
        pagado = agg['pagado'] or 0
        return total - pagado
    
    return {
        'total_que_debo': adeudado(debo),
        'total_que_me_deben': adeudado(me_deben),
        'cantidad_vigentes': prestamos.count(),
    }


def actualizar_estados_prestamos_vencidos():
    """
    Igual que con los gastos, recorre los préstamos vigentes
    y marca como vencido si pasó la fecha límite.
    Esta función se llama desde la vista 'inicio' cada vez que alguien entra.
    """
    hoy = timezone.now().date()
    return Prestamo.objects.filter(
        estado='vigente',
        fecha_vencimiento__lt=hoy,
    ).update(estado='vencido')

def crear_meta(usuario, nombre, monto_objetivo, icono='💰',
               fecha_objetivo=None, descripcion=''):
    if not nombre or not nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
    from decimal import Decimal
    if Decimal(str(monto_objetivo)) <= 0:
        raise ValueError("El monto objetivo debe ser mayor a cero.")
    return MetaAhorro.objects.create(
        usuario=usuario,
        nombre=nombre.strip(),
        monto_objetivo=monto_objetivo,
        icono=icono,
        fecha_objetivo=fecha_objetivo or None,
        descripcion=descripcion,
    )


def registrar_aporte(usuario, meta_id, monto, fecha=None, notas=''):
    from decimal import Decimal
    meta = MetaAhorro.objects.get(id=meta_id, usuario=usuario)
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValueError("El aporte debe ser mayor a cero.")
    
    AporteMeta.objects.create(
        meta=meta,
        monto=monto,
        fecha=fecha or timezone.now().date(),
        notas=notas,
    )
    return meta