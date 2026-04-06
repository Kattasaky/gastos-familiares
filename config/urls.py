from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls), #panel de administración de Django
    path('', include('gastos.urls')), #incluye las URLs de la aplicación "gastos" en la URL raíz del proyecto
    path('reportes/', include('reportes.urls')),#incluye las URLs de la aplicación "reportes"
    path('alertas/', include('alertas.urls')), #incluye las URLs de la aplicación "alertas"
    path('login/', auth_views.LoginView.as_view(template_name='gastos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]