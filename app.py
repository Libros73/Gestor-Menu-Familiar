from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)
ARCHIVO_DB = "recetas_db.json"

# --- FUNCIONES AUXILIARES (Tu lógica de backend) ---
def leer_datos():
    # 1. Si el archivo no existe, devolvemos lista vacía
    if not os.path.exists(ARCHIVO_DB):
        return []
    
    # 2. Si existe, intentamos leerlo
    try:
        with open(ARCHIVO_DB, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # 3. ¡AQUÍ ESTÁ EL BLINDAJE!
        # Si el archivo existe pero está vacío o corrupto, no explotes.
        # Simplemente asume que está vacío.
        return []

def guardar_datos(lista_nueva):
    with open(ARCHIVO_DB, "w") as f:
        json.dump(lista_nueva, f, indent=4)

# --- RUTAS DEL SERVIDOR (Los "Caminos" de tu API) ---

# RUTA 1: La entrada principal (GET)
# Cuando entres a la web, Python te sirve el HTML
@app.route('/')
def home():
    return render_template('index.html')

# RUTA 2: Entregar las recetas al Frontend (GET)
# El JS llamará aquí para pedir la lista
@app.route('/api/recetas', methods=['GET'])
def obtener_recetas():
    datos = leer_datos()
    return jsonify(datos) # Convertimos lista Python -> JSON para JS

# RUTA 3: Guardar una nueva receta (POST)
# El JS enviará datos aquí para guardarlos
@app.route('/api/recetas', methods=['POST'])
def agregar_receta():
    nueva_receta = request.json # Recibimos el paquete del JS
    
    # Lógica de guardado
    lista = leer_datos()
    lista.append(nueva_receta)
    guardar_datos(lista)
    
    return jsonify({"mensaje": "Guardado exitoso", "status": "ok"})

# --- ENCENDER EL MOTOR ---
if __name__ == '__main__':
    # debug=True permite que si cambias código, se actualice solo
    app.run(debug=True, port=5000)