from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# CONFIGURACIÓN DE LA BASE DE DATOS
# Le decimos: "Usa un archivo local llamado recetas.db"
# (Más adelante, cambiaremos esta sola línea para conectar con la Nube)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recetas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# INICIALIZAMOS EL ORM (El Traductor)
db = SQLAlchemy(app)

# --- DEFINICIÓN DEL MODELO (La Tabla) ---
# Esto crea una tabla con columnas específicas. Estructura rígida = Ingeniería.
class Receta(db.Model):
    id = db.Column(db.Integer, primary_key=True)       # Identificador único (1, 2, 3...)
    nombre = db.Column(db.String(100), nullable=False) # Texto de máx 100 caracteres
    calorias = db.Column(db.Integer, nullable=False)   # Número entero
    apta_majo = db.Column(db.Boolean, default=True)    # Verdadero/Falso

    # Esta función ayuda a convertir la fila de la DB a Diccionario (JSON)
    def to_json(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "calorias": self.calorias,
            "apta_majo": self.apta_majo
        }

# --- CREAR LA BASE DE DATOS SI NO EXISTE ---
with app.app_context():
    db.create_all()  # Esto crea el archivo recetas.db y la tabla automáticamente

# --- RUTAS DEL SERVIDOR ---

@app.route('/')
def home():
    return render_template('index.html')

# RUTA GET: Leer desde SQL
@app.route('/api/recetas', methods=['GET'])
def obtener_recetas():
    # TRADUCCIÓN: "SELECT * FROM Receta"
    lista_recetas = Receta.query.all() 
    
    # Convertimos cada objeto de base de datos a JSON
    return jsonify([receta.to_json() for receta in lista_recetas])

# RUTA POST: Escribir en SQL
@app.route('/api/recetas', methods=['POST'])
def agregar_receta():
    datos = request.json
    
    # Creamos un nuevo objeto (fila)
    nueva_receta = Receta(
        nombre=datos['nombre'],
        calorias=datos['calorias'],
        apta_majo=datos.get('apta_majo', True)
    )
    
    # TRADUCCIÓN: TRANSACTION COMMIT
    db.session.add(nueva_receta) # Prepara la inserción
    db.session.commit()          # Guarda los cambios permanentemente
    
    return jsonify({"mensaje": "Guardado exitoso en SQL", "status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)