from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'jd_tech_seguridad_interna_secreta'

# Contraseña exclusiva de administrador
ADMIN_PASSWORD = '301023'

# Base de datos simulada en memoria para el taller
reparaciones = [
    {"id": 1, "cliente": "Carlos Pérez", "dispositivo": "Samsung Galaxy A52", "falla": "Cambio de módulos de pantalla", "estado": "En diagnóstico", "contacto": "3101234567"},
    {"id": 2, "cliente": "María Rodríguez", "dispositivo": "iPhone 11", "falla": "Reemplazo de baterías", "estado": "Reparado", "contacto": "3209876543"}
]

servicios_jd_tech = [
    {"nombre": "Cambio de módulos de pantalla", "descripcion": "Sustitución de displays completos con garantía y máxima precisión."},
    {"nombre": "Reemplazo de baterías", "descripcion": "Instalación de baterías óptimas para recuperar la autonomía del equipo."},
    {"nombre": "Reparación de puertos de carga", "descripcion": "Solución a fallos de energía, pines zafados o falsos contactos."},
    {"nombre": "Mantenimiento y limpieza técnica", "descripcion": "Limpieza profunda de componentes internos y prevención de sulfatación."},
    {"nombre": "Diagnóstico de fallas funcionales", "descripcion": "Análisis exhaustivo en placa y sistemas operativos."}
]

@app.route('/')
def index():
    return render_template('index.html', servicios=servicios_jd_tech)

@app.route('/recepcion', methods=['POST'])
def recepcion():
    cliente = request.form.get('cliente')
    dispositivo = request.form.get('dispositivo')
    falla = request.form.get('falla')
    contacto = request.form.get('contacto')
    
    if cliente and dispositivo and falla:
        nuevo_id = len(reparaciones) + 1
        reparaciones.append({
            "id": nuevo_id,
            "cliente": cliente,
            "dispositivo": dispositivo,
            "falla": falla,
            "estado": "Recibido / En cola",
            "contacto": contacto
        })
        flash(f'¡Equipo registrado correctamente! Número de orden asignado: #{nuevo_id}', 'success')
    else:
        flash('Por favor, complete todos los campos obligatorios.', 'danger')
    return redirect(url_for('index'))

@app.route('/estado', methods=['GET', 'POST'])
def estado():
    resultado = None
    busqueda = None
    if request.method == 'POST':
        busqueda = request.form.get('busqueda', '').strip()
        for rep in reparaciones:
            if str(rep['id']) == busqueda or rep['cliente'].lower() == busqueda.lower():
                resultado = rep
                break
    return render_template('estado.html', resultado=resultado, busqueda=busqueda)

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged'] = True
            return redirect(url_for('admin'))
        else:
            flash('Contraseña incorrecta. Intente de nuevo.', 'danger')
    return render_template('login_admin.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged', None)
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('login_admin'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged'):
        return redirect(url_for('login_admin'))
    return render_template('admin.html', reparaciones=reparaciones)

@app.route('/actualizar_estado/<int:id_equipo>', methods=['POST'])
def actualizar_estado(id_equipo):
    if not session.get('admin_logged'):
        return redirect(url_for('login_admin'))
    
    nuevo_estado = request.form.get('nuevo_estado')
    for rep in reparaciones:
        if rep['id'] == id_equipo:
            rep['estado'] = nuevo_estado
            flash(f'Estado de la orden #{id_equipo} actualizado a: {nuevo_estado}', 'success')
            break
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
