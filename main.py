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

# --- 2. PROCESAMIENTO CON GROBID ---
def run_grobid():
    """Envía los PDFs al contenedor de Grobid para obtener XML/TEI."""
    print("Iniciando procesamiento con Grobid (esto puede tardar)...")
    client = GrobidClient(
        grobid_server=CONFIG["grobid_server"],
        timeout=CONFIG["timeout"],
        config_path=None, 
        check_server=True)
    
    # Procesamos todos los documentos
    client.process("processFulltextDocument", 
                   CONFIG["input_path"], 
                   output=CONFIG["output_path"], 
                   consolidate_citations=False, 
                   force=True)
    print("Procesamiento completado. Archivos XML generados en /output.")

# --- Extracción de Links ---
def extract_links(soup):
    """Extrae URLs y DOIs escritos en el PDF."""
    found = []

    # 1. Capturar URLs normales (páginas web, repositorios)
    for tag in soup.find_all(["ptr", "ref"]):
        if tag.has_attr("target"):
            found.append(tag["target"])
        elif tag.get("type") == "url":
            found.append(tag.get_text())

    # 2. Capturar DOIs
    for idno in soup.find_all("idno", type="DOI"):
        doi_clean = idno.get_text().strip()
        if doi_clean:
            # Los convertimos a enlace web para que la salida sea uniforme
            found.append(f"https://doi.org/{doi_clean}")

    # 3. Data Cleaning
    clean_list = []
    for item in found:
        c = item.strip()
        
        # Elimina años pegados al final del link
        c = c.split(',')[0]
        
        # Elimina paginación extra como "71pp"
        if "arxiv.org/abs/" in c.lower():
            c = re.sub(r'(arxiv\.org/abs/\d{4}\.\d{4,5}(?:v\d+)?).*', r'\1', c, flags=re.IGNORECASE)
        
        # C. Elimina puntuacion residual
        c = c.rstrip('.,;:)"\'-')
        
        # D. Filtrar: Aceptar solo enlaces HTTP válidos y elimina el enlace del repo de Grobid
        if c.startswith("http") and "github.com/kermitt2/grobid" not in c:
            clean_list.append(c)
                
    return list(set(clean_list))

# --- 3. EXTRACCIÓN Y ANÁLISIS ---
def analyze_data():
    """Parsea los archivos XML para extraer abstracts, figuras y links limpios."""
    all_abstracts = ""
    stats = {"filenames": [], "figures": []}
    all_links = {}

    for file in os.listdir(CONFIG["output_path"]):
        if file.endswith(".tei.xml"):
            with open(os.path.join(CONFIG["output_path"], file), 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'xml')
                
                # Abstract (para Nube de Palabras)
                abstract = soup.find('abstract')
                if abstract:
                    all_abstracts += abstract.get_text() + " "
                
                # Contar Figuras (para Gráfico de Barras)
                figure_count = len(soup.find_all('figure'))
                stats["filenames"].append(file[:15] + "...") 
                stats["figures"].append(figure_count)
                
                # Extraer Enlaces (usando la función estricta)
                all_links[file] = extract_links(soup)

    return all_abstracts, stats, all_links

# --- 4. VISUALIZACIÓN ---
def generate_viz(abstract_text, stats):
    #Genera la nube de palabras y el gráfico de barras
    
    # Nube
    if abstract_text.strip():
        wc = WordCloud(width=800, height=400, background_color='white').generate(abstract_text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title("Nube de Conceptos (Abstracts)")
        plt.savefig(os.path.join(CONFIG["output_path"], 'keyword_cloud.png'))
        plt.close()

    # Barras
    plt.figure(figsize=(12, 6))
    plt.bar(stats["filenames"], stats["figures"], color='teal')
    plt.ylabel('Número de Figuras')
    plt.title('Figuras detectadas por Artículo')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(CONFIG["output_path"], 'figures_chart.png'))
    plt.close()

# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    setup_folders()
    
    if not os.listdir(CONFIG["input_path"]):
        print("Error: La carpeta /data está vacía. Mete tus PDFs ahí.")
    else:
        try:
            run_grobid()
        except Exception as e:
            print("Error: No se pudo conectar con Grobid. Asegúrese de que el contenedor Docker está corriendo")
            exit(1)
        text, figures_stats, links_found = analyze_data()
        generate_viz(text, figures_stats)
        
        print("\nENLACES ENCONTRADOS:")
        for doc, links in links_found.items():
            print(f"\n {doc} ({len(links)} Enlaces encontrados en este pdf):")
            for l in links: 
                print(f"  - {l}")
        print("\nProceso finalizado")