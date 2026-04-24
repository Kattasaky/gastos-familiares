from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.conf import settings

def service_worker(request):
    sw_path = settings.BASE_DIR / 'gastos' / 'static' / 'sw.js'
    with open(sw_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', service_worker, name='sw'),          # ← línea nueva
    path('', include('gastos.urls')),
    path('reportes/', include('reportes.urls')),
    path('alertas/', include('alertas.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='gastos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]