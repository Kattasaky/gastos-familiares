# Mejoras:
# 1. resumen_categorias muestra SOLO gastos pagados en "Total pagado"
#    y separa pendiente/vencido
# 2. Gráfico torta siempre usa TODAS las categorías (ignora el filtro
#    de categoría para el gráfico — así siempre hay comparación)
# 3. Tarjetas muestran: Pagado | Pendiente | Vencido | Balance

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Q
from gastos.models import Gasto, Ingreso, Categoria
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import json
from datetime import date, timedelta
from decimal import Decimal


MESES_LISTA = [
    (1,'Enero'),(2,'Febrero'),(3,'Marzo'),(4,'Abril'),
    (5,'Mayo'),(6,'Junio'),(7,'Julio'),(8,'Agosto'),
    (9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre'),
]
MESES_CORTO = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']


def _rango_fechas(periodo, año, mes):
    import calendar
    hoy = timezone.now().date()
    if periodo == 'diario':
        dia = hoy.day if (año == hoy.year and mes == hoy.month) else 1
        inicio = fin = date(año, mes, dia)
        titulo = f"Día {inicio.strftime('%d/%m/%Y')}"
        dias = 1
    elif periodo == 'semanal':
        lunes = hoy - timedelta(days=hoy.weekday())
        inicio, fin = lunes, lunes + timedelta(days=6)
        titulo = f"Semana {inicio.strftime('%d/%m')} – {fin.strftime('%d/%m/%Y')}"
        dias = 7
    elif periodo == 'semestral':
        if mes <= 6:
            inicio, fin = date(año,1,1), date(año,6,30)
            titulo = f"1° Semestre {año}"
        else:
            inicio, fin = date(año,7,1), date(año,12,31)
            titulo = f"2° Semestre {año}"
        dias = (fin - inicio).days + 1
    elif periodo == 'anual':
        inicio, fin = date(año,1,1), date(año,12,31)
        titulo = f"Año {año}"
        dias = 365
    else:  # mensual
        ultimo = calendar.monthrange(año, mes)[1]
        inicio, fin = date(año,mes,1), date(año,mes,ultimo)
        titulo = f"{dict(MESES_LISTA)[mes]} {año}"
        dias = ultimo
    return inicio, fin, titulo, dias


def _datos_categorias_json(gastos_todos):
    """
    SIEMPRE usa todos los gastos del período (sin filtro de categoría)
    para que el gráfico torta muestre la comparación real entre categorías.
    Solo incluye gastos PAGADOS para mostrar gasto real.
    """
    por_cat = (
        gastos_todos
        .filter(estado='pagado')  # solo lo realmente gastado
        .values('categoria__nombre', 'categoria__icono')
        .annotate(subtotal=Sum('monto'))
        .order_by('-subtotal')
    )
    labels, values = [], []
    for item in por_cat:
        nombre = item['categoria__nombre'] or 'Sin categoría'
        icono  = item['categoria__icono'] or ''
        labels.append(f"{icono} {nombre}".strip())
        values.append(float(item['subtotal'] or 0))

    # Si no hay pagados, mostrar todos (para que el gráfico no quede vacío)
    if not values:
        por_cat_todos = (
            gastos_todos
            .values('categoria__nombre', 'categoria__icono')
            .annotate(subtotal=Sum('monto'))
            .order_by('-subtotal')
        )
        for item in por_cat_todos:
            nombre = item['categoria__nombre'] or 'Sin categoría'
            icono  = item['categoria__icono'] or ''
            labels.append(f"{icono} {nombre}".strip())
            values.append(float(item['subtotal'] or 0))

    return json.dumps({'labels': labels, 'values': values})


def _resumen_por_categoria(gastos_filtrados, dias, total_pagado):
    """
    Muestra solo gastos PAGADOS en el resumen.
    El porcentaje es sobre el total pagado real.
    """
    por_cat = (
        gastos_filtrados
        .filter(estado='pagado')
        .values('categoria__nombre', 'categoria__icono')
        .annotate(subtotal=Sum('monto'))
        .order_by('-subtotal')
    )
    resultado = []
    for item in por_cat:
        total = float(item['subtotal'] or 0)
        if total == 0 or dias == 0:
            continue
        por_dia = total / dias
        resultado.append({
            'nombre': f"{item['categoria__icono'] or ''} {item['categoria__nombre'] or 'Sin categoría'}".strip(),
            'total': total,
            'por_dia': round(por_dia),
            'proyeccion_mensual': round(por_dia * 30),
            'proyeccion_anual': round(por_dia * 365),
            'porcentaje': round((total / total_pagado * 100)) if total_pagado > 0 else 0,
        })
    return resultado


def _evolucion(usuario, periodo, año, mes):
    labels, egresos_vals, ingresos_vals = [], [], []
    if periodo == 'anual':
        titulo = "Evolución últimos 5 años"
        for a in range(año-4, año+1):
            labels.append(str(a))
            eg = Gasto.objects.filter(usuario=usuario, fecha__year=a, estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
            ing = Ingreso.objects.filter(usuario=usuario, fecha__year=a).aggregate(t=Sum('monto'))['t'] or 0
            egresos_vals.append(float(eg))
            ingresos_vals.append(float(ing))
    elif periodo == 'semestral':
        titulo = "Evolución últimos 4 semestres"
        semestres = []
        a, s = año, (1 if mes <= 6 else 2)
        for _ in range(4):
            semestres.insert(0, (a, s))
            s -= 1
            if s == 0: s, a = 2, a-1
        for a_s, s_s in semestres:
            if s_s == 1:
                inicio, fin = date(a_s,1,1), date(a_s,6,30)
                labels.append(f"1S {a_s}")
            else:
                inicio, fin = date(a_s,7,1), date(a_s,12,31)
                labels.append(f"2S {a_s}")
            eg = Gasto.objects.filter(usuario=usuario, fecha__range=(inicio,fin), estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
            ing = Ingreso.objects.filter(usuario=usuario, fecha__range=(inicio,fin)).aggregate(t=Sum('monto'))['t'] or 0
            egresos_vals.append(float(eg))
            ingresos_vals.append(float(ing))
    else:
        titulo = "Evolución últimos 6 meses"
        m, a = mes, año
        meses = []
        for _ in range(6):
            meses.insert(0, (a, m))
            m -= 1
            if m == 0: m, a = 12, a-1
        for a_m, m_m in meses:
            labels.append(f"{MESES_CORTO[m_m-1]} {str(a_m)[2:]}")
            eg = Gasto.objects.filter(usuario=usuario, fecha__year=a_m, fecha__month=m_m, estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
            ing = Ingreso.objects.filter(usuario=usuario, fecha__year=a_m, fecha__month=m_m).aggregate(t=Sum('monto'))['t'] or 0
            egresos_vals.append(float(eg))
            ingresos_vals.append(float(ing))
    return json.dumps(labels), json.dumps(egresos_vals), json.dumps(ingresos_vals), titulo


@login_required
def estadisticas(request):
    hoy = timezone.now().date()
    año  = int(request.GET.get('año', hoy.year))
    mes  = int(request.GET.get('mes', hoy.month))
    periodo = request.GET.get('periodo', 'mensual')
    categoria_filtro = request.GET.get('categoria_filtro', '')

    fecha_inicio, fecha_fin, titulo_periodo, dias = _rango_fechas(periodo, año, mes)

    # ── Todos los gastos del período (para el gráfico)
    gastos_todos = Gasto.objects.filter(
        usuario=request.user,
        fecha__range=(fecha_inicio, fecha_fin),
    ).select_related('categoria')

    # ── Gastos filtrados (para tablas y resumen)
    gastos_qs = gastos_todos
    categoria_nombre = ''
    if categoria_filtro:
        gastos_qs = gastos_qs.filter(categoria__pk=categoria_filtro)
        try:
            cat = Categoria.objects.get(pk=categoria_filtro)
            categoria_nombre = str(cat)
        except Categoria.DoesNotExist:
            categoria_filtro = ''

    # ── Ingresos
    ingresos_qs = Ingreso.objects.filter(
        usuario=request.user,
        fecha__range=(fecha_inicio, fecha_fin),
    )

    # ── Totales separados
    total_pagado    = gastos_qs.filter(estado='pagado').aggregate(t=Sum('monto'))['t'] or 0
    total_pendiente = gastos_qs.filter(estado='pendiente').aggregate(t=Sum('monto'))['t'] or 0
    total_vencido   = gastos_qs.filter(estado='vencido').aggregate(t=Sum('monto'))['t'] or 0
    total_egresos   = total_pagado + total_pendiente + total_vencido
    total_ingresos  = ingresos_qs.aggregate(t=Sum('monto'))['t'] or 0
    balance         = total_ingresos - total_pagado  # balance real = ingresado - pagado

    promedio_diario_egresos  = round(float(total_pagado) / dias) if dias > 0 and total_pagado else 0
    promedio_diario_ingresos = round(float(total_ingresos) / dias) if dias > 0 and total_ingresos else 0

    # ── Datos gráficos
    # El gráfico SIEMPRE usa todos los gastos (sin filtro de categoría)
    datos_categorias_json = _datos_categorias_json(gastos_todos)

    ingresos_por_tipo = ingresos_qs.values('tipo').annotate(subtotal=Sum('monto'))
    TIPOS = {'sueldo':'Sueldo','extra':'Extra','pyme':'Pyme','otro':'Otro'}
    datos_ingresos_json = json.dumps({
        'labels': [TIPOS.get(i['tipo'], i['tipo']) for i in ingresos_por_tipo],
        'values': [float(i['subtotal'] or 0) for i in ingresos_por_tipo],
    })

    evolucion_labels, evolucion_egresos, evolucion_ingresos, titulo_evolucion = \
        _evolucion(request.user, periodo, año, mes)

    resumen_categorias = _resumen_por_categoria(gastos_qs, dias, float(total_pagado))

    # ── Determinar si hay datos para el gráfico
    datos_cat = json.loads(datos_categorias_json)
    hay_grafico_cat = bool(datos_cat['values'])
    hay_grafico_ing = bool(json.loads(datos_ingresos_json)['values'])

    return render(request, 'gastos/estadisticas.html', {
        'periodo': periodo,
        'mes': mes,
        'año': año,
        'categoria_filtro': categoria_filtro,
        'categoria_nombre': categoria_nombre,
        'categorias': Categoria.objects.all(),
        'meses_lista': MESES_LISTA,
        'titulo_periodo': titulo_periodo,
        'titulo_evolucion': titulo_evolucion,
        'gastos': gastos_qs.order_by('estado', '-fecha'),
        'ingresos': ingresos_qs,
        # Totales separados
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'total_vencido': total_vencido,
        'total_egresos': total_egresos,
        'total_ingresos': total_ingresos,
        'balance': balance,
        'promedio_diario_egresos': promedio_diario_egresos,
        'promedio_diario_ingresos': promedio_diario_ingresos,
        'resumen_categorias': resumen_categorias,
        # Gráficos
        'datos_categorias_json': datos_categorias_json,
        'datos_ingresos_json': datos_ingresos_json,
        'evolucion_labels': evolucion_labels,
        'evolucion_egresos': evolucion_egresos,
        'evolucion_ingresos': evolucion_ingresos,
        'hay_grafico_cat': hay_grafico_cat,
        'hay_grafico_ing': hay_grafico_ing,
        'por_categoria': hay_grafico_cat,
        'ingresos_por_tipo': hay_grafico_ing,
    })


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
    enc_font = Font(bold=True, color="FFFFFF")
    enc_fill = PatternFill("solid", fgColor="1a1a2e")
    encabezados = ['Descripción','Monto','Categoría','Fecha','Vencimiento','Prioridad','Estado']
    for col, titulo in enumerate(encabezados, 1):
        c = ws.cell(row=1, column=col, value=titulo)
        c.font = enc_font; c.fill = enc_fill
        c.alignment = Alignment(horizontal='center')
    for row, g in enumerate(gastos, 2):
        ws.cell(row=row, column=1, value=g.descripcion)
        ws.cell(row=row, column=2, value=float(g.monto) if g.monto else 0)
        ws.cell(row=row, column=3, value=str(g.categoria) if g.categoria else '')
        ws.cell(row=row, column=4, value=str(g.fecha))
        ws.cell(row=row, column=5, value=str(g.fecha_vencimiento) if g.fecha_vencimiento else '')
        ws.cell(row=row, column=6, value=g.get_prioridad_display())
        ws.cell(row=row, column=7, value=g.get_estado_display())
    for col in ws.columns:
        max_length = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 4
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=gastos_{hoy.month}_{hoy.year}.xlsx'
    wb.save(response)
    return response
