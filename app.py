from flask import Flask, jsonify
import pdfplumber
import re
import os

app = Flask(__name__)

PDF_FILE_PATH = 'fact_robson.pdf'  # Ruta fija al archivo PDF en el servidor

def es_inicio_factura(linea):
    return re.match(r"^E\d+\s*-\s*", linea.strip()) is not None

def contiene_monto_fecha(linea):
    return (
        any(simbolo in linea for simbolo in ["S/", "$", "C$"])
        and re.search(r"\d{2}/\d{2}/\d{4}", linea)
    )

def procesar_pdf_from_path(pdf_path):
    facturas_raw = []
    inicio_detectado = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue
            lineas = texto.split('\n')
            buffer = ""
            for linea in lineas:
                if not inicio_detectado:
                    if es_inicio_factura(linea):
                        inicio_detectado = True
                        buffer = linea.strip()
                    continue
                if es_inicio_factura(linea):
                    if buffer:
                        facturas_raw.append(buffer.strip())
                    buffer = linea.strip()
                elif contiene_monto_fecha(linea):
                    buffer += "  " + linea.strip()
                else:
                    buffer += " " + linea.strip()
            if buffer:
                facturas_raw.append(buffer.strip())

    facturas_formateadas = []

    for factura in facturas_raw:
        match = re.match(
            r"^(E\d+)\s*-\s*(\d+)\s*-\s*(.+?)\s+(S/|\$|C\$)([\d,\.]+)\s+(\d{2}/\d{2}/\d{4})\s+(\d{4})(.*)?$",
            factura
        )
        if match:
            serie = match.group(1)
            ruc = match.group(2)
            razon = match.group(3).strip()
            simbolo = match.group(4)
            monto = match.group(5)
            fecha = match.group(6)
            correlativo = match.group(7)
            adicional = match.group(8).strip() if match.group(8) else ""
            monto_total = f"{simbolo}{monto}"
            if adicional:
                linea = f"{serie} | {ruc} | {razon} | {monto_total} | {fecha} | {correlativo} | {adicional}"
            else:
                linea = f"{serie} | {ruc} | {razon} | {monto_total} | {fecha} | {correlativo}"
            facturas_formateadas.append(linea)
        else:
            print("No se pudo parsear:", factura)

    return facturas_formateadas

@app.route('/procesar_pdf', methods=['GET'])
def procesar_pdf_endpoint():
    if not os.path.isfile(PDF_FILE_PATH):
        return jsonify({"error": f"Archivo '{PDF_FILE_PATH}' no encontrado"}), 404

    try:
        resultado = procesar_pdf_from_path(PDF_FILE_PATH)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": f"Error al procesar el PDF: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
