 #CAMBIOS vs la versión anterior:
# 1. La vista estadisticas() ahora prepara datos JSON para Chart.js
# 2. Se agregan datos de evolución (últimos 6 meses)
# 3. Se agrega lista de meses para el selector del filtro
#
# ¿Por qué preparar los datos en Python y no en JS?
# Porque Python tiene acceso directo a la BD, y podemos
# formatear exactamente lo que Chart.js necesita.
# El JS solo recibe el JSON listo para usar.
# ============================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from gastos.models import Gasto, Ingreso
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import json


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


def _datos_grafico_categorias(gastos):
    """
    Convierte el queryset de gastos en el formato que Chart.js necesita.
    
    Chart.js espera:
    { labels: ["Cat1", "Cat2"], values: [1000, 2000] }
    
    Nota: si un gasto no tiene categoría, lo agrupamos como "Sin categoría".
    """
    por_cat = (
        gastos.values('categoria__nombre', 'categoria__icono')
        .annotate(subtotal=Sum('monto'))
        .order_by('-subtotal')
    )
    labels = []
    values = []
    for item in por_cat:
        nombre = item['categoria__nombre'] or 'Sin categoría'
        icono = item['categoria__icono'] or ''
        labels.append(f"{icono} {nombre}".strip())
        values.append(float(item['subtotal'] or 0))
    
    return json.dumps({'labels': labels, 'values': values})


def _datos_evolucion(usuario, año, mes):
    """
    Calcula ingresos y egresos de los últimos 6 meses para el gráfico de barras.
    
    ¿Por qué 6 meses?
    Es el período más útil para ver tendencias sin sobrecargar la vista.
    
    Técnica: iteramos hacia atrás desde el mes actual restando 1 mes cada vez.
    Usamos timedelta no directamente en meses (Python no tiene timedelta de meses)
    sino que calculamos el primer día de cada mes manualmente.
    """
    from datetime import date
    
    labels = []
    egresos = []
    ingresos_vals = []
    
    MESES_ES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    # Generar los últimos 6 meses (incluyendo el actual)
    meses = []
    m, a = mes, año
    for _ in range(6):
        meses.insert(0, (a, m))  # insert al inicio para que queden en orden cronológico
        m -= 1
        if m == 0:
            m = 12
            a -= 1
    
    for a_iter, m_iter in meses:
        labels.append(f"{MESES_ES[m_iter-1]} {str(a_iter)[2:]}")
        
        eg = Gasto.objects.filter(
            usuario=usuario, fecha__year=a_iter, fecha__month=m_iter
        ).aggregate(t=Sum('monto'))['t'] or 0
        
        ing = Ingreso.objects.filter(
            usuario=usuario, fecha__year=a_iter, fecha__month=m_iter
        ).aggregate(t=Sum('monto'))['t'] or 0
        
        egresos.append(float(eg))
        ingresos_vals.append(float(ing))
    
    return (
        json.dumps(labels),
        json.dumps(egresos),
        json.dumps(ingresos_vals),
    )


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
    total_pendiente = gastos.filter(estado='pendiente').aggregate(t=Sum('monto'))['t'] or 0
    total_ingresos = ingresos.aggregate(t=Sum('monto'))['t'] or 0
    balance = total_ingresos - total_egresos

    # Datos para gráficos
    por_categoria = (
        gastos.values('categoria__nombre')
        .annotate(subtotal=Sum('monto'))
        .filter(subtotal__gt=0)
    )
    
    ingresos_por_tipo = (
        ingresos.values('tipo')
        .annotate(subtotal=Sum('monto'))
    )
    
    # Preparar JSON para los gráficos de torta
    datos_categorias_json = _datos_grafico_categorias(gastos)
    
    # Ingresos por tipo (traducir los codes a nombres legibles)
    TIPOS_INGRESO = {'sueldo': 'Sueldo', 'extra': 'Extra', 'pyme': 'Pyme', 'otro': 'Otro'}
    ing_labels = [TIPOS_INGRESO.get(i['tipo'], i['tipo']) for i in ingresos_por_tipo]
    ing_values = [float(i['subtotal'] or 0) for i in ingresos_por_tipo]
    datos_ingresos_json = json.dumps({'labels': ing_labels, 'values': ing_values})

    # Datos evolución últimos 6 meses
    evolucion_labels, evolucion_egresos, evolucion_ingresos = _datos_evolucion(
        request.user, año, mes
    )

    # Lista de meses para el selector del filtro
    MESES_LISTA = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    return render(request, 'gastos/estadisticas.html', {
        'gastos': gastos,
        'ingresos': ingresos,
        'total_egresos': total_egresos,
        'total_pendiente': total_pendiente,
        'total_ingresos': total_ingresos,
        'balance': balance,
        'mes': mes,
        'año': año,
        'hoy': hoy,
        'por_categoria': por_categoria,
        'ingresos_por_tipo': ingresos_por_tipo,
        # JSON para Chart.js
        'datos_categorias_json': datos_categorias_json,
        'datos_ingresos_json': datos_ingresos_json,
        'evolucion_labels': evolucion_labels,
        'evolucion_egresos': evolucion_egresos,
        'evolucion_ingresos': evolucion_ingresos,
        'meses_lista': MESES_LISTA,
    })
