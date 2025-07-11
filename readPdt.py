import pdfplumber
import re
import json

# Claves objetivo
claves_ventas = {"100", "154", "102", "160", "162", "106", "127", "105", "109", "112"}
claves_compras = {"107", "156", "110", "113", "114", "116", "119", "120", "122"}
todas_claves = claves_ventas | claves_compras

# Resultado
datos = {
    "ruc": None,
    "razon_social": None,
    "periodo": None,
    "igv_ventas": {k: 0.0 for k in claves_ventas},
    "igv_compras": {k: 0.0 for k in claves_compras}
}

# Verifica si es un número decimal válido
def es_decimal_real(s):
    if not s:
        return False
    s = s.replace(',', '').replace('S/', '').replace('$', '').strip()
    return re.fullmatch(r"\d+\.\d{2}", s) is not None

# Convierte a float
def convertir_a_float(s):
    return float(s.replace(',', '').replace('S/', '').replace('$', '').strip())

# Procesar el PDF
with pdfplumber.open("PDT0621_10011625253_ENERO2025.pdf") as pdf:
    texto = "\n".join(page.extract_text() for page in pdf.pages)

# Extraer cabecera
ruc_match = re.search(r"RUC\s+(\d{11})", texto)
if ruc_match:
    datos["ruc"] = ruc_match.group(1)

razon_match = re.search(r"Razón Social\s+([A-Z\s\.&]+)", texto)
if razon_match:
    datos["razon_social"] = razon_match.group(1).strip()

periodo_match = re.search(r"Período\s+(\d{6})", texto)
if periodo_match:
    datos["periodo"] = periodo_match.group(1)

# Buscar claves y valores reales
for linea in texto.splitlines():
    partes = linea.strip().split()
    for i, parte in enumerate(partes):
        if parte in todas_claves:
            # Buscar en el resto de la línea si hay un valor decimal
            for j in range(i + 1, len(partes)):
                candidato = partes[j]
                if candidato in todas_claves:
                    break  # el valor siguiente es otro código, cancelamos
                if es_decimal_real(candidato):
                    valor = convertir_a_float(candidato)
                    if parte in claves_ventas:
                        datos["igv_ventas"][parte] = valor
                    else:
                        datos["igv_compras"][parte] = valor
                    break  # ya encontramos el valor, salimos

# Mostrar como JSON
print(json.dumps(datos, indent=4, ensure_ascii=False))
