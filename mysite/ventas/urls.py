# ventas/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("productos/", views.ProductoListView.as_view(), name="producto_list"),
    path("productos/<int:pk>/", views.ProductoDetailView.as_view(), name="producto_detail"),

    path("clientes/", views.ClienteListView.as_view(), name="cliente_list"),

    path("pedidos/", views.PedidoListView.as_view(), name="pedido_list"),
    path("pedidos/<int:pk>/", views.PedidoDetailView.as_view(), name="pedido_detail"),
    path("pedidos/nuevo/", views.PedidoCreateView.as_view(), name="pedido_create"),
    path("pedidos/<int:pk>/procesar/", views.pedido_procesar, name="pedido_procesar"),
    path("pedidos/<int:pk>/cancelar/", views.pedido_cancelar, name="pedido_cancelar"),
]

