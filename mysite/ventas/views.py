from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Producto, Cliente 


from .models import Pedido, PedidoItem, Producto
from .forms import PedidoForm, PedidoItemFormSet

class PedidoListView(ListView):
    model = Pedido
    template_name = "ventas/pedido_list.html"
    context_object_name = "pedidos"
    paginate_by = 20

class PedidoDetailView(DetailView):
    model = Pedido
    template_name = "ventas/pedido_detail.html"
    context_object_name = "pedido"

class PedidoCreateView(CreateView):
    model = Pedido
    form_class = PedidoForm
    template_name = "ventas/pedido_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["formset"] = PedidoItemFormSet(self.request.POST)
        else:
            ctx["formset"] = PedidoItemFormSet()
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx["formset"]
        if formset.is_valid():
            pedido = form.save(commit=False)
            pedido.estado = "nuevo"  # se crea como nuevo
            pedido.save()
            formset.instance = pedido
            formset.save()
            messages.success(self.request, f"Pedido #{pedido.id} creado en estado 'nuevo'.")
            return redirect("pedido_detail", pk=pedido.pk)
        else:
            return self.form_invalid(form)

@transaction.atomic
def pedido_procesar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if pedido.estado != "nuevo":
        messages.info(request, "Solo se pueden procesar pedidos en estado 'nuevo'.")
        return redirect("pedido_detail", pk=pk)

    # Validar stock y descontar
    # Bloque transaccional para evitar sobreventa en concurrencia
    for item in pedido.items.select_related("producto").all():
        prod = item.producto
        if item.cantidad > prod.stock:
            messages.error(request, f"Stock insuficiente para {prod} (stock: {prod.stock}, requerido: {item.cantidad}).")
            return redirect("pedido_detail", pk=pk)

    # Si todo ok, descontar
    for item in pedido.items.select_related("producto").all():
        prod = item.producto
        prod.stock = prod.stock - item.cantidad
        prod.save(update_fields=["stock"])

    pedido.estado = "procesado"
    pedido.save(update_fields=["estado"])
    messages.success(request, f"Pedido #{pedido.id} procesado y stock actualizado.")
    return redirect("pedido_detail", pk=pk)

@transaction.atomic
def pedido_cancelar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if pedido.estado == "procesado":
        # Reponer stock al cancelar un pedido ya procesado
        for item in pedido.items.select_related("producto").all():
            prod = item.producto
            prod.stock = prod.stock + item.cantidad
            prod.save(update_fields=["stock"])
    pedido.estado = "cancelado"
    pedido.save(update_fields=["estado"])
    messages.success(request, f"Pedido #{pedido.id} cancelado.")
    return redirect("pedido_detail", pk=pk)

class ProductoListView(ListView):
    model = Producto
    template_name = "ventas/producto_list.html"
    context_object_name = "productos"
    paginate_by = 12

    def get_queryset(self):
        qs = Producto.objects.filter(activo=True).order_by("nombre")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(sku__icontains=q))
        return qs


class ProductoDetailView(DetailView):
    model = Producto
    template_name = "ventas/producto_detail.html"
    context_object_name = "producto"


class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = "ventas/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 20
    permission_required = "ventas.view_cliente"

    def get_queryset(self):
        qs = Cliente.objects.filter(activo=True).order_by("nombre")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(email__icontains=q))
        return qs




