# === ./dm_sistema/urls.py ===
from django.urls import path

from .views import (
    OperadorLoginAPIView,
    OperadorCodigoVerificacionAPIView,
    OperadorSesionActivaTokenAPIView,
    OperadorLogoutAPIView,
    # -------- LOGÍSTICA – PROVEEDOR -------- #
    ProveedorCreateAPIView,
    ProveedorListAPIView,
    ProveedorDetailAPIView,
    ProveedorUpdateAPIView,
    # -------- LOGÍSTICA – BODEGA ----------- #
    BodegaListAPIView,
    BodegaUpdateAPIView,
    BodegaCreateAPIView,
    BodegaDetailAPIView,
    # -------- LOGÍSTICA – BODEGA TIPO ------ #
    BodegaTipoListAPIView,
    BodegaTipoDetailAPIView,
    # -------- LOGÍSTICA – BODEGAS “COMPLETAS” – JOIN -------- #
    BodegaCompletaListAPIView,
    # -------- LOGÍSTICA – TIPO PRODUCTO ---- #
    TipoProductoCreateAPIView,
    TipoProductoListAPIView,
    TipoProductoUpdateAPIView,
    TipoProductoDetailAPIView,
    # -------- LOGÍSTICA – MARCA PRODUCTO --- #
    MarcaProductoCreateAPIView,
    MarcaProductoListAPIView,
    MarcaProductoUpdateAPIView,
    MarcaProductoDetailAPIView,
    # -------- LOGÍSTICA – TIPO-MARCA ------ #
    TipoMarcaProductoCreateAPIView,
    TipoMarcaProductoListAPIView,
    TipoMarcaProductoUpdateAPIView,
    TipoMarcaProductoDetailAPIView,
    TipoMarcaProductoDeleteAPIView,
    # -------- LOGÍSTICA – MODELO PRODUCTO -- #
    ModeloProductoCreateAPIView,
    ModeloProductoListAPIView,
    ModeloProductoUpdateAPIView,
    ModeloProductoDetailAPIView,
    # ----------------- NUEVO ENDPOINTS ----------------- #
    ModeloProductoCompletoListAPIView,
    ModeloProductoCompletoDetailAPIView,
    # -------- NUEVO (★) JOIN TIPO‑MARCA‑PRODUCTO -------- #
    TipoMarcaProductoJoinDetailAPIView,
    # -------------------------------------------------- #
    # -------- NUEVO ENDPOINT ATRIBUTOS ----------------- #
    ModeloProductoAtributosAPIView,
    # -------- ★★★ NUEVOS ENDPOINTS ATRIBUTO ------------ #
    AtributoUpdateAPIView,          # PUT
    AtributoCreateAPIView,          # ← NUEVO POST
    AtributoDetailAPIView,
    # -------- SISTEMA ----------- #
    ComunaListAPIView,
    ComunaByRegionAPIView,
    RegionListAPIView,
    IdentificadorSerieListAPIView,
    UnidadMedidaListAPIView,
)

urlpatterns = [
    # --------------------------- OPERADORES ----------------------------- #
    path("operadores/validar/",   OperadorLoginAPIView.as_view(),              name="operador-login"),
    path("operadores/verificar/", OperadorCodigoVerificacionAPIView.as_view(), name="operador-verificar"),
    path("operadores/sesiones-activas-token/", OperadorSesionActivaTokenAPIView.as_view(), name="operador-sesion-por-token"),
    path("operadores/logout/", OperadorLogoutAPIView.as_view(), name="operador-logout"),

    # --------------------------- LOGÍSTICA – PROVEEDOR ------------------ #
    path("logistica/proveedores/crear/",   ProveedorCreateAPIView.as_view(),  name="proveedor-crear"),
    path("logistica/proveedores/",         ProveedorListAPIView.as_view(),    name="proveedor-listar"),
    path("logistica/proveedores/detalle/", ProveedorDetailAPIView.as_view(),  name="proveedor-detalle"),
    path("logistica/proveedores/editar/",  ProveedorUpdateAPIView.as_view(),  name="proveedor-editar"),

    # --------------------------- LOGÍSTICA – BODEGA --------------------- #
    path("logistica/bodegas/",            BodegaListAPIView.as_view(),       name="bodega-listar"),
    path("logistica/bodegas/crear/",      BodegaCreateAPIView.as_view(),     name="bodega-crear"),
    path("logistica/bodegas/detalle/",    BodegaDetailAPIView.as_view(),     name="bodega-detalle"),
    path("logistica/bodegas/editar/",     BodegaUpdateAPIView.as_view(),     name="bodega-editar"),

    # --------------------------- LOGÍSTICA – BODEGA TIPO ---------------- #
    path("logistica/bodegas/tipos/",         BodegaTipoListAPIView.as_view(),   name="bodega-tipo-listar"),
    path("logistica/bodegas/tipos/detalle/", BodegaTipoDetailAPIView.as_view(), name="bodega-tipo-detalle"),

    # ------------ LOGÍSTICA – BODEGAS CON JOIN (tipos) ------------------ #
    path("logistica/bodegas-completas/", BodegaCompletaListAPIView.as_view(), name="bodega-completa-listar"),

    # --------------------------- LOGÍSTICA – TIPO PRODUCTO -------------- #
    path("logistica/tipos-producto/",         TipoProductoListAPIView.as_view(),   name="tipo-producto-listar"),
    path("logistica/tipos-producto/crear/",   TipoProductoCreateAPIView.as_view(), name="tipo-producto-crear"),
    path("logistica/tipos-producto/editar/",  TipoProductoUpdateAPIView.as_view(), name="tipo-producto-editar"),
    path("logistica/tipos-producto/detalle/", TipoProductoDetailAPIView.as_view(), name="tipo-producto-detalle"),

    # --------------------------- LOGÍSTICA – MARCA PRODUCTO ------------- #
    path("logistica/marcas-producto/",         MarcaProductoListAPIView.as_view(),    name="marca-producto-listar"),
    path("logistica/marcas-producto/crear/",   MarcaProductoCreateAPIView.as_view(),  name="marca-producto-crear"),
    path("logistica/marcas-producto/editar/",  MarcaProductoUpdateAPIView.as_view(),  name="marca-producto-editar"),
    path("logistica/marcas-producto/detalle/", MarcaProductoDetailAPIView.as_view(),  name="marca-producto-detalle"),

    # --------------------------- LOGÍSTICA – TIPO-MARCA PRODUCTO -------- #
    path("logistica/tipo-marca-producto/crear/",   TipoMarcaProductoCreateAPIView.as_view(),  name="tipo-marca-producto-crear"),
    path("logistica/tipo-marca-producto/",         TipoMarcaProductoListAPIView.as_view(),    name="tipo-marca-producto-listar"),
    path("logistica/tipo-marca-producto/editar/",  TipoMarcaProductoUpdateAPIView.as_view(),  name="tipo-marca-producto-editar"),
    path("logistica/tipo-marca-producto/detalle/", TipoMarcaProductoDetailAPIView.as_view(),  name="tipo-marca-producto-detalle"),
    path("logistica/tipo-marca-producto/eliminar/", TipoMarcaProductoDeleteAPIView.as_view(),   name="tipo-marca-producto-eliminar"),

    # ---------- ★ NUEVO ENDPOINT – JOIN TIPO‑MARCA‑PRODUCTO ------------- #
    path(
        "logistica/tipo-marca-producto-completo/",
        TipoMarcaProductoJoinDetailAPIView.as_view(),
        name="tipo-marca-producto-completo-detalle",
    ),

    # --------------------------- LOGÍSTICA – MODELO PRODUCTO ----------- #
    path("logistica/modelo-producto/crear/",   ModeloProductoCreateAPIView.as_view(),   name="modelo-producto-crear"),
    path("logistica/modelo-producto/",         ModeloProductoListAPIView.as_view(),     name="modelo-producto-listar"),
    path("logistica/modelo-producto/editar/",  ModeloProductoUpdateAPIView.as_view(),   name="modelo-producto-editar"),
    path("logistica/modelo-producto/detalle/", ModeloProductoDetailAPIView.as_view(),   name="modelo-producto-detalle"),

    # ---------------------- NUEVOS ENDPOINTS ---------------------------- #
    path("logistica/modelos-producto-completos/", ModeloProductoCompletoListAPIView.as_view(),   name="modelo-producto-completo-listar"),
    path("logistica/modelo-producto-completo/",   ModeloProductoCompletoDetailAPIView.as_view(), name="modelo-producto-completo-detalle"),

    # ---------------------- NUEVO ENDPOINT ATRIBUTOS (GET) -------------- #
    path(
        "logistica/modelo-producto-atributos/",
        ModeloProductoAtributosAPIView.as_view(),
        name="modelo-producto-atributos",
    ),

    # ---------------------- ENDPOINTS ATRIBUTO -------------------------- #
    path("logistica/atributo/crear/", AtributoCreateAPIView.as_view(), name="atributo-crear"),   # ← NUEVO
    path("logistica/atributo/editar/", AtributoUpdateAPIView.as_view(), name="atributo-editar"),
    path("logistica/atributo/detalle/", AtributoDetailAPIView.as_view(), name="atributo-detalle"),  # ← NUEVO

    # --------------------------- SISTEMA – COMUNAS / REGIONES ----------- #
    path("comunas/",            ComunaListAPIView.as_view(),     name="comuna-listar"),
    path("comunas/por-region/", ComunaByRegionAPIView.as_view(), name="comuna-por-region"),
    path("regiones/",           RegionListAPIView.as_view(),     name="region-listar"),

    # -------- LOGÍSTICA – IDENTIFICADORES DE SERIE -------- #
    path("logistica/identificadores-serie/", IdentificadorSerieListAPIView.as_view(), name="identificador-serie-listar"),

    # -------- LOGÍSTICA – UNIDADES DE MEDIDA -------- #
    path("logistica/unidades-medida/", UnidadMedidaListAPIView.as_view(), name="unidad-medida-listar"),
]
