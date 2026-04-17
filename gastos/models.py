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


class Prestamo(models.Model):
    TIPO_CHOICES = [
        ('recibido', 'Me prestaron a mí'),   # yo debo dinero
        ('otorgado', 'Yo presté dinero'),     # me deben a mí
    ]
    ESTADO_CHOICES = [
        ('vigente', 'Vigente'),
        ('saldado', 'Saldado'),
        ('vencido', 'Vencido'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prestamos')
    
    # Quién es la otra persona involucrada
    persona = models.CharField(max_length=150, help_text='Nombre de quien prestó o a quien prestaste')
    
    # Descripción del motivo
    concepto = models.CharField(max_length=200, help_text='Ej: Gastos médicos, Arriendo, Vacaciones')
    
    # Monto original del préstamo
    monto_total = models.DecimalField(max_digits=12, decimal_places=0)
    
    # Cuánto se ha pagado hasta ahora (se actualiza con cada pago)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='recibido')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='vigente')
    
    fecha_prestamo = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField(null=True, blank=True, help_text='Fecha límite para pagar (opcional)')
    
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_prestamo']
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'

    def __str__(self):
        return f"{self.persona} — ${self.monto_total:,.0f} ({self.get_tipo_display()})"

    # ---- Propiedades calculadas (no se guardan en BD) ----

    @property
    def monto_adeudado(self):
        """Cuánto queda por pagar. Se calcula siempre al vuelo."""
        return self.monto_total - self.monto_pagado

    @property
    def porcentaje_pagado(self):
        """Para la barra de progreso en el template."""
        if self.monto_total == 0:
            return 0
        return int((self.monto_pagado / self.monto_total) * 100)

    @property
    def esta_saldado(self):
        return self.monto_pagado >= self.monto_total

    @property
    def esta_vencido(self):
        if self.fecha_vencimiento and self.estado == 'vigente':
            return self.fecha_vencimiento < timezone.now().date()
        return False
    
class PagoPrestamo(models.Model):
    """Cada vez que se registra un pago parcial o total de un préstamo."""
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    fecha = models.DateField(default=timezone.now)
    notas = models.CharField(max_length=200, blank=True, help_text='Ej: transferencia, efectivo')

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
    nombre = models.CharField(max_length=150, help_text='Ej: Viaje a Buenos Aires')
    icono = models.CharField(max_length=5, choices=ICONO_CHOICES, default='💰')
    monto_objetivo = models.DecimalField(max_digits=12, decimal_places=0)
    fecha_objetivo = models.DateField(null=True, blank=True, help_text='¿Para cuándo querés tenerlo?')
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
        """Suma todos los aportes. Se recalcula cada vez, sin guardar."""
        from django.db.models import Sum
        resultado = self.aportes.aggregate(total=Sum('monto'))['total']
        return resultado or 0

    @property
    def monto_restante(self):
        return self.monto_objetivo - self.monto_actual

    @property
    def porcentaje(self):
        if self.monto_objetivo == 0:
            return 0
        pct = int((self.monto_actual / self.monto_objetivo) * 100)
        return min(pct, 100)  # no puede superar 100%

    @property
    def completada(self):
        return self.monto_actual >= self.monto_objetivo

    @property
    def dias_restantes(self):
        if self.fecha_objetivo:
            delta = self.fecha_objetivo - timezone.now().date()
            return delta.days
        return None

    @property
    def ahorro_mensual_necesario(self):
        """
        Calcula cuánto hay que ahorrar por mes para llegar al objetivo.
        Útil para mostrar "necesitás ahorrar X por mes".
        Solo tiene sentido si hay fecha objetivo y monto restante > 0.
        """
        dias = self.dias_restantes
        if dias and dias > 0 and self.monto_restante > 0:
            meses = max(dias / 30, 1)
            return int(self.monto_restante / meses)
        return None


class AporteMeta(models.Model):
    """Cada vez que la usuaria deposita algo a su meta."""
    meta = models.ForeignKey(MetaAhorro, on_delete=models.CASCADE, related_name='aportes')
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    fecha = models.DateField(default=timezone.now)
    notas = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"${self.monto:,.0f} → {self.meta.nombre} ({self.fecha})"
