from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from gastos.models import Gasto, Ingreso
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


@login_required
def exportar_excel(request):
    hoy = timezone.now().date()
    gastos = Gasto.objects.filter(
        usuario=request.user,
        fecha__year=hoy.year,
        fecha__month=hoy.month,
    ).select_related('categoria')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Gastos {hoy.month}-{hoy.year}"

    encabezado_font = Font(bold=True, color="FFFFFF")
    encabezado_fill = PatternFill("solid", fgColor="1a1a2e")
    encabezados = ['Descripción', 'Monto', 'Categoría', 'Fecha', 'Vencimiento', 'Prioridad', 'Estado']

    for col, titulo in enumerate(encabezados, 1):
        celda = ws.cell(row=1, column=col, value=titulo)
        celda.font = encabezado_font
        celda.fill = encabezado_fill
        celda.alignment = Alignment(horizontal='center')

    for row, g in enumerate(gastos, 2):
        ws.cell(row=row, column=1, value=g.descripcion)
        ws.cell(row=row, column=2, value=float(g.monto) if g.monto else 0)
        ws.cell(row=row, column=3, value=str(g.categoria) if g.categoria else '')
        ws.cell(row=row, column=4, value=str(g.fecha))
        ws.cell(row=row, column=5, value=str(g.fecha_vencimiento) if g.fecha_vencimiento else '')
        ws.cell(row=row, column=6, value=g.get_prioridad_display())
        ws.cell(row=row, column=7, value=g.get_estado_display())

    for col in ws.columns:
        max_length = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 4

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=gastos_{hoy.month}_{hoy.year}.xlsx'
    wb.save(response)
    return response


@login_required
def estadisticas(request):
    hoy = timezone.now().date()
    año = int(request.GET.get('año', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))

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