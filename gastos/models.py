from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Categoria(models.Model): #categorias de gastos
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=10, default='💰')
    color = models.CharField(max_length=7, default='#6366f1')

    class Meta:
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.icono} {self.nombre}"


class Gasto(models.Model): #cada gasto registrado como monto, fecha, etc
    PRIORIDAD_CHOICES = [
        ('urgente', 'Urgente'),
        ('alta', 'Alta'),
        ('normal', 'Normal'),
        ('postergable', 'Postergable'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gastos')
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='normal')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f"{self.descripcion} — ${self.monto:,.0f}"

    @property
    def esta_vencido(self):
        if self.fecha_vencimiento and self.estado == 'pendiente':
            return self.fecha_vencimiento < timezone.now().date()
        return False

    @property
    def dias_para_vencer(self):
        if self.fecha_vencimiento:
            return (self.fecha_vencimiento - timezone.now().date()).days
        return None


class ItemCompra(models.Model): #lista de compras, con nombre del producto, cantidad, si ya se compró o no, etc
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lista_compras')
    nombre = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField(default=1)
    valor_aprox = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    comprado = models.BooleanField(default=False)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['comprado', '-creado_en']

    def __str__(self):
        estado = '✓' if self.comprado else '○'
        return f"{estado} {self.nombre} (x{self.cantidad})"
    
class PagoRecurrente(models.Model):
    
    FRECUENCIA_CHOICES = [
    ('mensual', 'Mensual'),
    ('semanal', 'Semanal'),
    ('cuotas', 'En cuotas'),
]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagos_recurrentes')
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES, default='mensual')
    dia_pago = models.PositiveIntegerField(null=True, blank=True, help_text='Día del mes 1-31')
    dia_semana = models.PositiveIntegerField(null=True, blank=True, help_text='0=Lunes, 6=Domingo')
    total_cuotas = models.PositiveIntegerField(null=True, blank=True, help_text='Solo si es en cuotas')
    cuotas_pagadas = models.PositiveIntegerField(default=0)
    prioridad = models.CharField(max_length=20, choices=Gasto.PRIORIDAD_CHOICES, default='normal')
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dia_pago']

    def __str__(self):
        return f"{self.descripcion} — día {self.dia_pago}"

    @property
    def cuotas_restantes(self):
        if self.total_cuotas:
            return self.total_cuotas - self.cuotas_pagadas
        return None


class Ingreso(models.Model):
    TIPO_CHOICES = [
        ('sueldo', 'Sueldo'),
        ('extra', 'Extra'),
        ('pyme', 'Pyme'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ingresos')
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sueldo')
    fecha = models.DateField(default=timezone.now)
    es_fijo = models.BooleanField(default=False, help_text='Si es fijo se repite cada mes')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.descripcion} — ${self.monto:,.0f}"