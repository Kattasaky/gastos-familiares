# reportes/views.py


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def exportar_excel(request):
    # TODO Fase 3: exportar con openpyxl
    return HttpResponse("Exportación Excel — disponible en Fase 3")


@login_required
def estadisticas(request):
    hoy = timezone.now().date()
    año = int(request.GET.get('año', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))

    from gastos.models import Gasto, Ingreso
    from django.db.models import Sum

    gastos = Gasto.objects.filter(
        usuario=request.user,
        fecha__year=año,
        fecha__month=mes,
    ).select_related('categoria').order_by('estado', '-fecha')

    ingresos = Ingreso.objects.filter(
        usuario=request.user,
        fecha__year=año,
        fecha__month=mes,
    )

    total_egresos = gastos.aggregate(t=Sum('monto'))['t'] or 0
    total_pagado = gastos.filter(estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
    total_pendiente = gastos.filter(estado='pendiente').aggregate(t=Sum('monto'))['t'] or 0
    total_ingresos = ingresos.aggregate(t=Sum('monto'))['t'] or 0
    balance = total_ingresos - total_egresos

    return render(request, 'gastos/estadisticas.html', {
        'gastos': gastos,
        'ingresos': ingresos,
        'total_egresos': total_egresos,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'total_ingresos': total_ingresos,
        'balance': balance,
        'mes': mes,
        'año': año,
        'hoy': hoy,
    })