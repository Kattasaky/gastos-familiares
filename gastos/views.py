#Las vistas reciben las peticiones del navegador, llaman a los servicios y devuelven las páginas HTML
#El decorador @login_required protege cada página — si no estás logueada te manda al login.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from . import services
from .models import Gasto, Categoria, ItemCompra, PagoRecurrente, Ingreso


@login_required
def inicio(request):
    hoy = timezone.now().date()
    services.generar_gastos_del_mes(request.user)
    services.actualizar_estados_vencidos()
    contexto = {
        'proximos': services.gastos_proximos_a_vencer(request.user, dias=7),
        'urgentes': services.gastos_urgentes(request.user),
        'resumen': services.resumen_mensual(request.user, hoy.year, hoy.month),
    }
    return render(request, 'gastos/inicio.html', contexto)


@login_required
def lista_gastos(request):
    services.actualizar_estados_vencidos()
    gastos = Gasto.objects.filter(usuario=request.user).select_related('categoria')
    return render(request, 'gastos/lista.html', {'gastos': gastos})


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
    categorias = Categoria.objects.all()
    return render(request, 'gastos/formulario.html', {'categorias': categorias})


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


@login_required
def lista_compras(request):
    items = ItemCompra.objects.filter(usuario=request.user).select_related('categoria')
    return render(request, 'gastos/compras.html', {
        'items': items,
        'categorias': Categoria.objects.all(),
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
    services.marcar_comprado(pk, request.user)
    return redirect('lista_compras')


@login_required
def limpiar_comprados(request):
    if request.method == 'POST':
        n = services.limpiar_comprados(request.user)
        messages.success(request, f'{n} ítem(s) eliminado(s).')
    return redirect('lista_compras')


@login_required
def lista_recurrentes(request):
    pagos = PagoRecurrente.objects.filter(usuario=request.user)
    return render(request, 'gastos/recurrentes.html', {'pagos': pagos})


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

    # Incrementa el contador de cuotas pagadas
    pago.cuotas_pagadas = (pago.cuotas_pagadas or 0) + 1
    pago.save()

    # Registra el gasto en la tabla Gasto
    Gasto.objects.create(
        usuario=request.user,
        descripcion=f"{pago.descripcion} - cuota {pago.cuotas_pagadas}/{pago.total_cuotas or ''}",
        monto=pago.monto,
        categoria=pago.categoria,
        prioridad=pago.prioridad,
        fecha_vencimiento=timezone.now().date(),
        estado='pagado'
    )

    messages.success(request, 'Cuota marcada como pagada y registrada en gastos.')
    return redirect('lista_recurrentes')

@login_required
def editar_recurrente(request, pk):
    pago = get_object_or_404(PagoRecurrente, pk=pk, usuario=request.user)
    if request.method == 'POST':
        pago.descripcion = request.POST.get('descripcion', pago.descripcion)
        pago.monto = request.POST.get('monto') or None
        pago.dia_pago = request.POST.get('dia_pago') or None
        pago.dia_semana = request.POST.get('dia_semana') or None
        pago.frecuencia = request.POST.get('frecuencia', pago.frecuencia)
        pago.total_cuotas = request.POST.get('total_cuotas') or None
        pago.prioridad = request.POST.get('prioridad', pago.prioridad)
        pago.save()
        messages.success(request, 'Pago recurrente actualizado.')
        return redirect('lista_recurrentes')
    return render(request, 'gastos/form_recurrente.html', {
        'pago': pago,
        'categorias': Categoria.objects.all(),
    })