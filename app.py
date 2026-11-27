import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client

app = Flask(__name__)
# Clave secreta para manejar las sesiones del administrador de forma segura
app.secret_key = os.environ.get("SECRET_KEY", "jd_tech_secreto_seguro_2026")

# Inicialización de Supabase con las variables de entorno de Render (vía HTTP/443)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Las variables de entorno SUPABASE_URL y SUPABASE_KEY son obligatorias.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/estado', methods=['GET', 'POST'])
def estado():
    ordenes = []
    error = None
    if request.method == 'POST':
        busqueda = request.form.get('busqueda', '').strip()
        try:
            # Consulta segura a través de la API HTTP de Supabase
            response = supabase.table("ordenes").select("*").ilike("id", f"%{busqueda}%").execute()
            ordenes = response.data
            if not ordenes:
                error = "No se encontró ninguna orden con ese criterio."
        except Exception as e:
            error = f"Error al consultar la base de datos: {e}"
            
    return render_template('estado.html', ordenes=ordenes, error=error)

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        # Validación estricta con tu contraseña de siempre
        if usuario == "admin" and password == "301023":
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")
            
    return render_template('login_admin.html')

@app.route('/admin')
def admin_panel():
    # Verificación de seguridad de sesión activa
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    try:
        response = supabase.table("ordenes").select("*").execute()
        ordenes = response.data
    except Exception as e:
        ordenes = []
        flash(f"Error cargando órdenes: {e}", "danger")
        
    return render_template('admin.html', ordenes=ordenes)

@app.route('/crear-orden', methods=['POST'])
def crear_orden():
    try:
        nueva_orden = {
            "cliente": request.form.get('cliente'),
            "equipo": request.form.get('equipo'),
            "problema": request.form.get('problema'),
            "estado": "Recibido"
        }
        supabase.table("ordenes").insert(nueva_orden).execute()
        flash("Orden registrada con éxito", "success")
        return redirect(url_for('admin_panel') if session.get('admin') else url_for('index'))
    except Exception as e:
        return f"Error al registrar la orden: {e}", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
