# operadores/migrations/0005_remove_operador_idx_opr_emp_id_and_more.py
# -----------------------------------------------------------------------------
# Corrige definitivamente el error:
#     psycopg2.errors.DuplicateTable: relation "idx_opr_emp_id" already exists
#
# Idea clave → antes de recrear los índices eliminamos *cualquier* rastro
# del nombre, tanto en el esquema «dm_sistema» como en el search_path por
# defecto, de modo que AddIndex ya no colisione.
# -----------------------------------------------------------------------------

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configuracion", "0002_remove_empresamodulo_empresa_and_more"),
        ("coreempresas",
         "0002_remove_empresaparam_idx_empresa_param_empresa_id_and_more"),
        ("operadores", "0004_delete_sesionejecutivo"),
    ]

    operations = [
        # ------------------------------------------------------------------ #
        # 0.  **NUEVO:** limpia cualquier índice huérfano antes de todo.     #
        # ------------------------------------------------------------------ #
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    idxname text := 'idx_opr_emp_id';
                BEGIN
                    -- en el esquema específico
                    EXECUTE format(
                        'DROP INDEX IF EXISTS %I.%I',
                        'dm_sistema', idxname
                    );
                    -- y en search_path
                    EXECUTE format(
                        'DROP INDEX IF EXISTS %I',
                        idxname
                    );
                END$$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ------------------------------------------------------------------ #
        # 1.  Eliminar los índices “antiguos” declarados en 0001_initial.py   #
        # ------------------------------------------------------------------ #
        migrations.RemoveIndex(model_name="operador", name="idx_opr_emp_id"),
        migrations.RemoveIndex(model_name="operador", name="idx_opr_grp_id"),
        migrations.RemoveIndex(model_name="operadorbodega", name="idx_opbdg_bdg_id"),
        migrations.RemoveIndex(model_name="operadorbodega", name="idx_opbdg_emp_id"),
        migrations.RemoveIndex(model_name="operadorempresamodulo", name="idx_oem_opr_id"),
        migrations.RemoveIndex(model_name="operadorempresamodulo", name="idx_oem_em_id"),
        migrations.RemoveIndex(model_name="operadorempresamodulomenu", name="idx_oemm_opr_id"),
        migrations.RemoveIndex(model_name="operadorempresamodulomenu", name="idx_oemm_mm_id"),
        migrations.RemoveIndex(model_name="operadorpuntoventa", name="idx_opv_emp_id"),
        migrations.RemoveIndex(model_name="sesionactiva", name="idx_sact_sid"),
        migrations.RemoveIndex(model_name="sesionactiva", name="idx_sact_emp_id"),

        # ------------------------------------------------------------------ #
        # 2.  Renombrar columnas (idéntico a la versión previa)               #
        # ------------------------------------------------------------------ #
        migrations.RenameField("operador",              "operador_id",     "username"),
        migrations.RenameField("operadorbodega",        "bodega_id",       "id_bodega"),
        migrations.RenameField("operadorpuntoventa",    "punto_venta_id",  "id_punto_venta"),

        # ------------------------------------------------------------------ #
        # 3‑4.  Eliminamos UNIQUE constraints obsoletos                       #
        # ------------------------------------------------------------------ #
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_constraint
                         WHERE conrelid = '"dm_sistema"."operador"'::regclass
                           AND contype  = 'u'
                           AND conname  = 'operadores_operador_operador_id_empresa_id_uniq'
                    ) THEN
                        ALTER TABLE "dm_sistema"."operador"
                        DROP CONSTRAINT operadores_operador_operador_id_empresa_id_uniq;
                    ELSIF EXISTS (
                        SELECT 1 FROM pg_constraint
                         WHERE conrelid = '"dm_sistema"."operador"'::regclass
                           AND contype  = 'u'
                           AND conname  = 'operadores_operador_username_empresa_id_uniq'
                    ) THEN
                        ALTER TABLE "dm_sistema"."operador"
                        DROP CONSTRAINT operadores_operador_username_empresa_id_uniq;
                    END IF;
                END$$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_constraint
                         WHERE conrelid = '"dm_sistema"."operador_grupos"'::regclass
                           AND contype  = 'u'
                           AND conname  = 'operadores_operadorgr_operador_id_grupo_id_uniq'
                    ) THEN
                        ALTER TABLE "dm_sistema"."operador_grupos"
                        DROP CONSTRAINT operadores_operadorgr_operador_id_grupo_id_uniq;
                    END IF;
                END$$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ------------------------------------------------------------------ #
        # 5.  Limpieza exhaustiva de *todos* los índices potenciales          #
        # ------------------------------------------------------------------ #
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    idx text;
                BEGIN
                    FOREACH idx IN ARRAY ARRAY[
                        'idx_opr_emp_id','idx_opr_grp_id',
                        'idx_opbdg_bdg_id','idx_opbdg_emp_id','idx_opbdg_opr_id',
                        'idx_oem_opr_id','idx_oem_em_id',
                        'idx_oemm_opr_id','idx_oemm_mm_id',
                        'idx_opgr_opr_id','idx_opgr_grp_id',
                        'idx_opv_emp_id','idx_opv_pv_id','idx_opv_opr_id',
                        'idx_ses_emp_id','idx_ses_opr_id',
                        'idx_sact_sid','idx_sact_emp_id','idx_sact_opr_id'
                    ] LOOP
                        -- en «dm_sistema»
                        EXECUTE format(
                            'DROP INDEX IF EXISTS %I.%I',
                            'dm_sistema', idx
                        );
                        -- y también sin esquema
                        EXECUTE format(
                            'DROP INDEX IF EXISTS %I',
                            idx
                        );
                    END LOOP;
                END$$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ------------------------------------------------------------------ #
        # 6.  Eliminación de FK viejas (sin cambios)                          #
        # ------------------------------------------------------------------ #
        migrations.RemoveField("operadorbodega",            "empresa"),
        migrations.RemoveField("operadorbodega",            "operador"),
        migrations.RemoveField("operadorempresamodulo",     "empresa_modulo"),
        migrations.RemoveField("operadorempresamodulo",     "operador"),
        migrations.RemoveField("operadorempresamodulomenu", "empresa_modulo_menu"),
        migrations.RemoveField("operadorempresamodulomenu", "operador"),
        migrations.RemoveField("operadorpuntoventa",        "empresa"),
        migrations.RemoveField("operadorpuntoventa",        "operador"),
        migrations.RemoveField("sesion",                    "empresa"),
        migrations.RemoveField("sesion",                    "operador_id"),
        migrations.RemoveField("sesionactiva",              "empresa"),
        migrations.RemoveField("sesionactiva",              "operador_id"),
        migrations.RemoveField("sesionactiva",              "sesion_id"),

        # ------------------------------------------------------------------ #
        # 7.  Nuevas FK con prefijo id_… (idéntico a la versión previa)      #
        # ------------------------------------------------------------------ #
        migrations.AddField(
            "operador", "id_empresa",
            models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operadores",
                default=1,
            ),
        ),
        migrations.AddField(
            "operador", "id_grupo",
            models.ForeignKey(
                to="coreempresas.grupo",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operadores",
                null=True, blank=True,
            ),
        ),
        migrations.AddField(
            "operadorbodega", "id_empresa",
            models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_bodegas",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorbodega", "id_operador",
            models.ForeignKey(
                to="operadores.operador",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="bodegas",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorempresamodulo", "id_empresa_modulo",
            models.ForeignKey(
                to="configuracion.empresamodulo",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorempresamodulo", "id_operador",
            models.ForeignKey(
                to="operadores.operador",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorempresamodulomenu", "id_empresa_modulo_menu",
            models.ForeignKey(
                to="configuracion.empresamodulomenu",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos_menus",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorempresamodulomenu", "id_operador",
            models.ForeignKey(
                to="operadores.operador",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_empresa_modulos_menus",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorgrupo", "id_grupo",
            models.ForeignKey(
                to="coreempresas.grupo",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operadores_grupo",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorgrupo", "id_operador",
            models.ForeignKey(
                to="operadores.operador",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operadores_grupo",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorpuntoventa", "id_empresa",
            models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_puntos_ventas",
                default=1,
            ),
        ),
        migrations.AddField(
            "operadorpuntoventa", "id_operador",
            models.ForeignKey(
                to="operadores.operador",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="operador_puntos_venta",
                default=1,
            ),
        ),
        migrations.AddField(
            "sesion", "id_empresa",
            models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=django.db.models.deletion.RESTRICT,
                null=True, blank=True,
            ),
        ),
        migrations.AddField(
            "sesion", "id_operador",
            models.ForeignKey(
                to="operadores.operador",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="sesion",
                default=1,
            ),
        ),
        migrations.AddField(
            "sesionactiva", "id_empresa",
            models.ForeignKey(
                to="coreempresas.empresa",
                on_delete=django.db.models.deletion.RESTRICT,
                null=True, blank=True,
            ),
        ),
        migrations.AddField(
            "sesionactiva", "id_operador",
            models.ForeignKey(
                to="operadores.operador",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="sesion_activa",
                default=1,
            ),
        ),
        migrations.AddField(
            "sesionactiva", "id_sesion",
            models.ForeignKey(
                to="operadores.sesion",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="sesion_activa",
                default=1,
            ),
        ),

        # ------------------------------------------------------------------ #
        # 8.  Ajuste de AutoField → columnas reales                           #
        # ------------------------------------------------------------------ #
        migrations.AlterField("operador",                 "id",
                              models.AutoField(primary_key=True, db_column="id_operador")),
        migrations.AlterField("operadorbodega",           "id",
                              models.AutoField(primary_key=True, db_column="id_operador_bodega")),
        migrations.AlterField("operadorempresamodulo",    "id",
                              models.AutoField(primary_key=True, db_column="id_operador_empresa_modulo")),
        migrations.AlterField("operadorempresamodulomenu","id",
                              models.AutoField(primary_key=True, db_column="id_operador_empresa_modulo_menu")),
        migrations.AlterField("operadorgrupo",            "id",
                              models.AutoField(primary_key=True, db_column="id_operador_grupo")),
        migrations.AlterField("operadorpuntoventa",       "id",
                              models.AutoField(primary_key=True, db_column="id_operador_punto_venta")),
        migrations.AlterField("sesion",                   "id",
                              models.AutoField(primary_key=True, db_column="id_sesion")),
        migrations.AlterField("sesionactiva",             "id",
                              models.AutoField(primary_key=True, db_column="id_sesion_activa")),

        # ------------------------------------------------------------------ #
        # 9.  Re‑crear los índices con los nombres definitivos               #
        # ------------------------------------------------------------------ #
        migrations.AddIndex("operador",
            models.Index(fields=["id_empresa"], name="idx_opr_emp_id")),
        migrations.AddIndex("operador",
            models.Index(fields=["id_grupo"],   name="idx_opr_grp_id")),
        migrations.AddIndex("operadorbodega",
            models.Index(fields=["id_bodega"],  name="idx_opbdg_bdg_id")),
        migrations.AddIndex("operadorbodega",
            models.Index(fields=["id_empresa"], name="idx_opbdg_emp_id")),
        migrations.AddIndex("operadorbodega",
            models.Index(fields=["id_operador"], name="idx_opbdg_opr_id")),
        migrations.AddIndex("operadorempresamodulo",
            models.Index(fields=["id_operador"],        name="idx_oem_opr_id")),
        migrations.AddIndex("operadorempresamodulo",
            models.Index(fields=["id_empresa_modulo"],  name="idx_oem_em_id")),
        migrations.AddIndex("operadorempresamodulomenu",
            models.Index(fields=["id_operador"],            name="idx_oemm_opr_id")),
        migrations.AddIndex("operadorempresamodulomenu",
            models.Index(fields=["id_empresa_modulo_menu"], name="idx_oemm_mm_id")),
        migrations.AddIndex("operadorgrupo",
            models.Index(fields=["id_operador"], name="idx_opgr_opr_id")),
        migrations.AddIndex("operadorgrupo",
            models.Index(fields=["id_grupo"],    name="idx_opgr_grp_id")),
        migrations.AddIndex("operadorpuntoventa",
            models.Index(fields=["id_empresa"],     name="idx_opv_emp_id")),
        migrations.AddIndex("operadorpuntoventa",
            models.Index(fields=["id_punto_venta"], name="idx_opv_pv_id")),
        migrations.AddIndex("operadorpuntoventa",
            models.Index(fields=["id_operador"],    name="idx_opv_opr_id")),
        migrations.AddIndex("sesion",
            models.Index(fields=["id_empresa"],  name="idx_ses_emp_id")),
        migrations.AddIndex("sesion",
            models.Index(fields=["id_operador"], name="idx_ses_opr_id")),
        migrations.AddIndex("sesionactiva",
            models.Index(fields=["id_sesion"],   name="idx_sact_sid")),
        migrations.AddIndex("sesionactiva",
            models.Index(fields=["id_empresa"],  name="idx_sact_emp_id")),
        migrations.AddIndex("sesionactiva",
            models.Index(fields=["id_operador"], name="idx_sact_opr_id")),
    ]
