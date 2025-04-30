# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AjusteDetalleCompra(models.Model):
    id_empresa = models.IntegerField()
    id_proceso_comparacion = models.ForeignKey('ProcesoComparacion', models.DO_NOTHING, db_column='id_proceso_comparacion')
    id_orden_compra = models.ForeignKey('OrdenCompra', models.DO_NOTHING, db_column='id_orden_compra')
    id_detalle_compra = models.IntegerField()
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.FloatField()
    glosa = models.CharField(max_length=100)
    descuento = models.FloatField()
    tipo_descuento = models.CharField(max_length=10, blank=True, null=True)
    total_neto = models.FloatField()

    class Meta:
        managed = False
        db_table = '"dm_logistica"."ajuste_detalle_compra"'


class Atributo(models.Model):
    id_empresa = models.IntegerField()
    id_modelo_producto = models.ForeignKey('ModeloProducto', models.DO_NOTHING, db_column='id_modelo_producto')
    nombre_atributo = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."atributo"'


class AtributoDetalle(models.Model):
    id_empresa = models.IntegerField()
    id_atributo = models.ForeignKey(Atributo, models.DO_NOTHING, db_column='id_atributo')
    id_producto_bodega = models.ForeignKey('ProductoBodega', models.DO_NOTHING, db_column='id_producto_bodega')
    valor = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."atributo_detalle"'


class Bodega(models.Model):
    id_empresa = models.IntegerField()
    id_bodega_tipo = models.IntegerField()
    estado_bodega = models.IntegerField()
    nombre_bodega = models.CharField(max_length=100)
    nombre_tipo_bodega = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."bodega"'


class BodegaStock(models.Model):
    id_empresa = models.IntegerField()
    id_bodega = models.ForeignKey(Bodega, models.DO_NOTHING, db_column='id_bodega')
    id_modelo_producto = models.ForeignKey('ModeloProducto', models.DO_NOTHING, db_column='id_modelo_producto')
    stock_critico = models.IntegerField(blank=True, null=True)
    porc_alarma = models.IntegerField(blank=True, null=True)
    alarma = models.SmallIntegerField(blank=True, null=True)
    id_grupo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."bodega_stock"'


class BodegaTipo(models.Model):
    nombre_tipo_bodega = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."bodega_tipo"'


class ControlInventario(models.Model):
    id_empresa = models.IntegerField(blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)
    id_control_inventario = models.IntegerField(blank=True, null=True)
    id_operador = models.IntegerField()
    id_bodega = models.ForeignKey(Bodega, models.DO_NOTHING, db_column='id_bodega', blank=True, null=True)
    id_estado_control_inventario = models.ForeignKey('EstadoControlInventario', models.DO_NOTHING, db_column='id_estado_control_inventario', blank=True, null=True)
    id_tipo_control_inventario = models.ForeignKey('TipoControlInventario', models.DO_NOTHING, db_column='id_tipo_control_inventario', blank=True, null=True)
    fecha_termino = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."control_inventario"'


class Cotizacion(models.Model):
    id_empresa = models.IntegerField()
    id_proveedor = models.ForeignKey('Proveedor', models.DO_NOTHING, db_column='id_proveedor')
    id_solicitud_compra = models.ForeignKey('SolicitudCompra', models.DO_NOTHING, db_column='id_solicitud_compra', blank=True, null=True)
    fecha_cotizacion = models.DateTimeField()
    total = models.FloatField(blank=True, null=True)
    validez_cotizacion = models.IntegerField(blank=True, null=True)
    archivo = models.CharField(max_length=256, blank=True, null=True)
    estado_cotizacion = models.IntegerField(blank=True, null=True)
    estado_detalle = models.IntegerField(blank=True, null=True)
    iva = models.IntegerField(blank=True, null=True)
    folio = models.CharField(max_length=64, blank=True, null=True)
    id_operador = models.IntegerField()
    id_tipo_moneda = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."cotizacion"'


class DetalleCompra(models.Model):
    id_empresa = models.IntegerField()
    id_orden_compra = models.ForeignKey('OrdenCompra', models.DO_NOTHING, db_column='id_orden_compra')
    id_modelo_producto = models.ForeignKey('ModeloProducto', models.DO_NOTHING, db_column='id_modelo_producto')
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.FloatField(blank=True, null=True)
    glosa = models.CharField(max_length=100, blank=True, null=True)
    descuento_unitario = models.FloatField(blank=True, null=True)
    total_neto = models.FloatField(blank=True, null=True)
    tipo_item = models.IntegerField(blank=True, null=True)
    comprobado = models.IntegerField()
    producto_ingresado = models.IntegerField()
    fecha_ingreso_producto = models.DateTimeField(blank=True, null=True)
    id_operador_ingreso_producto = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."detalle_compra"'


class DetalleControlInventario(models.Model):
    id_empresa = models.IntegerField(blank=True, null=True)
    id_producto_bodega = models.ForeignKey('ProductoBodega', models.DO_NOTHING, db_column='id_producto_bodega', blank=True, null=True)
    id_estado_detalle_control_inventario = models.ForeignKey('EstadoDetalleControlInventario', models.DO_NOTHING, db_column='id_estado_detalle_control_inventario', blank=True, null=True)
    serie = models.CharField(max_length=100, blank=True, null=True)
    id_modelo_producto = models.ForeignKey('ModeloProducto', models.DO_NOTHING, db_column='id_modelo_producto', blank=True, null=True)
    id_estado_producto = models.ForeignKey('EstadoProducto', models.DO_NOTHING, db_column='id_estado_producto', blank=True, null=True)
    cantidad_original = models.FloatField(blank=True, null=True)
    cantidad_actual = models.FloatField(blank=True, null=True)
    nombre_modelo = models.CharField(max_length=100, blank=True, null=True)
    producto_seriado = models.IntegerField(blank=True, null=True)
    nombre_unidad_medida = models.CharField(max_length=30, blank=True, null=True)
    nombre_serie = models.CharField(max_length=45, blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)
    fecha_verificacion = models.DateTimeField(blank=True, null=True)
    id_control_inventario = models.ForeignKey(ControlInventario, models.DO_NOTHING, db_column='id_control_inventario', blank=True, null=True)
    id_operador = models.IntegerField()
    id_operador_verificador = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."detalle_control_inventario"'


class DetalleCotizacion(models.Model):
    id_empresa = models.IntegerField()
    id_cotizacion = models.ForeignKey(Cotizacion, models.DO_NOTHING, db_column='id_cotizacion')
    id_proveedor = models.ForeignKey('Proveedor', models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)
    cantidad = models.CharField(max_length=50, blank=True, null=True)
    detalles = models.CharField(max_length=255, blank=True, null=True)
    descuento_unitario = models.FloatField(blank=True, null=True)
    precio_unitario = models.FloatField(blank=True, null=True)
    id_modelo_producto = models.ForeignKey('ModeloProducto', models.DO_NOTHING, db_column='id_modelo_producto', blank=True, null=True)
    tipo_descuento = models.CharField(max_length=5, blank=True, null=True)
    tipo_item = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."detalle_cotizacion"'


class EstadoControlInventario(models.Model):
    id_empresa = models.IntegerField(blank=True, null=True)
    id_estado_solicitud_compra = models.ForeignKey('EstadoSolicitudCompra', models.DO_NOTHING, db_column='id_estado_solicitud_compra', blank=True, null=True)
    id_estado_compra = models.IntegerField(blank=True, null=True)
    id_estado_control_inventario = models.IntegerField(blank=True, null=True)
    detalle = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."estado_control_inventario"'


class EstadoDetalleControlInventario(models.Model):
    descripcion = models.CharField(max_length=45, blank=True, null=True)
    boton = models.IntegerField(blank=True, null=True)
    dboton = models.CharField(max_length=15, blank=True, null=True)
    icon = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."estado_detalle_control_inventario"'


class EstadoOrdenCompra(models.Model):
    descripcion = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."estado_orden_compra"'


class EstadoProducto(models.Model):
    nombre_estado_producto = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."estado_producto"'


class EstadoSolicitudCompra(models.Model):
    descripcion_solicitud_compra = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."estado_solicitud_compra"'


class Giro(models.Model):
    id_empresa = models.IntegerField()
    id_proveedor = models.IntegerField()
    descrip_giro = models.CharField(max_length=250)
    codigo_sii = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."giro"'


class IdentificadorSerie(models.Model):
    nombre_serie = models.CharField(max_length=45)
    estado_serie = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"dm_logistica"."identificador_serie"'


class MarcaProducto(models.Model):
    id_empresa = models.IntegerField()
    nombre_marca_producto = models.CharField(max_length=50)
    estado = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"dm_logistica"."marca_producto"'


class ModeloProducto(models.Model):
    id_modelo_producto = models.IntegerField(primary_key=True)  # The composite primary key (id_modelo_producto, id_empresa) found, that is not supported. The first column is selected.
    id_empresa = models.IntegerField()
    id_tipo_marca_producto = models.ForeignKey('TipoMarcaProducto', models.DO_NOTHING, db_column='id_tipo_marca_producto')
    id_identificador_serie = models.ForeignKey(IdentificadorSerie, models.DO_NOTHING, db_column='id_identificador_serie')
    id_unidad_medida = models.ForeignKey('UnidadMedida', models.DO_NOTHING, db_column='id_unidad_medida')
    codigo_interno = models.CharField(max_length=50, blank=True, null=True)
    fccid = models.CharField(max_length=50, blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    sku_codigo = models.CharField(max_length=255, blank=True, null=True)
    nombre_modelo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.CharField(max_length=200, blank=True, null=True)
    estado = models.IntegerField()
    producto_seriado = models.IntegerField()
    nombre_comercial = models.CharField(max_length=255, blank=True, null=True)
    despacho_express = models.IntegerField()
    rebaja_consumo = models.IntegerField(blank=True, null=True)
    dias_rebaja_consumo = models.IntegerField(blank=True, null=True)
    orden_solicitud_despacho = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."modelo_producto"'
        unique_together = (('id_modelo_producto', 'id_empresa'),)


class ModeloProductoValores(models.Model):
    id_empresa = models.IntegerField()
    id_modelo_producto = models.ForeignKey(ModeloProducto, models.DO_NOTHING, db_column='id_modelo_producto')
    valor_cliente = models.IntegerField(blank=True, null=True)
    valor_publico = models.IntegerField(blank=True, null=True)
    margen = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."modelo_producto_valores"'


class Movimiento(models.Model):
    id_empresa = models.IntegerField()
    folio = models.CharField(max_length=9, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    operador_emision = models.IntegerField()
    operador_destino = models.IntegerField()
    id_tipo_movimiento = models.IntegerField(blank=True, null=True)
    id_bodega = models.ForeignKey(Bodega, models.DO_NOTHING, db_column='id_bodega')
    fecha_registro = models.DateTimeField()
    tipo_movimiento = models.CharField(max_length=50, blank=True, null=True)
    id_bodega_origen = models.ForeignKey(Bodega, models.DO_NOTHING, db_column='id_bodega_origen', related_name='movimiento_id_bodega_origen_set')
    id_despachador = models.IntegerField(blank=True, null=True)
    id_receptor = models.IntegerField(blank=True, null=True)
    id_punto_venta = models.IntegerField(blank=True, null=True)
    pdf = models.CharField(max_length=255, blank=True, null=True)
    folio_comprobante = models.CharField(max_length=32, blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(blank=True, null=True)
    id_requerimiento = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"dm_logistica"."movimiento"'


class MovimientoBodega(models.Model):
    id_empresa = models.IntegerField()
    id_movimiento = models.ForeignKey(Movimiento, models.DO_NOTHING, db_column='id_movimiento', blank=True, null=True)
    id_producto_bodega = models.ForeignKey('ProductoBodega', models.DO_NOTHING, db_column='id_producto_bodega', blank=True, null=True)
    id_ejecutivo_terreno = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=15, blank=True, null=True)
    id_ejecutivo_recibe = models.IntegerField(blank=True, null=True)
    obs = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."movimiento_bodega"'


class OrdenCompra(models.Model):
    id_empresa = models.IntegerField()
    id_cotizacion = models.ForeignKey(Cotizacion, models.DO_NOTHING, db_column='id_cotizacion')
    id_solicitante = models.IntegerField()
    id_operador = models.IntegerField()
    id_estado_orden_compra = models.ForeignKey(EstadoOrdenCompra, models.DO_NOTHING, db_column='id_estado_orden_compra')
    id_solicitud_compra = models.ForeignKey('SolicitudCompra', models.DO_NOTHING, db_column='id_solicitud_compra')
    id_proveedor = models.ForeignKey('Proveedor', models.DO_NOTHING, db_column='id_proveedor')
    folio = models.CharField(max_length=30, blank=True, null=True)
    fecha = models.DateTimeField()
    neto = models.FloatField(blank=True, null=True)
    iva = models.FloatField(blank=True, null=True)
    monto_total = models.FloatField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    id_aprobador = models.IntegerField()
    archivo = models.CharField(max_length=256, blank=True, null=True)
    notas_adicionales = models.TextField(blank=True, null=True)
    id_requerimiento = models.IntegerField()
    id_tipo_moneda = models.IntegerField(blank=True, null=True)
    operador_anula = models.IntegerField()
    fecha_anula = models.DateTimeField(blank=True, null=True)
    motivo_anula = models.TextField(blank=True, null=True)
    desviacion = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."orden_compra"'


class ProcesoComparacion(models.Model):
    id_empresa = models.IntegerField()
    id_orden_compra = models.ForeignKey(OrdenCompra, models.DO_NOTHING, db_column='id_orden_compra')
    id_operador = models.IntegerField()
    fecha_comparacion = models.DateTimeField()
    estado_comparacion = models.IntegerField()
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."proceso_comparacion"'


class ProductoBodega(models.Model):
    id_empresa = models.IntegerField()
    id_detalle_compra = models.IntegerField()
    serie = models.CharField(max_length=100)
    id_bodega = models.ForeignKey(Bodega, models.DO_NOTHING, db_column='id_bodega')
    id_modelo_producto = models.ForeignKey(ModeloProducto, models.DO_NOTHING, db_column='id_modelo_producto')
    id_estado_producto = models.ForeignKey(EstadoProducto, models.DO_NOTHING, db_column='id_estado_producto')
    id_producto_bodega_pack = models.ForeignKey('self', models.DO_NOTHING, db_column='id_producto_bodega_pack', blank=True, null=True)
    lote = models.CharField(max_length=50, blank=True, null=True)
    cantidad_original = models.FloatField()
    id_producto_bodega_origen = models.ForeignKey('self', models.DO_NOTHING, db_column='id_producto_bodega_origen', related_name='productobodega_id_producto_bodega_origen_set')
    cantidad_actual = models.FloatField()
    fecha_registro = models.DateTimeField()
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    id_operador = models.IntegerField()
    id_ejecutivo_stock = models.IntegerField()
    id_punto_venta_stock = models.IntegerField()
    id_movimiento = models.ForeignKey(Movimiento, models.DO_NOTHING, db_column='id_movimiento')
    inventario = models.TextField(blank=True, null=True)
    tipo_serie = models.CharField(max_length=50, blank=True, null=True)
    valor_serie = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."producto_bodega"'


class Proveedor(models.Model):
    giro = models.CharField(max_length=250)
    descrip_giro = models.CharField(max_length=250, blank=True, null=True)
    id_empresa = models.IntegerField()
    rut = models.CharField(max_length=20)
    nombre_rs = models.CharField(max_length=200)
    nombre_fantasia = models.CharField(max_length=200, blank=True, null=True)
    web = models.CharField(max_length=50, blank=True, null=True)
    fecha_alta = models.DateTimeField()
    modalidad_pago = models.CharField(max_length=50, blank=True, null=True)
    plazo_pago = models.IntegerField(blank=True, null=True)
    estado = models.IntegerField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    id_comuna = models.IntegerField(blank=True, null=True)
    id_region = models.IntegerField(blank=True, null=True)
    proveedor_unico = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."proveedor"'


class ProveedorContactos(models.Model):
    id_proveedor_telefono = models.ForeignKey('ProveedorTelefono', models.DO_NOTHING, db_column='id_proveedor_telefono')
    contacto = models.CharField(max_length=100, blank=True, null=True)
    relacion_contacto = models.CharField(max_length=50, blank=True, null=True)
    telefono_contacto = models.CharField(max_length=20, blank=True, null=True)
    mail_contacto = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."proveedor_contactos"'


class ProveedorTelefono(models.Model):
    id_proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='id_proveedor')
    telefono = models.CharField(max_length=50, blank=True, null=True)
    principal = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."proveedor_telefono"'


class ServiciosBasicos(models.Model):
    id_empresa = models.IntegerField()
    id_operador = models.IntegerField()
    id_proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    item_presupuesto = models.CharField(max_length=6, blank=True, null=True)
    fecha_registro = models.DateTimeField()
    observacion = models.TextField(blank=True, null=True)
    id_punto_venta = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."servicios_basicos"'


class ServiciosCajaChica(models.Model):
    monto = models.FloatField(blank=True, null=True)
    id_empresa = models.IntegerField()
    id_operador = models.IntegerField()
    id_operador_autoriza = models.CharField(max_length=50)
    fecha_registro = models.DateTimeField()
    fecha_autoriza = models.DateField(blank=True, null=True)
    nota = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    motivo_rechazo = models.TextField(blank=True, null=True)
    archivo = models.CharField(max_length=255, blank=True, null=True)
    id_punto_venta = models.IntegerField(blank=True, null=True)
    id_solicitante = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."servicios_caja_chica"'


class ServiciosCajaChicaDetalle(models.Model):
    id_empresa = models.IntegerField()
    id_servicios_caja_chica = models.ForeignKey(ServiciosCajaChica, models.DO_NOTHING, db_column='id_servicios_caja_chica', blank=True, null=True)
    tipo_doc = models.CharField(max_length=50, blank=True, null=True)
    fecha_emision = models.DateTimeField(blank=True, null=True)
    razon_social = models.CharField(max_length=50, blank=True, null=True)
    folio_dt = models.CharField(max_length=50, blank=True, null=True)
    monto = models.FloatField(blank=True, null=True)
    detalle = models.CharField(max_length=255, blank=True, null=True)
    item_presupuesto = models.CharField(max_length=10, blank=True, null=True)
    archivo = models.CharField(max_length=255, blank=True, null=True)
    id_operador = models.IntegerField()
    fecha_registro = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."servicios_caja_chica_detalle"'


class SolicitudCompra(models.Model):
    id_empresa = models.IntegerField()
    id_operador = models.IntegerField()
    id_aprobador = models.IntegerField()
    id_estado_solicitud_compra = models.ForeignKey(EstadoSolicitudCompra, models.DO_NOTHING, db_column='id_estado_solicitud_compra')
    fecha_registro = models.DateTimeField()
    descripcion = models.TextField()
    fecha_solicitud_compra = models.DateTimeField(blank=True, null=True)
    id_tipo_solicitud = models.ForeignKey('TipoSolicitud', models.DO_NOTHING, db_column='id_tipo_solicitud')
    titulo = models.CharField(max_length=100, blank=True, null=True)
    ruta_file = models.CharField(max_length=255, blank=True, null=True)
    cod_presupuesto = models.CharField(max_length=10, blank=True, null=True)
    id_punto_venta = models.IntegerField(blank=True, null=True)
    operador_rechazo = models.CharField(max_length=50, blank=True, null=True)
    fecha_rechazo = models.DateTimeField(blank=True, null=True)
    motivo_rechazo = models.TextField(blank=True, null=True)
    id_requerimiento = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."solicitud_compra"'


class TipoControlInventario(models.Model):
    detalle = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."tipo_control_inventario"'


class TipoMarcaProducto(models.Model):
    id_empresa = models.IntegerField()
    id_tipo_producto = models.IntegerField()
    id_marca_producto = models.ForeignKey(MarcaProducto, models.DO_NOTHING, db_column='id_marca_producto')

    class Meta:
        managed = False
        db_table = '"dm_logistica"."tipo_marca_producto"'


class TipoProducto(models.Model):
    codigo_tipo_producto = models.CharField(max_length=255, blank=True, null=True)
    id_empresa = models.IntegerField()
    nombre_tipo_producto = models.CharField(max_length=100)
    estado = models.IntegerField()
    correlativo_desde = models.IntegerField(blank=True, null=True)
    correlativo_hasta = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."tipo_producto"'


class TipoSolicitud(models.Model):
    descripcion = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."tipo_solicitud"'


class UnidadMedida(models.Model):
    nombre_unidad_medida = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_logistica"."unidad_medida"'
