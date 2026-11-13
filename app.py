from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro"

# Contraseña fija de administrador
ADMIN_PASSWORD = "301023"

# Base de datos simulada en memoria con registros de prueba
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
        "estado": "Ingresado",
        "fecha_reparacion": None,
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


# Ruta para consultar estado (Muestra TODOS los dispositivos asociados al número o cliente)
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


# Login Administrador
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


# Panel de Administración con Registro, Histórico y Filtros
@app.route("/admin", methods=["GET", "POST"])
def admin():
  if not session.get("admin_logged"):
    return redirect(url_for("login_admin"))

  hoy = datetime.now()

  if request.method == "POST":
    accion = request.form.get("accion")

    if accion == "crear":
      # Registro de un nuevo equipo desde el perfil de administrador
      try:
        costo_val = int(request.form.get("costo", 0))
      except ValueError:
        costo_val = 0

      try:
        precio_val = int(request.form.get("precio", 0))
      except ValueError:
        precio_val = 0

      nueva_orden = {
          "id": len(ordenes_taller) + 1,
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
      flash("Equipo registrado con éxito", "success")

    elif accion == "cambiar_estado":
      try:
        orden_id = int(request.form.get("orden_id"))
      except (TypeError, ValueError):
        orden_id = None

      nuevo_estado = request.form.get("nuevo_estado")
      for o in ordenes_taller:
        if o["id"] == orden_id:
          o["estado"] = nuevo_estado
          # Si el equipo pasa a Reparado o Entregado, se sella la fecha si no la tenía
          if nuevo_estado in ["Reparado", "Entregado"] and not o[
              "fecha_reparacion"
          ]:
            o["fecha_reparacion"] = hoy.strftime("%d/%m/%Y %H:%M")
          break
      flash("Estado actualizado correctamente", "success")

  # Filtro de estados por desplegable
  filtro_estado = request.args.get("filtro_estado", "Todos")

  activas = []
  historico = []

  for o in ordenes_taller:
    # 1. Cuenta regresiva de 30 días desde la fecha de reparación
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

    # 2. Archivo histórico automático (equipos entregados con más de 8 días de antigüedad)
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
