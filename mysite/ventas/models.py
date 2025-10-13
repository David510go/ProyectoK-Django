from django.db import models

# Create your models here.

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sku} - {self.nombre}"

class Pedido(models.Model):
        ESTADOS = [
            ('nuevo', 'Nuevo'),
            ('procesado', 'Procesado'),
            ('cancelado', 'Cancelado'),
        ]
        cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='pedidos')
        fecha = models.DateTimeField(default=timezone.now)
        estado = models.CharField(max_length=20, choices=ESTADOS, default='nuevo')
        nota = models.TextField(blank=True, null=True)

        class Meta:
            ordering = ['-fecha']

        def __str__(self):
            return f"Pedido #{self.id} - {self.cliente}"

        @property
        def total(self):
            return sum((item.subtotal for item in self.items.all()), start=Decimal('0'))

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = [('pedido', 'producto')]

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        if self.precio_unitario in (None, Decimal('0')):
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)
