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
    raise ValueError("Las variables de entorno SUPABASE_URL y SUPABASE_KEY son obligatorias en Render.")

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
            # Consulta limpia a través de la API HTTP de Supabase
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
        password = request.form.get('password')
        
        # Validación estricta únicamente con la contraseña establecida (301023)
        if password == "301023":
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Contraseña incorrecta", "danger")
            
    return render_template('login_admin.html')

@app.route('/admin', methods=['GET'])
def admin_panel():
    # Seguridad: si no hay sesión activa de administrador, redirige al login
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    ordenes = []
    try:
        response = supabase.table("ordenes").select("*").execute()
        ordenes = response.data
    except Exception as e:
        flash(f"Error cargando las órdenes: {e}", "danger")
        
    return render_template('admin.html', ordenes=ordenes)

@app.route('/crear-orden', methods=['POST'])
def crear_orden():
    try:
        # Captura de datos respetando los nombres exactos de las columnas en Supabase
        nueva_orden = {
            "cliente": request.form.get('cliente'),
            "equipo": request.form.get('equipo'),
            "problema": request.form.get('problema'),
            "estado": "Recibido"
        }
        
        # Inserción en la tabla 'ordenes' mediante Supabase HTTP
        supabase.table("ordenes").insert(nueva_orden).execute()
        flash("¡Orden registrada con éxito!", "success")
        
        # Redirección inteligente según el rol activo
        if session.get('admin'):
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error al registrar la orden en la base de datos: {e}", 500

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
