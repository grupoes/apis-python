from flask import Flask, request, jsonify
import pdfplumber
import re
import tempfile

app = Flask(__name__)

# claves
claves_ventas = {"100", "154", "102", "160", "162", "106", "127", "105", "109", "112"}
claves_compras = {"107", "156", "110", "113", "114", "116", "119", "120", "122"}
todas_claves = claves_ventas | claves_compras

def es_decimal_real(s):
    if not s:
        return False
    s = s.replace(',', '').replace('S/', '').replace('$', '').strip()
    return re.fullmatch(r"\d+\.\d{2}", s) is not None

def convertir_a_float(s):
    return float(s.replace(',', '').replace('S/', '').replace('$', '').strip())

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/extraer-datos", methods=["POST"])
def extraer_datos():
    if 'archivo' not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    archivo = request.files['archivo']
    if archivo.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    datos = {
        "ruc": None,
        "razon_social": None,
        "periodo": None,
        "igv_ventas": {k: 0.0 for k in claves_ventas},
        "igv_compras": {k: 0.0 for k in claves_compras}
    }

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        archivo.save(temp_file.name)
        with pdfplumber.open(temp_file.name) as pdf:
            texto = "\n".join(page.extract_text() for page in pdf.pages)

    ruc_match = re.search(r"RUC\s+(\d{11})", texto)
    if ruc_match:
        datos["ruc"] = ruc_match.group(1)

    razon_match = re.search(r"Razón Social\s+([A-Z\s\.&]+)", texto)
    if razon_match:
        datos["razon_social"] = razon_match.group(1).strip()

    periodo_match = re.search(r"Período\s+(\d{6})", texto)
    if periodo_match:
        datos["periodo"] = periodo_match.group(1)

    for linea in texto.splitlines():
        partes = linea.strip().split()
        for i, parte in enumerate(partes):
            if parte in todas_claves:
                for j in range(i + 1, len(partes)):
                    candidato = partes[j]
                    if candidato in todas_claves:
                        break
                    if es_decimal_real(candidato):
                        valor = convertir_a_float(candidato)
                        if parte in claves_ventas:
                            datos["igv_ventas"][parte] = valor
                        else:
                            datos["igv_compras"][parte] = valor
                        break

    return jsonify(datos)

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=4100)
