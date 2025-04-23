# coreempresas/migrations/0002_remove_empresaparam_idx_empresa_param_empresa_id_and_more.py
# -----------------------------------------------------------------------------
# Corrige definitivamente el error “relation "idx_empresa_param_campo" does not exist”.
# En vez de renombrar el índice, lo eliminamos con seguridad si llegara a existir
# (en cualquier esquema) y luego volvemos a crearlo con AddIndex.
# -----------------------------------------------------------------------------

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coreempresas", "0001_initial"),
    ]

    operations = [
        # ---------------------------------------------------------------------
        # 1. Eliminar el índice antiguo *solo* si existe.
        #    - Buscamos el índice por nombre en TODO el clúster.
        #    - Si lo encontramos, lo suprimimos con EXECUTE format().
        # ---------------------------------------------------------------------
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    _idx_oid oid;
                BEGIN
                    SELECT c.oid
                    INTO   _idx_oid
                    FROM   pg_class c
                    WHERE  c.relname = 'idx_empresa_param_campo'
                    LIMIT  1;

                    IF FOUND THEN
                        EXECUTE (
                            SELECT format(
                                'DROP INDEX IF EXISTS %I.%I',
                                n.nspname,  -- esquema
                                c.relname   -- nombre del índice
                            )
                            FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE c.oid = _idx_oid
                        );
                    END IF;
                END$$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ---------------------------------------------------------------------
        # 2. Borramos el índice idx_empresa_param_empresa_id generado en 0001.
        #    (sigue igual que en tu migración original)
        # ---------------------------------------------------------------------
        migrations.RemoveIndex(
            model_name="empresaparam",
            name="idx_empresa_param_empresa_id",
        ),

        # ---------------------------------------------------------------------
        # 3. Sustituimos claves foráneas antiguas por las nuevas.
        # ---------------------------------------------------------------------
        migrations.RemoveField(model_name="empresaparam",    name="empresa"),
        migrations.RemoveField(model_name="empresaresolucion", name="empresa"),
        migrations.RemoveField(model_name="empresatelefono",  name="empresa"),
        migrations.RemoveField(model_name="grupo",            name="empresa"),

        migrations.AddField(
            model_name="empresaparam",
            name="id_empresa",
            field=models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=models.deletion.RESTRICT,
                related_name="parametros",
                default=1,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="empresaresolucion",
            name="id_empresa",
            field=models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=models.deletion.RESTRICT,
                related_name="resoluciones",
                default=1,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="empresatelefono",
            name="id_empresa",
            field=models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=models.deletion.RESTRICT,
                related_name="telefonos",
                default=1,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="grupo",
            name="id_empresa",
            field=models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=models.deletion.RESTRICT,
                related_name="grupos",
                null=True,
                blank=True,
            ),
        ),

        # ---------------------------------------------------------------------
        # 4. Nuevos índices (o recreación) con los nombres correctos.
        # ---------------------------------------------------------------------
        migrations.AddIndex(
            model_name="empresa",
            index=models.Index(fields=["ingreso_pcd"], name="idx_emp_ing_pcd"),
        ),
        migrations.AddIndex(
            model_name="empresaparam",
            index=models.Index(fields=["id_empresa"], name="idx_emp_par_emp_id"),
        ),
        migrations.AddIndex(
            model_name="empresaparam",
            index=models.Index(fields=["campo"], name="idx_emp_par_campo"),
        ),
        migrations.AddIndex(
            model_name="empresaparam",
            index=models.Index(fields=["valor"], name="idx_emp_par_valor"),
        ),
        migrations.AddIndex(
            model_name="empresaresolucion",
            index=models.Index(fields=["id_empresa"], name="idx_emp_res_empid"),
        ),
        migrations.AddIndex(
            model_name="empresaresolucion",
            index=models.Index(fields=["numero"], name="idx_emp_res_num"),
        ),
        migrations.AddIndex(
            model_name="empresaresolucion",
            index=models.Index(fields=["fecha"], name="idx_emp_res_fecha"),
        ),
        migrations.AddIndex(
            model_name="empresaresolucion",
            index=models.Index(fields=["descripcion"], name="idx_emp_res_desc"),
        ),
        migrations.AddIndex(
            model_name="empresatelefono",
            index=models.Index(
                fields=["id_empresa", "principal"], name="idx_empresa_telem_princ"
            ),
        ),
        migrations.AddIndex(
            model_name="grupo",
            index=models.Index(fields=["id_empresa"], name="idx_grupo_emp_id"),
        ),
        migrations.AddIndex(
            model_name="grupo",
            index=models.Index(fields=["asignable"], name="idx_grupo_asign"),
        ),

        # ---------------------------------------------------------------------
        # 5. Cambiamos los AutoField para usar nuestras columnas reales.
        # ---------------------------------------------------------------------
        migrations.AlterField(
            model_name="empresa",
            name="id",
            field=models.AutoField(primary_key=True, db_column="id_empresa", serialize=False),
        ),
        migrations.AlterField(
            model_name="empresaparam",
            name="id",
            field=models.AutoField(primary_key=True, db_column="id_empresa_param", serialize=False),
        ),
        migrations.AlterField(
            model_name="empresaresolucion",
            name="id",
            field=models.AutoField(primary_key=True, db_column="id_empresa_resolucion", serialize=False),
        ),
        migrations.AlterField(
            model_name="empresatelefono",
            name="id",
            field=models.AutoField(primary_key=True, db_column="id_empresa_telefono", serialize=False),
        ),
        migrations.AlterField(
            model_name="grupo",
            name="id",
            field=models.AutoField(primary_key=True, db_column="id_grupo", serialize=False),
        ),
    ]
