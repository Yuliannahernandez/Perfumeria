from flask import Blueprint, render_template, request
from datetime import datetime

reporte_ventas_producto_bp = Blueprint('reporte_ventas_producto', __name__)

@reporte_ventas_producto_bp.route('/reporte_ventas_producto', methods=['GET', 'POST'])
def reporte_ventas_producto():
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

        
        cursor.execute('''
            SELECT DISTINCT p.nombre
            FROM Ventas v
            JOIN Detalle_Ventas dv ON v.IDVenta = dv.IDVenta
            JOIN Productos p ON dv.IDProducto = p.id_producto
            WHERE CAST(v.FechaVenta AS DATE) = CAST(GETDATE() AS DATE)
            ORDER BY p.nombre ASC;
        ''')
        productos_vendidos = sorted(set(row[0] for row in cursor.fetchall()))

    
        producto_inicial = request.form.get('producto_inicial')
        producto_final = request.form.get('producto_final') or producto_inicial

        if producto_inicial:
            # Consulta para obtener las ventas por producto en el rango seleccionado
            cursor.execute('''
                SELECT 
    p.id_producto, 
    COALESCE(tp.nombre, 'Sin Categoría') AS categoria, 
    p.id_producto AS codigo, 
    p.nombre, 
    p.descripcion, 
    CAST(p.precio AS FLOAT) AS precio, 
    SUM(dv.cantidad) AS cantidad_vendida, 
    SUM(dv.cantidad * p.precio) AS total_vendido  
FROM Ventas v
JOIN Detalle_Ventas dv ON v.IDVenta = dv.IDVenta
JOIN Productos p ON dv.IDProducto = p.id_producto
LEFT JOIN Tipos_Productos tp ON p.tipo_producto_id = tp.id_tipo_producto  
WHERE CAST(v.FechaVenta AS DATE) = CAST(GETDATE() AS DATE)
AND p.nombre BETWEEN ? AND ?
GROUP BY p.id_producto, tp.nombre, p.nombre, p.descripcion, p.precio
ORDER BY p.nombre ASC;

            ''', (producto_inicial, producto_final))

            ventas_por_producto = [
                (row[0], row[1], row[2], row[3], row[4], row[5] or 0, row[6] or 0) 
                for row in cursor.fetchall()
            ]

            # Calcular el total general de ventas
            total_general = sum(row[5] * row[6] for row in ventas_por_producto)

        else:
            message = "Seleccione al menos un producto para generar el reporte."

        conn.commit()
    except Exception as e:
        message = f"Error al obtener el reporte de ventas por producto: {str(e)}"
    finally:
        if conn: 
            conn.close()

    return render_template(
        'reporte_ventas_producto.html',
        productos=productos_vendidos,
        ventas=ventas_por_producto,
        fecha=fecha_hoy,
        message=message,
        total_general=total_general
    )
