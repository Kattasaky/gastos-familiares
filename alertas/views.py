# En este archivo defino la vista para el panel de alertas, 
# que muestra los gastos próximos a vencer y los gastos urgentes.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from gastos.services import gastos_proximos_a_vencer, gastos_urgentes


@login_required
def panel_alertas(request):
    contexto = {
        'proximos_7': gastos_proximos_a_vencer(request.user, dias=7),
        'proximos_30': gastos_proximos_a_vencer(request.user, dias=30),
        'urgentes': gastos_urgentes(request.user),
    }
    return render(request, 'gastos/alertas.html', contexto)