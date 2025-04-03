from flask import Blueprint, render_template, request
from datetime import datetime

reporte_rango_fecha_bp = Blueprint('reporte_rango_fecha', __name__)

@reporte_rango_fecha_bp.route('/reporte_rango_fecha', methods=['GET', 'POST'])
def reporte_rango_fecha():
    fecha_hoy = datetime.today().strftime('%d/%m/%Y')  
    productos_vendidos = []
    ventas_por_producto = []
    total_general = 0
    message = ""

    from app import get_db_connection 

    username = "usuario"
    password = "contraseña"

    conn = None  

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Obtener la lista de productos vendidos en el rango de fechas seleccionado
        cursor.execute('''
            SELECT DISTINCT p.nombre
            FROM Ventas v
            JOIN Detalle_Ventas dv ON v.IDVenta = dv.IDVenta
            JOIN Productos p ON dv.IDProducto = p.id_producto
            ORDER BY p.nombre ASC;
        ''')
        productos_vendidos = sorted(set(row[0] for row in cursor.fetchall()))

        
        fecha_inicial = request.form.get('fecha_inicial')
        fecha_final = request.form.get('fecha_final') or fecha_inicial

        if fecha_inicial and fecha_final:
            # Consulta para obtener las ventas por producto en el rango de fechas seleccionado
            cursor.execute('''
                SELECT 
                    p.id_producto, 
                    COALESCE(tp.nombre, 'Sin Categoría') AS categoria, 
                    p.id_producto AS codigo, 
                    p.nombre, 
                    p.descripcion, 
                    CONVERT(VARCHAR, v.FechaVenta, 103) AS fecha,  
                    CAST(p.precio AS FLOAT) AS precio, 
                    SUM(dv.cantidad) AS cantidad_vendida, 
                    SUM(dv.cantidad * p.precio) AS total_vendido  
                FROM Ventas v
                JOIN Detalle_Ventas dv ON v.IDVenta = dv.IDVenta
                JOIN Productos p ON dv.IDProducto = p.id_producto
                LEFT JOIN Tipos_Productos tp ON p.tipo_producto_id = tp.id_tipo_producto  
                WHERE CAST(v.FechaVenta AS DATE) BETWEEN ? AND ?
                GROUP BY p.id_producto, tp.nombre, p.nombre, p.descripcion, p.precio, v.FechaVenta
                ORDER BY p.nombre ASC;
            ''', (fecha_inicial, fecha_final))

            ventas_por_producto = [
                (row[2], row[3], row[4], row[5], row[6], row[7] or 0, row[8] or 0)
                for row in cursor.fetchall()
            ]

            # Calcular el total general de ventas
            total_general = sum(row[6] for row in ventas_por_producto)

        else:
            message = "Seleccione un rango de fechas para generar el reporte."

        conn.commit()
    except Exception as e:
        message = f"Error al obtener el reporte de ventas por rango de fechas: {str(e)}"
    finally:
        if conn: 
            conn.close()

    return render_template(
        'reporte_rango_fecha.html',
        productos=productos_vendidos,
        ventas=ventas_por_producto,
        fecha=fecha_hoy,
        message=message,
        total_general=total_general
    )
