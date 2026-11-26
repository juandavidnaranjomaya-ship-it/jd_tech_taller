from datetime import datetime
from io import BytesIO
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
import openpyxl
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro"
ADMIN_PASSWORD = "301023"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ordenes (
                id SERIAL PRIMARY KEY,
                cliente TEXT,
                cedula TEXT,
                telefono TEXT,
                equipo TEXT,
                imei TEXT,
                problema TEXT,
                fecha_ingreso TEXT,
                costo INTEGER,
                precio INTEGER,
                estado TEXT,
                fecha_reparacion TEXT,
                foto_recepcion TEXT,
                autorizacion_datos INTEGER
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

init_db()

servicios_jd_tech = [
    {
        "nombre": "Cambio de Pantalla",
        "descripcion": "Displays originales y genéricos con garantía.",
        "precio": "80.000+",
    },
    {
        "nombre": "Reparación de Pin de Carga",
        "descripcion": "Soldadura de precisión y limpieza de puertos.",
        "precio": "35.000+",
    },
    {
        "nombre": "Diagnóstico y Software",
        "descripcion": "Recuperación de sistemas, cuentas y desvirus.",
        "precio": "25.000+",
    },
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        hoy = datetime.now()
        cliente = request.form.get("cliente", "").strip()
        cedula = request.form.get("cedula", "").strip()
        telefono = request.form.get("telefono", "").strip()
        equipo = request.form.get("equipo", "").strip()
        autorizacion = 1 if request.form.get("autorizacion") == "on" else 0
        if not autorizacion:
            flash(
                "Debe autorizar el tratamiento de datos personales para continuar.",
                "error",
            )
            return redirect(url_for("index"))
        
        falla_sel = request.form.get("problema_select", "")
        falla_otra = request.form.get("problema_otro", "").strip()
        problema_final = (
            falla_otra if falla_sel == "Otra" and falla_otra else falla_sel
        )
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ordenes (cliente, cedula, telefono, equipo, imei, problema, fecha_ingreso, costo, precio, estado, fecha_reparacion, foto_recepcion, autorizacion_datos)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cliente,
                cedula,
                telefono,
                equipo,
                "",
                problema_final,
                hoy.strftime("%d/%m/%Y"),
                0,
                0,
                "Ingresado",
                None,
                None,
                autorizacion,
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash(
            "Solicitud enviada con éxito. Ya puede consultar su estado en línea.",
            "success",
        )
        return redirect(url_for("estado"))
    return render_template("index.html", servicios=servicios_jd_tech)

@app.route("/estado", methods=["GET", "POST"])
def estado():
    resultados = []
    busqueda = ""
    hoy = datetime.now()
    if request.method == "POST":
        busqueda = request.form.get("telefono", "").strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ordenes")
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        for row in filas:
            o = dict(row)
            if (
                o["telefono"] == busqueda
                or busqueda.lower() in o["cliente"].lower()
            ):
                ocultar = False
                if o["estado"] == "Entregado" and o["fecha_reparacion"]:
                    try:
                        f_ent = datetime.strptime(
                            o["fecha_reparacion"].split()[0], "%d/%m/%Y"
                        )
                        if (hoy - f_ent).days > 8:
                            ocultar = True
                    except Exception:
                        pass
                if not ocultar:
                    resultados.append(o)
    return render_template(
        "estado.html", resultados=resultados, busqueda=busqueda
    )

@app.route("/login-admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged"] = True
            return redirect(url_for("admin"))
        else:
            flash("Contraseña incorrecta", "error")
    return render_template("login_admin.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged", None)
    return redirect(url_for("login_admin"))

@app.route("/admin/exportar-excel")
def exportar_excel():
    if not session.get("admin_logged"):
        return redirect(url_for("login_admin"))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ordenes")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Historial JD TECH"
    ws.append([
        "ID",
        "Cliente",
        "Cédula",
        "Teléfono",
        "Equipo",
        "IMEI",
        "Problema",
        "Fecha Ingreso",
        "Costo Repuesto ($)",
        "Precio Cobrado ($)",
        "Ganancia Neta ($)",
        "Estado",
        "Fecha Reparación",
        "Autorizado Ley 1581",
    ])
    for row in filas:
        o = dict(row)
        costo = int(o.get("costo", 0) or 0)
        precio = int(o.get("precio", 0) or 0)
        ganancia = precio - costo
        ws.append([
            o["id"],
            o["cliente"],
            o["cedula"] or "N/A",
            o["telefono"],
            o["equipo"],
            o["imei"] or "No registrado",
            o["problema"],
            o["fecha_ingreso"],
            costo,
            precio,
            ganancia,
            o["estado"],
            o["fecha_reparacion"] or "Pendiente",
            "Sí" if o["autorizacion_datos"] else "No",
        ])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        mimetype=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        as_attachment=True,
        download_name=f"JD_TECH_Historico_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
    )

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin_logged"):
        return redirect(url_for("login_admin"))
    
    hoy = datetime.now()
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == "POST":
        accion = request.form.get("accion")
        if accion == "guardar":
            orden_id = request.form.get("orden_id", "").strip()
            cliente = request.form.get("cliente", "").strip()
            cedula = request.form.get("cedula", "").strip()
            telefono = request.form.get("telefono", "").strip()
            equipo = request.form.get("equipo", "").strip()
            imei = request.form.get("imei", "").strip()
            falla_sel = request.form.get("problema_select", "")
            falla_otra = request.form.get("problema_otro", "").strip()
            problema = (
                falla_otra if falla_sel == "Otra" and falla_otra else falla_sel
            )
            try:
                costo_val = int(request.form.get("costo") or 0)
            except ValueError:
                costo_val = 0
            try:
                precio_val = int(request.form.get("precio") or 0)
            except ValueError:
                precio_val = 0
            
            foto_url = None
            if "foto" in request.files:
                file = request.files["foto"]
                if file and file.filename != "":
                    file_bytes = file.read()
                    file_name = f"recibo_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                    try:
                        supabase.storage.from_("recibos").upload(
                            file_name, file_bytes, {"content-type": file.content_type}
                        )
                        foto_url = supabase.storage.from_("recibos").get_public_url(file_name)
                    except Exception as e:
                        print(f"Error al subir imagen a Supabase: {e}")
            
            if orden_id:
                if foto_url:
                    cursor.execute(
                        """
                        UPDATE ordenes SET 
                            cliente = %s, cedula = %s, telefono = %s, equipo = %s, imei = %s, 
                            problema = COALESCE(NULLIF(%s, ''), problema), costo = %s, precio = %s,
                            foto_recepcion = %s
                        WHERE id = %s
                        """,
                        (cliente, cedula, telefono, equipo, imei, problema, costo_val, precio_val, foto_url, orden_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE ordenes SET 
                            cliente = %s, cedula = %s, telefono = %s, equipo = %s, imei = %s, 
                            problema = COALESCE(NULLIF(%s, ''), problema), costo = %s, precio = %s
                        WHERE id = %s
                        """,
                        (cliente, cedula, telefono, equipo, imei, problema, costo_val, precio_val, orden_id),
                    )
                conn.commit()
                flash("Orden actualizada correctamente", "success")
            else:
                if cliente and telefono and equipo:
                    cursor.execute(
                        """
                        INSERT INTO ordenes (cliente, cedula, telefono, equipo, imei, problema, fecha_ingreso, costo, precio, estado, fecha_reparacion, foto_recepcion, autorizacion_datos)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            cliente,
                            cedula,
                            telefono,
                            equipo,
                            imei,
                            problema or "Revisión general",
                            hoy.strftime("%d/%m/%Y"),
                            costo_val,
                            precio_val,
                            "Ingresado",
                            None,
                            foto_url,
                            1,
                        ),
                    )
                    conn.commit()
                    flash("Nueva orden agregada con éxito", "success")
        elif accion == "cambiar_estado":
            orden_id = request.form.get("orden_id")
            nuevo_estado = request.form.get("nuevo_estado")
            cursor.execute(
                "SELECT estado, fecha_reparacion FROM ordenes WHERE id = %s",
                (orden_id,),
            )
            row = cursor.fetchone()
            if row:
                f_rep = row["fecha_reparacion"]
                if nuevo_estado in ["Reparado", "Entregado"] and not f_rep:
                    f_rep = hoy.strftime("%d/%m/%Y %H:%M")
                cursor.execute(
                    "UPDATE ordenes SET estado = %s, fecha_reparacion = %s WHERE id = %s",
                    (nuevo_estado, f_rep, orden_id),
                )
                conn.commit()
                flash("Estado actualizado correctamente", "success")
        elif accion == "eliminar":
            try:
                orden_id = int(request.form.get("orden_id"))
                cursor.execute("DELETE FROM ordenes WHERE id = %s", (orden_id,))
                conn.commit()
                flash("Orden eliminada correctamente", "success")
            except Exception:
                flash("Error al eliminar la orden", "error")
        elif accion == "actualizar_masivo":
            for key, value in request.form.items():
                if key.startswith("estado_"):
                    try:
                        orden_id = int(key.split("_")[1])
                        cursor.execute(
                            "SELECT estado, fecha_reparacion FROM ordenes WHERE id = %s",
                            (orden_id,),
                        )
                        row = cursor.fetchone()
                        if row and row["estado"] != value:
                            f_rep = row["fecha_reparacion"]
                            if value in ["Reparado", "Entregado"] and not f_rep:
                                f_rep = hoy.strftime("%d/%m/%Y %H:%M")
                            cursor.execute(
                                "UPDATE ordenes SET estado = %s, fecha_reparacion = %s WHERE id = %s",
                                (value, f_rep, orden_id),
                            )
                            conn.commit()
                    except Exception:
                        pass
            flash(
                "Se guardaron los cambios de todas las órdenes correctamente",
                "success",
            )
            
    filtro_estado = request.args.get("filtro_estado", "Todos")
    cursor.execute("SELECT * FROM ordenes")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    
    activas = []
    historico = []
    for row in filas:
        o = dict(row)
        dias_restantes = None
        if o["fecha_reparacion"] and o["estado"] in ["Reparado", "Entregado"]:
            try:
                f_rep = datetime.strptime(o["fecha_reparacion"].split()[0], "%d/%m/%Y")
                dias_restantes = max(0, 30 - (hoy - f_rep).days)
            except Exception:
                pass
        o["dias_restantes"] = dias_restantes
        
        es_historico = False
        if o["estado"] == "Entregado" and o["fecha_reparacion"]:
            try:
                f_ent = datetime.strptime(
                    o["fecha_reparacion"].split()[0], "%d/%m/%Y"
                )
                if (hoy - f_ent).days > 8:
                    es_historico = True
            except Exception:
                pass
        if es_historico:
            historico.append(o)
        else:
            if filtro_estado == "Todos" or o["estado"] == filtro_estado:
                activas.append(o)
                
    return render_template(
        "admin.html",
        ordenes=activas,
        historico=historico,
        filtro_estado=filtro_estado,
    )

if __name__ == "__main__":
    app.run(debug=True, port=10000)
