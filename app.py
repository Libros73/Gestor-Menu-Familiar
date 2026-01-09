from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'clave_super_secreta_de_ingeniero'

# --- CONFIGURACIÓN HÍBRIDA (NUBE / LOCAL) ---
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///recetas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- CONFIGURACIÓN DE LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELOS (TABLAS) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- RUTAS DE LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        clave = request.form['password']
        user = User.query.filter_by(username=usuario).first()
        if user and user.check_password(clave):
            login_user(user)
            return "<html><body><script>window.location.href='/';</script></body></html>"
        else:
            return "Usuario o clave incorrectos <a href='/login'>Volver</a>"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "<html><body><script>window.location.href='/';</script></body></html>"

@app.route('/crear-admin')
def crear_admin():
    if User.query.filter_by(username='admin').first():
        return "El usuario admin ya existe."
    nuevo_user = User(username='admin')
    nuevo_user.set_password('1234')
    db.session.add(nuevo_user)
    db.session.commit()
    return "Usuario admin creado."

# --- RUTAS DE LA APP ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/recetas', methods=['GET'])
def obtener_recetas():
    lista = Receta.query.all()
    # Devolvemos la lista invertida para ver las nuevas primero
    return jsonify([r.to_json() for r in lista][::-1])

@app.route('/api/recetas', methods=['POST'])
@login_required
def agregar_receta():
    d = request.json
    nueva = Receta(nombre=d['nombre'], calorias=d['calorias'], apta_majo=d.get('apta_majo', True))
    db.session.add(nueva)
    db.session.commit()
    return jsonify({"mensaje": "Guardado"})

# RUTA NUEVA: ACTUALIZAR (PUT)
@app.route('/api/recetas/<int:id>', methods=['PUT'])
@login_required
def actualizar_receta(id):
    receta = Receta.query.get(id)
    if not receta: return jsonify({"mensaje": "No existe"}), 404
    
    d = request.json
    receta.nombre = d['nombre']
    receta.calorias = d['calorias']
    receta.apta_majo = d.get('apta_majo', True)
    
    db.session.commit()
    return jsonify({"mensaje": "Actualizado"})

@app.route('/api/recetas/<int:id>', methods=['DELETE'])
@login_required
def eliminar_receta(id):
    r = Receta.query.get(id)
    if r:
        db.session.delete(r)
        db.session.commit()
    return jsonify({"mensaje": "Eliminado"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)