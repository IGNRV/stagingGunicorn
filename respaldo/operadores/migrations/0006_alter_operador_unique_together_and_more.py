# operadores/migrations/0006_alter_operador_unique_together_and_more.py
# -----------------------------------------------------------------------------
# Esta versión evita el error:
#   ValueError: Found wrong number (0) of constraints for "dm_sistema"."operador"
#               (username, empresa_id)
#
# ¿Qué cambia?
#   • Las dos operaciones `AlterUniqueTogether` se convierten en una única
#     operación `SeparateDatabaseAndState` que **solo** actúa sobre el *state*;
#     no hay modificación real en la base de datos, porque los constraints
#     ya fueron eliminados en la migración 0005 mediante SQL explícito.
#   • El resto del archivo se mantiene idéntico (AlterField, RemoveField, etc.).
# -----------------------------------------------------------------------------

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configuracion", "0002_remove_empresamodulo_empresa_and_more"),
        ("coreempresas", "0003_remove_empresaparam_idx_empresa_param_campo"),
        ("operadores",  "0005_remove_operador_idx_opr_emp_id_and_more"),
    ]

    operations = [
        # ------------------------------------------------------------------ #
        # 1.  Actualizamos SOLO el estado para quitar unique_together         #
        # ------------------------------------------------------------------ #
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="operador",
                    unique_together=set(),
                ),
                migrations.AlterUniqueTogether(
                    name="operadorgrupo",
                    unique_together=set(),
                ),
            ],
        ),

        # ------------------------------------------------------------------ #
        # 2.  AlterField → columnas reales, y demás cambios previstos         #
        # ------------------------------------------------------------------ #
        migrations.AlterField(
            model_name="operador",
            name="id",
            field=models.AutoField(db_column="id_operador", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="operador",
            name="id_empresa",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operadores",
                to="coreempresas.empresa",
            ),
        ),
        migrations.AlterField(
            model_name="operadorbodega",
            name="id",
            field=models.AutoField(db_column="id_operador_bodega", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="operadorbodega",
            name="id_empresa",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_bodegas",
                to="coreempresas.empresa",
            ),
        ),
        migrations.AlterField(
            model_name="operadorbodega",
            name="id_operador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="bodegas",
                to="operadores.operador",
            ),
        ),
        migrations.AlterField(
            model_name="operadorempresamodulo",
            name="id",
            field=models.AutoField(db_column="id_operador_empresa_modulo", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="operadorempresamodulo",
            name="id_empresa_modulo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos",
                to="configuracion.empresamodulo",
            ),
        ),
        migrations.AlterField(
            model_name="operadorempresamodulo",
            name="id_operador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos",
                to="operadores.operador",
            ),
        ),
        migrations.AlterField(
            model_name="operadorempresamodulomenu",
            name="id",
            field=models.AutoField(db_column="id_operador_empresa_modulo_menu", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="operadorempresamodulomenu",
            name="id_empresa_modulo_menu",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos_menus",
                to="configuracion.empresamodulomenu",
            ),
        ),
        migrations.AlterField(
            model_name="operadorempresamodulomenu",
            name="id_operador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos_menus",
                to="operadores.operador",
            ),
        ),
        migrations.AlterField(
            model_name="operadorgrupo",
            name="id",
            field=models.AutoField(db_column="id_operador_grupo", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="operadorgrupo",
            name="id_grupo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operadores_grupo",
                to="coreempresas.grupo",
            ),
        ),
        migrations.AlterField(
            model_name="operadorgrupo",
            name="id_operador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operadores_grupo",
                to="operadores.operador",
            ),
        ),
        migrations.AlterField(
            model_name="operadorpuntoventa",
            name="id",
            field=models.AutoField(db_column="id_operador_punto_venta", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="operadorpuntoventa",
            name="id_empresa",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_puntos_ventas",
                to="coreempresas.empresa",
            ),
        ),
        migrations.AlterField(
            model_name="operadorpuntoventa",
            name="id_operador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_puntos_venta",
                to="operadores.operador",
            ),
        ),
        migrations.AlterField(
            model_name="sesion",
            name="id",
            field=models.AutoField(db_column="id_sesion", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="sesion",
            name="id_operador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="sesion",
                to="operadores.operador",
            ),
        ),
        migrations.AlterField(
            model_name="sesionactiva",
            name="id",
            field=models.AutoField(db_column="id_sesion_activa", primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="sesionactiva",
            name="id_operador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="sesion_activa",
                to="operadores.operador",
            ),
        ),
        migrations.AlterField(
            model_name="sesionactiva",
            name="id_sesion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="sesion_activa",
                to="operadores.sesion",
            ),
        ),

        # Eliminamos los campos viejos que aún quedaban en las tablas
        migrations.RemoveField(model_name="operador",      name="empresa"),
        migrations.RemoveField(model_name="operador",      name="grupo"),
        migrations.RemoveField(model_name="operadorgrupo", name="grupo"),
        migrations.RemoveField(model_name="operadorgrupo", name="operador"),
    ]
