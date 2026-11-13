from datetime import datetime
from io import BytesIO
from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for
import openpyxl

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro"

ADMIN_PASSWORD = "301023"

# Base de datos simulada en memoria
ordenes_taller = [
    {
        "id": 1,
        "cliente": "Carlos Pérez",
        "telefono": "3001234567",
        "equipo": "iPhone 11",
        "problema": "Cambio de pantalla",
        "fecha_ingreso": "10/11/2026",
        "costo": 50000,
        "precio": 120000,
        "estado": "Reparado",
        "fecha_reparacion": "13/11/2026 06:28",
    },
    {
        "id": 2,
        "cliente": "Carlos Pérez",
        "telefono": "3001234567",
        "equipo": "Samsung Galaxy A52",
        "problema": "Pin de carga roto",
        "fecha_ingreso": "11/11/2026",
        "costo": 25000,
        "precio": 60000,
        "estado": "Reparado",
        "fecha_reparacion": "12/11/2026 14:30",
    },
]

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


@app.route("/")
def index():
  return render_template("index.html", servicios=servicios_jd_tech)


@app.route("/estado", methods=["GET", "POST"])
def estado():
  resultados = []
  busqueda = ""
  if request.method == "POST":
    busqueda = request.form.get("telefono", "").strip()
    resultados = [
        o for o in ordenes_taller if o["telefono"] == busqueda
        or busqueda.lower() in o["cliente"].lower()
    ]
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


# Ruta para descargar el Histórico en Excel (.xlsx)
@app.route("/admin/exportar-excel")
def exportar_excel():
  if not session.get("admin_logged"):
    return redirect(url_for("login_admin"))

  wb = openpyxl.Workbook()
  ws = wb.active
  ws.title = "Historial JD TECH"

  # Encabezados
  ws.append([
      "ID",
      "Cliente",
      "Teléfono",
      "Equipo",
      "Problema",
      "Fecha Ingreso",
      "Costo Repuesto",
      "Precio Cliente",
      "Estado",
      "Fecha Reparación",
  ])

  # Datos
  for o in ordenes_taller:
    ws.append([
        o["id"],
        o["cliente"],
        o["telefono"],
        o["equipo"],
        o["problema"],
        o["fecha_ingreso"],
        o["costo"],
        o["precio"],
        o["estado"],
        o["fecha_reparacion"] or "Pendiente",
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

  if request.method == "POST":
    accion = request.form.get("accion")

    # 1. Crear o Actualizar equipo desde el formulario superior
    if accion == "guardar":
      try:
        orden_id = request.form.get("orden_id")
        costo_val = int(request.form.get("costo", 0) or 0)
        precio_val = int(request.form.get("precio", 0) or 0)

        if orden_id:  # Si tiene ID, es una actualización de datos / costos
          for o in ordenes_taller:
            if o["id"] == int(orden_id):
              o["cliente"] = request.form.get("cliente", "").strip()
              o["telefono"] = request.form.get("telefono", "").strip()
              o["equipo"] = request.form.get("equipo", "").strip()
              o["problema"] = request.form.get("problema", "").strip()
              o["costo"] = costo_val
              o["precio"] = precio_val
              flash("Orden actualizada con éxito", "success")
              break
        else:  # Nuevo registro
          nuevo_id = (
              max([o["id"] for o in ordenes_taller], default=0) + 1
          )
          nueva_orden = {
              "id": nuevo_id,
              "cliente": request.form.get("cliente", "").strip(),
              "telefono": request.form.get("telefono", "").strip(),
              "equipo": request.form.get("equipo", "").strip(),
              "problema": request.form.get("problema", "").strip(),
              "fecha_ingreso": hoy.strftime("%d/%m/%Y"),
              "costo": costo_val,
              "precio": precio_val,
              "estado": "Ingresado",
              "fecha_reparacion": None,
          }
          ordenes_taller.append(nueva_orden)
          flash("Nuevo equipo registrado con éxito", "success")
      except Exception as e:
        flash(f"Error al procesar orden: {str(e)}", "error")

    # 2. Cambiar estado individual
    elif accion == "cambiar_estado":
      try:
        orden_id = int(request.form.get("orden_id"))
        nuevo_estado = request.form.get("nuevo_estado")
        for o in ordenes_taller:
          if o["id"] == orden_id:
            o["estado"] = nuevo_estado
            if nuevo_estado in ["Reparado", "Entregado"] and not o[
                "fecha_reparacion"
            ]:
              o["fecha_reparacion"] = hoy.strftime("%d/%m/%Y %H:%M")
            break
        flash("Estado actualizado correctamente", "success")
      except Exception:
        flash("Error al actualizar estado", "error")

  filtro_estado = request.args.get("filtro_estado", "Todos")
  activas = []
  historico = []

  for o in ordenes_taller:
    # Cuenta regresiva de 30 días
    dias_restantes = None
    if o["fecha_reparacion"] and o["estado"] in ["Reparado", "Entregado"]:
      try:
        f_rep_str = o["fecha_reparacion"].split()[0]
        f_rep = datetime.strptime(f_rep_str, "%d/%m/%Y")
        dias_transcurridos = (hoy - f_rep).days
        dias_restantes = max(0, 30 - dias_transcurridos)
      except Exception:
        dias_restantes = None
    o["dias_restantes"] = dias_restantes

    # Archivo histórico automático (> 8 días de entregado)
    es_historico = False
    if o["estado"] == "Entregado" and o["fecha_reparacion"]:
      try:
        f_ent_str = o["fecha_reparacion"].split()[0]
        f_ent = datetime.strptime(f_ent_str, "%d/%m/%Y")
        if (hoy - f_ent).days > 8:
          es_historico = True
      except Exception:
        es_historico = False

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
