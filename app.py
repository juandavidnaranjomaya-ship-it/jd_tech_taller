from datetime import datetime
from io import BytesIO
from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for
import openpyxl

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro"

ADMIN_PASSWORD = "301023"

# Base de datos en memoria
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
    }
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


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    hoy = datetime.now()
    falla_sel = request.form.get("problema_select", "")
    falla_otra = request.form.get("problema_otro", "").strip()
    problema_final = (
        falla_otra if falla_sel == "Otra" and falla_otra else falla_sel
    )

    nuevo_id = max([o["id"] for o in ordenes_taller], default=0) + 1
    nueva_orden = {
        "id": nuevo_id,
        "cliente": request.form.get("cliente", "").strip(),
        "telefono": request.form.get("telefono", "").strip(),
        "equipo": request.form.get("equipo", "").strip(),
        "problema": problema_final,
        "fecha_ingreso": hoy.strftime("%d/%m/%Y"),
        "costo": 0,
        "precio": 0,
        "estado": "Ingresado",
        "fecha_reparacion": None,
    }
    ordenes_taller.append(nueva_orden)
    flash("¡Solicitud enviada con éxito! Ya puedes consultar tu estado.", "success")
    return redirect(url_for("estado"))

  return render_template("index.html", servicios=servicios_jd_tech)


@app.route("/estado", methods=["GET", "POST"])
def estado():
  resultados = []
  busqueda = ""
  hoy = datetime.now()

  if request.method == "POST":
    busqueda = request.form.get("telefono", "").strip()
    for o in ordenes_taller:
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

  wb = openpyxl.Workbook()
  ws = wb.active
  ws.title = "Historial JD TECH"

  ws.append([
      "ID",
      "Cliente",
      "Teléfono",
      "Equipo",
      "Problema",
      "Fecha Ingreso",
      "Costo Repuesto ($)",
      "Precio Cobrado ($)",
      "Ganancia Neta ($)",
      "Estado",
      "Fecha Reparación",
  ])

  for o in ordenes_taller:
    costo = int(o.get("costo", 0) or 0)
    precio = int(o.get("precio", 0) or 0)
    ganancia = precio - costo

    ws.append([
        o["id"],
        o["cliente"],
        o["telefono"],
        o["equipo"],
        o["problema"],
        o["fecha_ingreso"],
        costo,
        precio,
        ganancia,
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
      orden_id = request.form.get("orden_id", "").strip()
      cliente = request.form.get("cliente", "").strip()
      telefono = request.form.get("telefono", "").strip()
      equipo = request.form.get("equipo", "").strip()

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

      if orden_id:
        for o in ordenes_taller:
          if str(o["id"]) == orden_id:
            o["cliente"] = cliente
            o["telefono"] = telefono
            o["equipo"] = equipo
            if problema:
              o["problema"] = problema
            o["costo"] = costo_val
            o["precio"] = precio_val
            flash("Orden actualizada correctamente", "success")
            break
      else:
        if cliente and telefono and equipo:
          nuevo_id = max([o["id"] for o in ordenes_taller], default=0) + 1
          nueva_orden = {
              "id": nuevo_id,
              "cliente": cliente,
              "telefono": telefono,
              "equipo": equipo,
              "problema": problema or "Revisión general",
              "fecha_ingreso": hoy.strftime("%d/%m/%Y"),
              "costo": costo_val,
              "precio": precio_val,
              "estado": "Ingresado",
              "fecha_reparacion": None,
          }
          ordenes_taller.append(nueva_orden)
          flash("Nueva orden agregada con éxito", "success")

    # 2. Cambiar estado individual
    elif accion == "cambiar_estado":
      orden_id = request.form.get("orden_id")
      nuevo_estado = request.form.get("nuevo_estado")
      for o in ordenes_taller:
        if str(o["id"]) == str(orden_id):
          o["estado"] = nuevo_estado
          if nuevo_estado in ["Reparado", "Entregado"] and not o[
              "fecha_reparacion"
          ]:
            o["fecha_reparacion"] = hoy.strftime("%d/%m/%Y %H:%M")
          break
      flash("Estado actualizado correctamente", "success")

    # 3. Actualizar MASIVO todos los cambios individuales a la vez
    elif accion == "actualizar_masivo":
      actualizados = 0
      for key, value in request.form.items():
        if key.startswith("estado_"):
          try:
            orden_id = int(key.split("_")[1])
            for o in ordenes_taller:
              if o["id"] == orden_id:
                if o["estado"] != value:
                  o["estado"] = value
                  if value in ["Reparado", "Entregado"] and not o[
                      "fecha_reparacion"
                  ]:
                    o["fecha_reparacion"] = hoy.strftime("%d/%m/%Y %H:%M")
                  actualizados += 1
                break
          except Exception:
            pass
      flash(
          f"¡Se guardaron los cambios de todas las órdenes correctamente!",
          "success",
      )

  filtro_estado = request.args.get("filtro_estado", "Todos")
  activas = []
  historico = []

  for o in ordenes_taller:
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
        f_ent = datetime.strptime(o["fecha_entregado"].split()[0], "%d/%m/%Y")
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
