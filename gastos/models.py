from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=10, default='💰')
    color = models.CharField(max_length=7, default='#6366f1')

    class Meta:
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.icono} {self.nombre}"


class Gasto(models.Model):
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


class ItemCompra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lista_compras')
    nombre = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField(default=1)
    cantidad_comprada = models.PositiveIntegerField(default=0)
    valor_aprox = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    comprado = models.BooleanField(default=False)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        if self.valor_aprox:
            return self.valor_aprox * self.cantidad
        return None

    @property
    def total_comprado(self):
        if self.valor_aprox:
            return self.valor_aprox * self.cantidad_comprada
        return None

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
    dia_pago = models.PositiveIntegerField(null=True, blank=True)
    dia_semana = models.PositiveIntegerField(null=True, blank=True)
    total_cuotas = models.PositiveIntegerField(null=True, blank=True)
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
    es_fijo = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.descripcion} — ${self.monto:,.0f}"


class Prestamo(models.Model):
    TIPO_CHOICES = [
        ('recibido', 'Me prestaron a mí'),
        ('otorgado', 'Yo presté dinero'),
    ]
    ESTADO_CHOICES = [
        ('vigente', 'Vigente'),
        ('saldado', 'Saldado'),
        ('vencido', 'Vencido'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prestamos')
    persona = models.CharField(max_length=150)
    concepto = models.CharField(max_length=200)
    monto_total = models.DecimalField(max_digits=12, decimal_places=0)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='recibido')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='vigente')
    fecha_prestamo = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_prestamo']
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'

    def __str__(self):
        return f"{self.persona} — ${self.monto_total:,.0f}"

    @property
    def monto_adeudado(self):
        return self.monto_total - self.monto_pagado

    @property
    def porcentaje_pagado(self):
        if self.monto_total == 0:
            return 0
        return int((self.monto_pagado / self.monto_total) * 100)

    @property
    def esta_saldado(self):
        return self.monto_pagado >= self.monto_total


class PagoPrestamo(models.Model):
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    fecha = models.DateField(default=timezone.now)
    notas = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"${self.monto:,.0f} el {self.fecha}"


class MetaAhorro(models.Model):
    ICONO_CHOICES = [
        ('🏖️', 'Viaje'),
        ('🏠', 'Casa'),
        ('🚗', 'Auto'),
        ('🎓', 'Educación'),
        ('🏥', 'Emergencia médica'),
        ('💼', 'Negocio'),
        ('🎁', 'Regalo'),
        ('📱', 'Tecnología'),
        ('💰', 'General'),
        ('🌟', 'Otro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas_ahorro')
    nombre = models.CharField(max_length=150)
    icono = models.CharField(max_length=10, choices=ICONO_CHOICES, default='💰')
    monto_objetivo = models.DecimalField(max_digits=12, decimal_places=0)
    fecha_objetivo = models.DateField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Meta de ahorro'
        verbose_name_plural = 'Metas de ahorro'

    def __str__(self):
        return f"{self.icono} {self.nombre}"

    @property
    def monto_actual(self):
        from django.db.models import Sum
        resultado = self.aportes.aggregate(total=Sum('monto'))['total']
        return resultado or 0

    @property
    def monto_restante(self):
        restante = self.monto_objetivo - self.monto_actual
        return max(restante, 0)

    @property
    def porcentaje(self):
        if self.monto_objetivo == 0:
            return 0
        pct = int((self.monto_actual / self.monto_objetivo) * 100)
        return min(pct, 100)

    @property
    def completada(self):
        return self.monto_actual >= self.monto_objetivo

    @property
    def dias_restantes(self):
        if self.fecha_objetivo:
            return (self.fecha_objetivo - timezone.now().date()).days
        return None

    @property
    def ahorro_mensual_necesario(self):
        dias = self.dias_restantes
        if dias and dias > 0 and self.monto_restante > 0:
            meses = max(dias / 30, 1)
            return int(self.monto_restante / meses)
        return None


class AporteMeta(models.Model):
    meta = models.ForeignKey(MetaAhorro, on_delete=models.CASCADE, related_name='aportes')
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    fecha = models.DateField(default=timezone.now)
    notas = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"${self.monto:,.0f} → {self.meta.nombre}"
