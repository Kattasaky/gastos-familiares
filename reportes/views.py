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
    # TODO Fase 2: gráficos y estadísticas
    return render(request, 'gastos/inicio.html')