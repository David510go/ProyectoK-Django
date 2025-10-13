from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Cliente, Producto, Pedido, PedidoItem

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'activo')
    search_fields = ('nombre', 'email', 'telefono')
    list_filter = ('activo',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'precio', 'stock', 'activo')
    search_fields = ('sku', 'nombre')
    list_filter = ('activo',)
    list_editable = ('precio', 'stock', 'activo')

class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 1
    autocomplete_fields = ('producto',)
    fields = ('producto', 'cantidad', 'precio_unitario')
    min_num = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'estado', 'total')
    list_filter = ('estado', 'fecha')
    search_fields = ('cliente__nombre', 'id')
    date_hierarchy = 'fecha'
    inlines = [PedidoItemInline]
