from flask import Blueprint, render_template
from datetime import datetime

reportes_iva_bp = Blueprint('reportes_iva', __name__)

@reportes_iva_bp.route('/reporte_iva')
def reporte_iva():
    fecha_hoy = datetime.today().strftime('%Y-%m-%d') 
    ventas_con_iva = []
    total_iva_general = 0
    message = ""

    from app import get_db_connection  
   
    username = "usuario"
    password = "contraseña"

    try:
       
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Consulta para obtener las ventas del día actual
        cursor.execute('''
            SELECT DISTINCT
                v.IDVenta AS IdVenta,
                c.NombreCompleto AS Cliente,
                v.Total AS TotalVenta,
                (v.Total * 13 / 113) AS MontoIVA  -- Calcular el IVA real
            FROM Ventas v
            JOIN Clientes c ON v.IDCliente = c.IDCliente
            WHERE v.Total > 0  -- Asegurar que hay ventas registradas
            AND CAST(v.FechaVenta AS DATE) = CAST(GETDATE() AS DATE)  -- Ventas del día
            ORDER BY v.IDVenta;
                       
        ''')

        ventas = cursor.fetchall()

        if ventas:
            for venta in ventas:
               
                total_venta = float(venta[2]) if venta[2] else 0  
                monto_iva = float(venta[3]) if venta[3] else 0  

                ventas_con_iva.append({
                    'IdVenta': venta[0],
                    'Cliente': venta[1],
                    'TotalVenta': total_venta,
                    'PorcentajeIVA': 13, 
                    'MontoIVA': monto_iva
                })

           
            total_iva_general = sum(venta['MontoIVA'] for venta in ventas_con_iva)
        else:
            message = "No se encontraron ventas en el día de hoy."

        conn.commit()

    except Exception as e:
        message = f"Error al obtener el reporte de IVA: {str(e)}"

    finally:
        if conn:
            conn.close()

    return render_template(
        'reportes_iva.html',
        ventas=ventas_con_iva,
        fecha=fecha_hoy,
        message=message,
        total_general=total_iva_general
    )
