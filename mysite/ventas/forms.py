from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet 
from collections import defaultdict
from .models import Pedido, PedidoItem, Producto


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente", "nota"]


class PedidoItemForm(forms.ModelForm):
    class Meta:
        model = PedidoItem
        fields = ["producto", "cantidad", "precio_unitario"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qs = Producto.objects.filter(activo=True).order_by("nombre")
        self.fields["producto"].queryset = qs
        self.fields["producto"].label_from_instance = (
            lambda obj: f"{obj.sku} - {obj.nombre} (Disp: {obj.stock})"
        )

        self.fields["cantidad"].widget.attrs.update({"min": 1})
        self.fields["precio_unitario"].widget.attrs.update({"step": "0.01", "min": "0"})

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        cantidad = cleaned.get("cantidad")

        if producto and cantidad:
            if cantidad <= 0:
                self.add_error("cantidad", "La cantidad debe ser mayor que 0.")
            elif cantidad > producto.stock:
                self.add_error("cantidad", f"No hay stock suficiente. Disponible: {producto.stock}")
        return cleaned


class ValidatingPedidoItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(form.errors for form in self.forms):
            return

        cantidades_por_producto = defaultdict(int)

        for form in self.forms:
            if getattr(form, "cleaned_data", None) and not form.cleaned_data.get("DELETE", False):
                producto = form.cleaned_data.get("producto")
                cantidad = form.cleaned_data.get("cantidad") or 0
                if producto:
                    cantidades_por_producto[producto.pk] += cantidad

        faltantes = []
        for prod_id, total in cantidades_por_producto.items():
            try:
                prod = Producto.objects.get(pk=prod_id)
            except Producto.DoesNotExist:
                continue
            if total > prod.stock:
                faltantes.append(f"{prod.sku} - {prod.nombre}: solicitado {total}, disponible {prod.stock}")

        if faltantes:
            raise forms.ValidationError(
                "Stock insuficiente en uno o más productos:\n- " + "\n- ".join(faltantes)
            )


PedidoItemFormSet = inlineformset_factory(
    Pedido,
    PedidoItem,
    form=PedidoItemForm,
    fields=["producto", "cantidad", "precio_unitario"],
    extra=1,
    can_delete=True,
    formset=ValidatingPedidoItemFormSet
)

