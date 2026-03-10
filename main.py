import os
import re
from grobid_client.grobid_client import GrobidClient
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# --- 1. CONFIGURACIÓN (Infraestructura Computacional) ---
# Grobid debe estar corriendo en Docker: docker run -t --rm -p 8070:8070 grobid/grobid:0.8.0
CONFIG = {
    "input_path": "./data",
    "output_path": "./output",
    "grobid_server": "http://localhost:8070",
    "timeout": 60
}

def setup_folders():
    """Crea las carpetas necesarias si no existen."""
    for path in [CONFIG["input_path"], CONFIG["output_path"]]:
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Carpeta creada: {path}")

# --- 2. PROCESAMIENTO CON GROBID (Reproducibilidad) ---
def run_grobid():
    """Envía los PDFs al contenedor de Grobid para obtener XML/TEI."""
    print("Iniciando procesamiento con Grobid (esto puede tardar)...")
    client = GrobidClient(config_path=None, check_server=True)
    
    # Procesamos todos los documentos de la carpeta data
    client.process("processFulltextDocument", 
                   CONFIG["input_path"], 
                   output=CONFIG["output_path"], 
                   consolidate_citations=True, 
                   force=True)
    print("Procesamiento completado. Archivos XML generados en /output.")

# --- 3. EXTRACCIÓN Y ANÁLISIS (Datos procesables por máquinas) ---
def analyze_data():
    """Parsea los archivos XML para extraer abstracts, figuras y links."""
    all_abstracts = ""
    stats = {"filenames": [], "figures": []}
    all_links = {}

    for file in os.listdir(CONFIG["output_path"]):
        if file.endswith(".tei.xml"):
            with open(os.path.join(CONFIG["output_path"], file), 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'xml')
                
                # A. Extraer Abstract (para Nube de Palabras)
                abstract = soup.find('abstract')
                if abstract:
                    all_abstracts += abstract.get_text() + " "
                
                # B. Contar Figuras (para Gráfico de Barras)
                figure_count = len(soup.find_all('figure'))
                stats["filenames"].append(file[:15] + "...") # Nombre corto
                stats["figures"].append(figure_count)
                
                # C. Extraer Enlaces/URLs
                links = [ptr['target'] for ptr in soup.find_all('ptr', target=True)]
                links += [ref.get_text() for ref in soup.find_all('ref', type='url')]
                all_links[file] = list(set(links)) # Eliminar duplicados

    return all_abstracts, stats, all_links

# --- 4. VISUALIZACIÓN (Comunicación de Resultados) ---
def generate_viz(abstract_text, stats):
    """Genera la nube de palabras y el gráfico de barras."""
    
    # Nube de Palabras
    if abstract_text.strip():
        wc = WordCloud(width=800, height=400, background_color='white').generate(abstract_text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title("Nube de Conceptos (Abstracts)")
        plt.savefig('keyword_cloud.png')
        print("Nube de palabras guardada como 'keyword_cloud.png'")

    # Gráfico de Figuras
    plt.figure(figsize=(12, 6))
    plt.bar(stats["filenames"], stats["figures"], color='teal')
    plt.ylabel('Número de Figuras')
    plt.title('Figuras detectadas por Artículo')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('figures_chart.png')
    print(" Gráfico de figuras guardado como 'figures_chart.png'")

# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    setup_folders()
    
    # Verificar si hay archivos en data
    if not os.listdir(CONFIG["input_path"]):
        print("Error: La carpeta /data está vacía. Mete tus 10 PDFs ahí.")
    else:
        run_grobid()
        text, figures_stats, links_found = analyze_data()
        generate_viz(text, figures_stats)
        
        print("\n ENLACES ENCONTRADOS:")
        for doc, links in links_found.items():
            print(f"\n{doc}:")
            for l in links[:5]: # Mostrar solo los 5 primeros para no saturar
                print(f"  - {l}")
        
        print("\n Proceso finalizado con éxito.")