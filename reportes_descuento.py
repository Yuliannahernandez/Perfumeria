from flask import Blueprint, render_template
from datetime import datetime

reportes_descuento_bp = Blueprint('reportes_descuento', __name__)

@reportes_descuento_bp.route('/reporte_descuentos')
def reporte_descuentos():
    fecha_hoy = datetime.today().strftime('%Y-%m-%d') 
    ventas_con_descuento = []
    total_descuento_general = 0
    message = ""

    from app import get_db_connection 

 
    username = "usuario"
    password = "contraseña"

    try:
        
        conn = get_db_connection(username, password) 
        cursor = conn.cursor()

        # Consulta para obtener las ventas con descuentos aplicados en el día de hoy 
        cursor.execute('''
            SELECT DISTINCT
                v.IDVenta AS IdVenta,
                c.NombreCompleto AS Cliente,
                v.Total AS TotalVenta,
                v.Descuento AS PorcentajeDescuento,
                (v.Total * v.Descuento / 100) AS TotalDescuento
            FROM Ventas v
            JOIN Clientes c ON v.IDCliente = c.IDCliente
            WHERE v.Descuento > 0  -- Filtrar solo ventas con descuento
            AND CAST(v.FechaVenta AS DATE) = CAST(GETDATE() AS DATE)  
            ORDER BY v.IDVenta;
        ''')

        ventas_con_descuento = cursor.fetchall()

        if ventas_con_descuento:
           
            ventas_con_descuento = [
                {
                    'IdVenta': venta[0],
                    'Cliente': venta[1],
                    'TotalVenta': float(venta[2]) if venta[2] else 0,
                    'PorcentajeDescuento': float(venta[3]) if venta[3] else 0,
                    'TotalDescuento': float(venta[4]) if venta[4] else 0
                }
                for venta in ventas_con_descuento
            ]

            # Calcular el total general de los descuentos aplicados correctamente
            total_descuento_general = sum(venta['TotalDescuento'] for venta in ventas_con_descuento)
        else:
            message = "No se encontraron ventas con descuento en el día de hoy."

        conn.commit()

    except Exception as e:
        message = f"Error al obtener el reporte: {str(e)}" 
    finally:
        if conn:
            conn.close()

    return render_template('reportes_descuento.html', ventas=ventas_con_descuento, fecha=fecha_hoy, message=message, total_general=total_descuento_general)
