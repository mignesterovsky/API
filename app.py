from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse, abort
import pandas as pd
import os

app = Flask(__name__)
api = Api(app)

# Ruta al archivo Excel
ruta_excel = os.path.join(os.path.dirname(__file__), 'data', 'operaciones.xlsx')

# Cargar la base de datos desde Excel
dframe = pd.read_excel(ruta_excel)

# hacemos un Parser para la paginación
parser = reqparse.RequestParser()
parser.add_argument('page', type=int, default=1, help='Número de página')

# Manejo de errores personalizado si el registro no se encuentra
def registro_no_encontrado(id):
    if id not in dframe['ID'].values:
        abort(404, message=f"Registro con ID {id} no encontrado")

# Recurso para obtener todos los registros con paginación
class RegistrosResource(Resource):
    def get(self):
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        # Verificar si la columna 'ID' existe en el DataFrame
        if 'ID' not in dframe.columns:
            abort(500, message="La columna 'ID' no existe en la base de datos.")

        total_registros = len(dframe)
        total_paginas = (total_registros + page_size - 1) // page_size  # Redondeo hacia arriba
        start_index = (page - 1) * page_size
        end_index = min(start_index + page_size, total_registros)

        if start_index >= total_registros:
            abort(404, message=f"No hay registros en la página {page}.")

        registros = dframe.iloc[start_index:end_index].to_dict(orient='records')

        # Información de paginación
        pagination_info = {
            "total": total_registros,
            "perPage": page_size,
            "currentPage": page,
            "totalPages": total_paginas
        }

        return jsonify({"pagination": pagination_info, "data": registros})


# Recurso para filtrar por ID
class RegistroResource(Resource):
    def get(self, id):
        registro_no_encontrado(id)
        registro = dframe[dframe['ID'] == id].to_dict(orient='records')
        return jsonify(registro)

# Recurso para buscar por campo específico
class BuscarResource(Resource):
    def get(self):
        campo = request.args.get('campo')
        valor = request.args.get('valor')

        # Verificar si el campo existe en el DataFrame
        if campo not in dframe.columns:
            abort(400, message=f'Campo {campo} no encontrado')

        # Convertir el campo al tipo de dato del valor de búsqueda (en este caso, cadena)
        df_campo = dframe[campo].astype(str)

        # Convertir ambas cadenas a mayúsculas antes de la comparación
        #debido a que en la Base de datos se encuentran en mayúsculas
        df_campo = df_campo.str.upper()
        valor = valor.upper()

        # Filtrar registros basados en el campo y valor
        resultados = dframe[df_campo == valor]

        # Verificar si hay resultados
        if resultados.empty:
            abort(404, message=f"No se encontraron registros con {campo} igual a {valor}.")

        # Parámetros de paginación
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        # Paginación de resultados
        total_registros = len(resultados)
        total_paginas = (total_registros + page_size - 1) // page_size  # Redondeo hacia arriba
        start_index = (page - 1) * page_size
        end_index = min(start_index + page_size, total_registros)

        resultados_paginados = resultados.iloc[start_index:end_index].to_dict(orient='records')

        # Información de paginación
        pagination_info = {
            "total": total_registros,
            "perPage": page_size,
            "currentPage": page,
            "totalPages": total_paginas
        }

        return jsonify({"pagination": pagination_info, "data": resultados_paginados})


# Agregar recursos a la API
api.add_resource(RegistrosResource, '/api/registros')
api.add_resource(RegistroResource, '/api/registros/<int:id>')
api.add_resource(BuscarResource, '/api/buscar')

# Función para manejar rutas no encontradas
@app.errorhandler(404)
def ruta_no_existe(e):
    return jsonify({"error": "Ruta Ingresada no pertenece a la API"}), 404

if __name__ == '__main__':
    app.run(debug=True)

