import pdfplumber
import re
import json

def debug_pdf_extraction(pdf_path):
    """
    Función de debug para ver exactamente qué contiene el PDF
    """
    print("🔍 Analizando el contenido del PDF...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 Total de páginas: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n--- PÁGINA {page_num + 1} ---")
                
                # Extraer texto plano
                text = page.extract_text()
                if text:
                    print("📝 Texto extraído:")
                    print(text[:500] + "..." if len(text) > 500 else text)
                    
                    # Buscar patrones específicos
                    lines = text.split('\n')
                    print(f"\n📊 Total de líneas: {len(lines)}")
                    
                    # Mostrar líneas que contienen E001
                    e001_lines = [line for line in lines if 'E001' in line]
                    print(f"📋 Líneas con E001: {len(e001_lines)}")
                    
                    for i, line in enumerate(e001_lines[:5]):  # Mostrar primeras 5
                        print(f"   {i+1}: {line}")
                    
                    if len(e001_lines) > 5:
                        print(f"   ... y {len(e001_lines) - 5} más")
                
                # Intentar extraer tablas
                tables = page.extract_tables()
                if tables:
                    print(f"\n📊 Tablas encontradas: {len(tables)}")
                    for i, table in enumerate(tables):
                        print(f"   Tabla {i+1}: {len(table)} filas")
                        if table:
                            print(f"   Primera fila: {table[0]}")
                            if len(table) > 1:
                                print(f"   Segunda fila: {table[1]}")
                else:
                    print("❌ No se encontraron tablas")
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def extract_invoices_specific_format(pdf_path):
    """
    Extractor específico para el formato de tu PDF
    """
    invoices = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Dividir por líneas y limpiar
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        
                        # Buscar líneas que empiecen con E001
                        if re.match(r'^E001\s*-\s*\d+', line):
                            # Extraer número CPE
                            cpe_match = re.search(r'E001\s*-\s*(\d+)', line)
                            if cpe_match:
                                cpe_number = cpe_match.group(1)
                                
                                # Buscar receptor en la siguiente línea
                                if i + 1 < len(lines):
                                    next_line = lines[i + 1]
                                    
                                    # Verificar si contiene RUC/DNI
                                    if re.search(r'^\d{8,11}\s*-', next_line):
                                        receptor = next_line
                                        
                                        # Buscar si hay continuación del receptor
                                        j = i + 2
                                        while j < len(lines):
                                            check_line = lines[j]
                                            
                                            # Si encuentra importe, procesarlo
                                            importe_match = re.search(r'(\$|S/)([0-9,]+\.?\d*)', check_line)
                                            if importe_match:
                                                importe = f"{importe_match.group(1)}{importe_match.group(2)}"
                                                
                                                # Buscar fecha en la misma línea o siguiente
                                                fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', check_line)
                                                if fecha_match:
                                                    fecha = fecha_match.group(1)
                                                elif j + 1 < len(lines):
                                                    fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', lines[j + 1])
                                                    if fecha_match:
                                                        fecha = fecha_match.group(1)
                                                
                                                # Crear factura si tenemos todos los datos
                                                if 'fecha' in locals():
                                                    invoice = {
                                                        'nro_cpe': f"E001-{cpe_number}",
                                                        'receptor': receptor,
                                                        'importe_total': importe,
                                                        'fecha_emision': fecha
                                                    }
                                                    invoices.append(invoice)
                                                    break
                                            
                                            # Si no es importe ni otra factura, podría ser continuación del receptor
                                            elif (not re.match(r'^E001\s*-\s*\d+', check_line) and 
                                                  not re.search(r'^\d{8,11}\s*-', check_line)):
                                                receptor += " " + check_line
                                            else:
                                                break
                                            
                                            j += 1
                                        
                                        i = j  # Continuar desde donde terminamos
                                    else:
                                        i += 1
                                else:
                                    i += 1
                            else:
                                i += 1
                        else:
                            i += 1
                            
        return invoices
        
    except Exception as e:
        raise Exception(f"Error al procesar: {str(e)}")

def test_extraction(pdf_path):
    """
    Función de prueba completa
    """
    print("🧪 Probando extracción específica...")
    
    try:
        # Primero hacer debug
        debug_pdf_extraction(pdf_path)
        
        print("\n" + "="*60)
        print("🔄 Procesando facturas...")
        
        # Extraer facturas
        invoices = extract_invoices_specific_format(pdf_path)
        
        print(f"✅ Total de facturas extraídas: {len(invoices)}")
        
        if invoices:
            print("\n📋 Facturas encontradas:")
            for i, invoice in enumerate(invoices[:10], 1):  # Mostrar primeras 10
                print(f"\n🧾 FACTURA {i}:")
                print(f"   Nro. CPE: {invoice['nro_cpe']}")
                print(f"   Receptor: {invoice['receptor']}")
                print(f"   Importe Total: {invoice['importe_total']}")
                print(f"   Fecha de Emisión: {invoice['fecha_emision']}")
                print("-" * 50)
            
            if len(invoices) > 10:
                print(f"\n... y {len(invoices) - 10} facturas más")
        else:
            print("❌ No se encontraron facturas")
            
        return invoices
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

if __name__ == "__main__":
    pdf_file = input("Ingresa la ruta del archivo PDF: ").strip()
    if pdf_file:
        test_extraction(pdf_file)
    else:
        print("❌ No se proporcionó archivo")