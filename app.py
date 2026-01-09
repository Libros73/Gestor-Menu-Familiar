from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DE BASE DE DATOS ROBUSTA ---
# Detecta si estamos en Render (Nube) o en tu PC
uri = os.environ.get('DATABASE_URL')
if uri:
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recetas.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELO DE DATOS (LA TABLA) ---
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

# Crea la DB si no existe
with app.app_context():
    db.create_all()

# --- RUTAS ---

@app.route('/')
def home():
    return render_template('index.html')

# 1. LEER (GET)
@app.route('/api/recetas', methods=['GET'])
def obtener_recetas():
    lista_recetas = Receta.query.all()
    # Invertimos la lista [::-1] para que las nuevas salgan arriba
    return jsonify([receta.to_json() for receta in lista_recetas][::-1])

# 2. CREAR (POST)
@app.route('/api/recetas', methods=['POST'])
def agregar_receta():
    datos = request.json
    
    # Debug para ver en la terminal qué llega
    print("Recibido:", datos) 

    nueva_receta = Receta(
        nombre=datos['nombre'],
        calorias=datos['calorias'],
        apta_majo=datos.get('apta_majo', True) 
    )
    
    db.session.add(nueva_receta)
    db.session.commit()
    
    return jsonify({"mensaje": "Guardado exitoso", "status": "ok"})

# 3. BORRAR (DELETE) - ¡NUEVO!
@app.route('/api/recetas/<int:id>', methods=['DELETE'])
def eliminar_receta(id):
    receta = Receta.query.get(id)
    if not receta:
        return jsonify({"mensaje": "No encontrada"}), 404
    
    db.session.delete(receta)
    db.session.commit()
    return jsonify({"mensaje": "Eliminada correctamente"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)