from flask import Flask, jsonify
import pdfplumber
import re

app = Flask(__name__)

def extraer_datos_pdf(ruta_pdf):
    resultados = []
    estado = 0  # 0: esperando E001, 1: RUC + razón, 2: importe+fecha, 3: correlativo
    factura = {}

    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            lineas = [l.strip() for l in pagina.extract_text().split('\n') if l.strip()]
            i = 0

            while i < len(lineas):
                linea = lineas[i]

                if estado == 0 and linea.startswith("E001 -"):
                    factura = {"serie": "E001"}
                    # ¿Viene el RUC en esta misma línea?
                    match_inline = re.match(r'^E001\s*-\s*(\d{11})\s*-\s*(.+)', linea)
                    if match_inline:
                        factura["ruc"] = match_inline.group(1)
                        factura["razon"] = match_inline.group(2)
                        estado = 2
                    else:
                        estado = 1
                    i += 1
                    continue

                if estado == 1:
                    match_ruc = re.match(r'^(\d{11})\s*-\s*(.+)', linea)
                    if match_ruc:
                        factura["ruc"] = match_ruc.group(1)
                        factura["razon"] = match_ruc.group(2)
                        estado = 2
                    i += 1
                    continue

                if estado == 2:
                    match_pago = re.search(r'([S/\$]\s?[0-9,]+\.\d{2})\s+(\d{2}/\d{2}/\d{4})', linea)
                    if match_pago:
                        factura["importe"] = match_pago.group(1).replace(' ', '')
                        factura["fecha"] = match_pago.group(2)
                        estado = 3
                    i += 1
                    continue

                if estado == 3:
                    match_corr = re.match(r'^(\d{4})(\s+.+)?', linea)
                    if match_corr:
                        correlativo = match_corr.group(1)
                        razon_adicional = match_corr.group(2).strip() if match_corr.group(2) else ""

                        razon_final = f'{factura["razon"]} {razon_adicional}'.strip()
                        nro_cpe = f'{factura["serie"]}-{correlativo}'

                        resultados.append({
                            "nro_cpe": nro_cpe,
                            "receptor": {
                                "ruc": factura["ruc"],
                                "razon_social": razon_final
                            },
                            "importe_total": factura["importe"],
                            "fecha_emision": factura["fecha"]
                        })

                        factura = {}
                        estado = 0  # reiniciar para la siguiente factura

                    i += 1
                    continue

                i += 1  # fallback por seguridad

    return resultados

@app.route('/api/cpe', methods=['GET'])
def obtener_datos():
    ruta_pdf = 'fact_robson.pdf'
    datos = extraer_datos_pdf(ruta_pdf)
    return jsonify(datos)

if __name__ == '__main__':
    app.run(debug=True)
