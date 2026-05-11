from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from . import services
from .models import (
    Gasto, Categoria, ItemCompra,
    PagoRecurrente, Ingreso,
    Prestamo, PagoPrestamo,
    MetaAhorro, AporteMeta,
)


# ─────────────────────────────────────────────
# INICIO
# ─────────────────────────────────────────────

@login_required
def inicio(request):
    hoy = timezone.now().date()
    services.generar_gastos_del_mes(request.user)
    services.actualizar_estados_vencidos()
    services.actualizar_estados_prestamos_vencidos()
    return render(request, 'gastos/inicio.html', {
        'proximos': services.gastos_proximos_a_vencer(request.user, dias=7),
        'urgentes': services.gastos_urgentes(request.user),
        'resumen': services.resumen_mensual(request.user, hoy.year, hoy.month),
    })


# ─────────────────────────────────────────────
# GASTOS
# ─────────────────────────────────────────────

@login_required
def lista_gastos(request):
    from django.db.models import Sum
    services.actualizar_estados_vencidos()
    hoy = timezone.now().date()
    año = int(request.GET.get('año', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))
    estado_filtro = request.GET.get('estado', '')
    gastos = Gasto.objects.filter(
        usuario=request.user,
        fecha__year=año,
        fecha__month=mes,
    ).select_related('categoria')
    if estado_filtro:
        gastos = gastos.filter(estado=estado_filtro)
    todos = Gasto.objects.filter(usuario=request.user, fecha__year=año, fecha__month=mes)
    total_pagado    = todos.filter(estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
    total_pendiente = todos.filter(estado='pendiente').aggregate(t=Sum('monto'))['t'] or 0
    total_vencido   = todos.filter(estado='vencido').aggregate(t=Sum('monto'))['t'] or 0
    # Calcular mes anterior y siguiente para navegación
    if mes == 1:
        mes_anterior = {'mes': 12, 'año': año - 1}
    else:
        mes_anterior = {'mes': mes - 1, 'año': año}
    if mes == 12:
        mes_siguiente = {'mes': 1, 'año': año + 1}
    else:
        mes_siguiente = {'mes': mes + 1, 'año': año}
    import calendar
    nombre_mes = calendar.month_name[mes].capitalize()
    return render(request, 'gastos/lista.html', {
        'gastos': gastos,
        'estado_filtro': estado_filtro,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'total_vencido': total_vencido,
        'mes': mes,
        'año': año,
        'nombre_mes': nombre_mes,
        'mes_anterior': mes_anterior,
        'mes_siguiente': mes_siguiente,
        'es_mes_actual': mes == hoy.month and año == hoy.year,
    })



@login_required
def nuevo_gasto(request):
    if request.method == 'POST':
        try:
            services.crear_gasto(
                usuario=request.user,
                descripcion=request.POST.get('descripcion', ''),
                monto=request.POST.get('monto', 0),
                categoria_id=request.POST.get('categoria') or None,
                fecha_vencimiento=request.POST.get('fecha_vencimiento') or None,
                prioridad=request.POST.get('prioridad', 'normal'),
                notas=request.POST.get('notas', ''),
            )
            messages.success(request, 'Gasto registrado.')
            return redirect('lista_gastos')
        except (ValueError, Exception) as e:
            messages.error(request, str(e))
    return render(request, 'gastos/formulario.html', {'categorias': Categoria.objects.all()})


@login_required
def marcar_pagado(request, pk):
    services.marcar_pagado(pk, request.user)
    messages.success(request, 'Marcado como pagado.')
    return redirect('lista_gastos')


@login_required
def editar_gasto(request, pk):
    gasto = get_object_or_404(Gasto, pk=pk, usuario=request.user)
    if request.method == 'POST':
        gasto.descripcion = request.POST.get('descripcion', gasto.descripcion)
        gasto.monto = request.POST.get('monto', gasto.monto)
        gasto.categoria_id = request.POST.get('categoria') or None
        gasto.prioridad = request.POST.get('prioridad', gasto.prioridad)
        gasto.notas = request.POST.get('notas', gasto.notas)
        gasto.save()
        messages.success(request, 'Gasto actualizado.')
        return redirect('lista_gastos')
    return render(request, 'gastos/formulario.html', {
        'gasto': gasto,
        'categorias': Categoria.objects.all(),
    })


@login_required
def eliminar_gasto(request, pk):
    gasto = get_object_or_404(Gasto, pk=pk, usuario=request.user)
    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto eliminado.')
    return redirect('lista_gastos')


# ─────────────────────────────────────────────
# LISTA DE COMPRAS
# ─────────────────────────────────────────────

@login_required
def lista_compras(request):
    categoria_filtro = request.GET.get('categoria', '')
    items = ItemCompra.objects.filter(usuario=request.user).select_related('categoria')
    if categoria_filtro:
        items = items.filter(categoria__pk=categoria_filtro)
    # Calcular total estimado de la lista filtrada
    total_lista = sum(
        (item.valor_aprox * item.cantidad) for item in items if item.valor_aprox
    )
    total_pendiente = sum(
        (item.valor_aprox * (item.cantidad - item.cantidad_comprada))
        for item in items if item.valor_aprox and not item.comprado
    )
    return render(request, 'gastos/compras.html', {
        'items': items,
        'categorias': Categoria.objects.all(),
        'categoria_filtro': categoria_filtro,
        'total_lista': total_lista,
        'total_pendiente': total_pendiente,
    })


@login_required
def agregar_compra(request):
    if request.method == 'POST':
        try:
            services.agregar_item_compra(
                usuario=request.user,
                nombre=request.POST.get('nombre', ''),
                cantidad=int(request.POST.get('cantidad', 1)),
                valor_aprox=request.POST.get('valor_aprox') or None,
                categoria_id=request.POST.get('categoria') or None,
            )
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('lista_compras')


@login_required
def toggle_compra(request, pk):
    item = get_object_or_404(ItemCompra, pk=pk, usuario=request.user)
    if item.comprado:
        item.comprado = False
        item.cantidad_comprada = 0
    else:
        item.cantidad_comprada = min(item.cantidad_comprada + 1, item.cantidad)
        # Crea gasto por CADA unidad marcada (no solo al completar)
        if item.valor_aprox:
            Gasto.objects.create(
                usuario=request.user,
                descripcion=f"🛒 {item.nombre} (1 unidad)",
                monto=item.valor_aprox,
                categoria=item.categoria,
                fecha=timezone.now().date(),
                estado='pagado',
                prioridad='normal',
            )
        if item.cantidad_comprada >= item.cantidad:
            item.comprado = True
    item.save()
    return redirect('lista_compras')

@login_required
def limpiar_comprados(request):
    if request.method == 'POST':
        n = services.limpiar_comprados(request.user)
        messages.success(request, f'{n} ítem(s) eliminado(s).')
    return redirect('lista_compras')


# ─────────────────────────────────────────────
# PAGOS RECURRENTES
# ─────────────────────────────────────────────

@login_required
def lista_recurrentes(request):
    from django.db.models import Sum
    pagos = PagoRecurrente.objects.filter(usuario=request.user)
    total_mensual = pagos.filter(
        activo=True,
        frecuencia__in=['mensual', 'cuotas']
    ).aggregate(t=Sum('monto'))['t'] or 0
    total_semanal = pagos.filter(
        activo=True,
        frecuencia='semanal'
    ).aggregate(t=Sum('monto'))['t'] or 0
    return render(request, 'gastos/recurrentes.html', {
        'pagos': pagos,
        'total_mensual': total_mensual,
        'total_semanal': total_semanal,
    })

@login_required
def nuevo_recurrente(request):
    if request.method == 'POST':
        try:
            services.crear_pago_recurrente(
                usuario=request.user,
                descripcion=request.POST.get('descripcion', ''),
                dia_pago=request.POST.get('dia_pago', 1),
                monto=request.POST.get('monto') or None,
                categoria_id=request.POST.get('categoria') or None,
                frecuencia=request.POST.get('frecuencia', 'mensual'),
                total_cuotas=request.POST.get('total_cuotas') or None,
                prioridad=request.POST.get('prioridad', 'normal'),
                dia_semana=request.POST.get('dia_semana') or None,
                cuotas_pagadas=request.POST.get('cuotas_pagadas') or 0,
            )
            messages.success(request, 'Pago recurrente creado.')
            return redirect('lista_recurrentes')
        except ValueError as e:
            messages.error(request, str(e))
    return render(request, 'gastos/form_recurrente.html', {
        'categorias': Categoria.objects.all()
    })

@login_required
def eliminar_recurrente(request, pk):
    pago = get_object_or_404(PagoRecurrente, pk=pk, usuario=request.user)
    if request.method == 'POST':
        pago.delete()
        messages.success(request, 'Pago recurrente eliminado.')
    return redirect('lista_recurrentes')


@login_required
def pagar_cuota_mes(request, pk):
    pago = get_object_or_404(PagoRecurrente, pk=pk, usuario=request.user)
    pago.cuotas_pagadas = (pago.cuotas_pagadas or 0) + 1
    pago.save()
    Gasto.objects.create(
        usuario=request.user,
        descripcion=f"{pago.descripcion} - cuota {pago.cuotas_pagadas}/{pago.total_cuotas or '∞'}",
        monto=pago.monto,
        categoria=pago.categoria,
        prioridad=pago.prioridad,
        fecha_vencimiento=timezone.now().date(),
        estado='pagado',
    )
    messages.success(request, 'Cuota marcada como pagada.')
    return redirect('lista_recurrentes')


@login_required
def editar_recurrente(request, pk):
    pago = get_object_or_404(PagoRecurrente, pk=pk, usuario=request.user)
    if request.method == 'POST':
        pago.descripcion = request.POST.get('descripcion', pago.descripcion)
        pago.monto = request.POST.get('monto') or pago.monto
        pago.dia_pago = request.POST.get('dia_pago') or pago.dia_pago
        pago.frecuencia = request.POST.get('frecuencia', pago.frecuencia)
        pago.total_cuotas = request.POST.get('total_cuotas') or pago.total_cuotas
        pago.prioridad = request.POST.get('prioridad', pago.prioridad)
        pago.dia_semana = request.POST.get('dia_semana') or pago.dia_semana
        pago.save()
        messages.success(request, 'Pago recurrente actualizado.')
        return redirect('lista_recurrentes')
    return render(request, 'gastos/form_recurrente.html', {
        'pago': pago,
        'categorias': Categoria.objects.all(),
    })


# ─────────────────────────────────────────────
# INGRESOS
# ─────────────────────────────────────────────

@login_required
def lista_ingresos(request):
    hoy = timezone.now().date()
    ingresos = Ingreso.objects.filter(usuario=request.user)
    resumen = services.resumen_ingresos_mes(request.user, hoy.year, hoy.month)
    return render(request, 'gastos/ingresos.html', {
        'ingresos': ingresos,
        'resumen': resumen,
    })


@login_required
def nuevo_ingreso(request):
    if request.method == 'POST':
        try:
            services.crear_ingreso(
                usuario=request.user,
                descripcion=request.POST.get('descripcion', ''),
                monto=request.POST.get('monto', 0),
                tipo=request.POST.get('tipo', 'sueldo'),
                fecha=request.POST.get('fecha') or None,
                es_fijo=request.POST.get('es_fijo') == 'on',
            )
            messages.success(request, 'Ingreso registrado.')
            return redirect('lista_ingresos')
        except ValueError as e:
            messages.error(request, str(e))
    return render(request, 'gastos/form_ingreso.html')


@login_required
def eliminar_ingreso(request, pk):
    ingreso = get_object_or_404(Ingreso, pk=pk, usuario=request.user)
    if request.method == 'POST':
        ingreso.delete()
        messages.success(request, 'Ingreso eliminado.')
    return redirect('lista_ingresos')


# ─────────────────────────────────────────────
# PRÉSTAMOS
# ─────────────────────────────────────────────

@login_required
def lista_prestamos(request):
    services.actualizar_estados_prestamos_vencidos()
    prestamos = Prestamo.objects.filter(usuario=request.user).prefetch_related('pagos')
    return render(request, 'gastos/prestamos.html', {
        'recibidos': prestamos.filter(tipo='recibido'),
        'otorgados': prestamos.filter(tipo='otorgado'),
        'resumen': services.resumen_prestamos(request.user),
    })


@login_required
def nuevo_prestamo(request):
    if request.method == 'POST':
        try:
            services.crear_prestamo(
                usuario=request.user,
                persona=request.POST.get('persona', ''),
                concepto=request.POST.get('concepto', ''),
                monto_total=request.POST.get('monto_total', 0),
                tipo=request.POST.get('tipo', 'recibido'),
                fecha_prestamo=request.POST.get('fecha_prestamo') or None,
                fecha_vencimiento=request.POST.get('fecha_vencimiento') or None,
                notas=request.POST.get('notas', ''),
            )
            messages.success(request, 'Préstamo registrado.')
            return redirect('lista_prestamos')
        except ValueError as e:
            messages.error(request, str(e))
    return render(request, 'gastos/form_prestamo.html')


@login_required
def registrar_pago_prestamo(request, pk):
    if request.method == 'POST':
        try:
            services.registrar_pago_prestamo(
                usuario=request.user,
                prestamo_id=pk,
                monto=request.POST.get('monto', 0),
                fecha=request.POST.get('fecha') or None,
                notas=request.POST.get('notas', ''),
            )
            messages.success(request, 'Pago registrado.')
        except (ValueError, Prestamo.DoesNotExist) as e:
            messages.error(request, str(e))
    return redirect('lista_prestamos')


@login_required
def eliminar_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk, usuario=request.user)
    if request.method == 'POST':
        prestamo.delete()
        messages.success(request, 'Préstamo eliminado.')
    return redirect('lista_prestamos')


@login_required
def detalle_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk, usuario=request.user)
    return render(request, 'gastos/detalle_prestamo.html', {
        'prestamo': prestamo,
        'pagos': prestamo.pagos.all(),
    })


# ─────────────────────────────────────────────
# METAS DE AHORRO
# ─────────────────────────────────────────────

@login_required
def lista_metas(request):
    metas = MetaAhorro.objects.filter(usuario=request.user).prefetch_related('aportes')
    return render(request, 'gastos/metas.html', {
        'activas': metas.filter(activa=True),
        'completadas': metas.filter(activa=False),
    })


@login_required
def nueva_meta(request):
    if request.method == 'POST':
        try:
            services.crear_meta(
                usuario=request.user,
                nombre=request.POST.get('nombre', ''),
                monto_objetivo=request.POST.get('monto_objetivo', 0),
                icono=request.POST.get('icono', '💰'),
                fecha_objetivo=request.POST.get('fecha_objetivo') or None,
                descripcion=request.POST.get('descripcion', ''),
            )
            messages.success(request, 'Meta de ahorro creada.')
            return redirect('lista_metas')
        except ValueError as e:
            messages.error(request, str(e))
    return render(request, 'gastos/form_meta.html', {
        'iconos': MetaAhorro.ICONO_CHOICES,
    })


@login_required
def registrar_aporte(request, pk):
    # NOMBRE CORRECTO: la vista se llama registrar_aporte
    # pero llama al servicio registrar_aporte_meta (con sufijo)
    if request.method == 'POST':
        try:
            services.registrar_aporte_meta(
                usuario=request.user,
                meta_id=pk,
                monto=request.POST.get('monto', 0),
                fecha=request.POST.get('fecha') or None,
                notas=request.POST.get('notas', ''),
            )
            messages.success(request, '¡Aporte registrado! 💪')
        except (ValueError, MetaAhorro.DoesNotExist) as e:
            messages.error(request, str(e))
    return redirect('lista_metas')


@login_required
def eliminar_meta(request, pk):
    meta = get_object_or_404(MetaAhorro, pk=pk, usuario=request.user)
    if request.method == 'POST':
        meta.delete()
        messages.success(request, 'Meta eliminada.')
    return redirect('lista_metas')


@login_required
def archivar_meta(request, pk):
    meta = get_object_or_404(MetaAhorro, pk=pk, usuario=request.user)
    if request.method == 'POST':
        meta.activa = False
        meta.save(update_fields=['activa'])
        messages.success(request, '¡Meta archivada!')
    return redirect('lista_metas')


# ─────────────────────────────────────────────
# REGISTRO DE USUARIO
# ─────────────────────────────────────────────

def registro(request):
    # BUG CORREGIDO: antes faltaba el return render() para GET y POST inválido
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f'¡Bienvenida, {usuario.username}!')
            return redirect('inicio')
    else:
        form = UserCreationForm()
    return render(request, 'gastos/registro.html', {'form': form})

# ═══════════════════════════════════════════════
# PARTE 1: REEMPLAZAR las 3 vistas de categoría
# en gastos/views.py (al final del archivo)
# ═══════════════════════════════════════════════

CATEGORIAS_SUGERIDAS = [
    {'nombre': 'Supermercado', 'icono': '🛒', 'color': '#16a34a'},
    {'nombre': 'Salud',        'icono': '🏥', 'color': '#dc2626'},
    {'nombre': 'Arriendo',     'icono': '🏠', 'color': '#7c3aed'},
    {'nombre': 'Transporte',   'icono': '🚗', 'color': '#2563eb'},
    {'nombre': 'Educación',    'icono': '🎓', 'color': '#0891b2'},
    {'nombre': 'Servicios',    'icono': '💡', 'color': '#d97706'},
    {'nombre': 'Pyme',         'icono': '💼', 'color': '#059669'},
    {'nombre': 'Restaurantes', 'icono': '🍽️', 'color': '#ea580c'},
    {'nombre': 'Ropa',         'icono': '👕', 'color': '#db2777'},
    {'nombre': 'Entretenimiento','icono':'🎬', 'color': '#7c3aed'},
    {'nombre': 'Mascotas',     'icono': '🐾', 'color': '#65a30d'},
    {'nombre': 'Viajes',       'icono': '✈️', 'color': '#0284c7'},
    {'nombre': 'Tecnología',   'icono': '📱', 'color': '#4f46e5'},
    {'nombre': 'Farmacia',     'icono': '💊', 'color': '#be123c'},
    {'nombre': 'Hogar',        'icono': '🔧', 'color': '#92400e'},
    {'nombre': 'Regalos',      'icono': '🎁', 'color': '#be185d'},
]


@login_required
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'gastos/categorias.html', {'categorias': categorias})


@login_required
def nueva_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        icono  = request.POST.get('icono', '💰').strip()
        color  = request.POST.get('color', '#6366f1').strip()
        if not nombre:
            messages.error(request, 'El nombre no puede estar vacío.')
        else:
            Categoria.objects.create(nombre=nombre, icono=icono, color=color)
            messages.success(request, f'Categoría "{nombre}" creada.')
            return redirect('lista_categorias')
    return render(request, 'gastos/form_categoria.html', {
        'sugeridas': CATEGORIAS_SUGERIDAS,
    })


@login_required
def editar_categoria(request, pk):
    cat = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        icono  = request.POST.get('icono', cat.icono).strip()
        color  = request.POST.get('color', cat.color).strip()
        if not nombre:
            messages.error(request, 'El nombre no puede estar vacío.')
        else:
            cat.nombre = nombre
            cat.icono = icono
            cat.color = color
            cat.save()
            messages.success(request, f'Categoría "{nombre}" actualizada.')
            return redirect('lista_categorias')
    return render(request, 'gastos/form_categoria.html', {
        'cat': cat,
        'sugeridas': CATEGORIAS_SUGERIDAS,
    })


@login_required
def eliminar_categoria(request, pk):
    cat = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Categoría eliminada.')
    return redirect('lista_categorias')

@login_required
def exportar_compras_excel(request):
    import openpyxl
    from django.http import HttpResponse
    categoria_filtro = request.GET.get('categoria', '')
    items = ItemCompra.objects.filter(usuario=request.user).select_related('categoria')
    if categoria_filtro:
        items = items.filter(categoria__pk=categoria_filtro)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Lista de Compras"
    ws.append(['Ítem', 'Cantidad', 'Comprado', 'Precio Unit.', 'Total', 'Categoría'])
    for item in items:
        ws.append([
            item.nombre,
            item.cantidad,
            'Sí' if item.comprado else 'No',
            float(item.valor_aprox) if item.valor_aprox else '',
            float(item.total) if item.total else '',
            str(item.categoria) if item.categoria else '',
        ])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="lista_compras.xlsx"'
    wb.save(response)
    return response

@login_required
def editar_compra(request, pk):
    item = get_object_or_404(ItemCompra, pk=pk, usuario=request.user)
    if request.method == 'POST':
        item.nombre = request.POST.get('nombre', item.nombre)
        item.cantidad = int(request.POST.get('cantidad', item.cantidad))
        item.valor_aprox = request.POST.get('valor_aprox') or None
        item.categoria_id = request.POST.get('categoria') or None
        item.save()
        messages.success(request, 'Ítem actualizado.')
        return redirect('lista_compras')
    return render(request, 'gastos/editar_compra.html', {
        'item': item,
        'categorias': Categoria.objects.all(),
    })