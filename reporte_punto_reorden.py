from flask import Blueprint, render_template
from datetime import datetime


reporte_punto_reorden_bp = Blueprint('reporte_punto_reorden', __name__)

@reporte_punto_reorden_bp.route('/reporte_punto_reorden', methods=['GET'])
def reporte_punto_reorden():
    fecha_hoy = datetime.today().strftime('%d/%m/%Y')  
    productos_punto_reorden = []
    total_productos_punto = 0
    message = ""

    from app import get_db_connection  

    username = "usuario"
    password = "contraseña"

    conn = None 

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Obtener los productos cuyo stock en bodega sea menor o igual a 5
        
        cursor.execute('''
            SELECT 
                p.id_producto, 
                p.nombre, 
                p.descripcion, 
                p.existencia_bodega, 
                p.precio
            FROM Productos p
            WHERE (p.existencia_bodega <= 5 OR p.existencia_bodega IS NULL)
            ORDER BY p.nombre ASC;
        ''')

        productos_punto_reorden = [
            (row[0], row[1], row[2], row[3], row[4])  
            for row in cursor.fetchall()
        ]

        total_productos_punto = len(productos_punto_reorden)  # Contar los productos con baja existencia en bodega

    except Exception as e:
        message = f"Error al obtener el reporte de productos en punto de reorden: {str(e)}"
    finally:
        if conn: 
            conn.close()

    return render_template(
        'reporte_punto_reorden.html',
        productos=productos_punto_reorden,
        fecha=fecha_hoy,
        total_productos_punto=total_productos_punto,
        message=message
    )
