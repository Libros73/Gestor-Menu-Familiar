from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ### SEGURIDAD ###
# Necesitamos una "llave secreta" para firmar las cookies de sesión.
# En producción esto debe ser un secreto real, aquí usamos uno simple.
app.secret_key = 'clave_super_secreta_de_ingeniero'

# Configuración de Base de Datos
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///recetas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ### SEGURIDAD: CONFIGURAR EL GESTOR DE LOGIN ###
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Si no estás logueado, te manda aquí

# --- MODELOS (TABLAS) ---

# Tabla 1: Usuarios (NUEVA)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False) # Guardamos el HASH, no la clave real

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Tabla 2: Recetas (LA DE SIEMPRE)
class Receta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    calorias = db.Column(db.Integer, nullable=False)
    apta_majo = db.Column(db.Boolean, default=True)

    def to_json(self):
        return {
            "id": self.id, 
            "nombre": self.nombre, 
            "calorias": self.calorias, 
            "apta_majo": self.apta_majo
        }

# Función auxiliar para Flask-Login: Busca usuario por ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crea las tablas
with app.app_context():
    db.create_all()

# --- RUTAS DE ACCESO (LOGIN) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        clave = request.form['password']
        
        user = User.query.filter_by(username=usuario).first()
        
        # Verificamos si el usuario existe y la clave coincide con el hash
        if user and user.check_password(clave):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Usuario o contraseña incorrectos') # Mensaje de error
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS DE LA APP (PROTEGIDAS) ---

@app.route('/')
# <--- @login_required  # <--- EL CANDADO: Si no te logueas, no entras
def home():
    return render_template('index.html')

@app.route('/api/recetas', methods=['GET'])
# <--- @login_required # <--- CANDADO
def obtener_recetas():
    lista_recetas = Receta.query.all()
    return jsonify([receta.to_json() for receta in lista_recetas][::-1])

@app.route('/api/recetas', methods=['POST'])
@login_required # <--- CANDADO
def agregar_receta():
    datos = request.json
    nueva_receta = Receta(
        nombre=datos['nombre'],
        calorias=datos['calorias'],
        apta_majo=datos.get('apta_majo', True) 
    )
    db.session.add(nueva_receta)
    db.session.commit()
    return jsonify({"mensaje": "Guardado", "status": "ok"})

@app.route('/api/recetas/<int:id>', methods=['DELETE'])
@login_required # <--- CANDADO
def eliminar_receta(id):
    receta = Receta.query.get(id)
    if receta:
        db.session.delete(receta)
        db.session.commit()
    return jsonify({"mensaje": "Eliminada"})

# --- RUTA SECRETA PARA CREAR EL PRIMER USUARIO ---
# (Solo la usaremos una vez y luego la puedes borrar)
@app.route('/crear-admin')
def crear_admin():
    if User.query.filter_by(username='admin').first():
        return "El usuario admin ya existe."
    
    nuevo_user = User(username='admin')
    nuevo_user.set_password('1234') # <--- TU CONTRASEÑA INICIAL
    db.session.add(nuevo_user)
    db.session.commit()
    return "¡Usuario 'admin' creado con clave '1234'!"

if __name__ == '__main__':
    app.run(debug=True, port=5000)