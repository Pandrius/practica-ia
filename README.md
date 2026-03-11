[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18965916.svg)](https://doi.org/10.5281/zenodo.18965916)
# Práctica IA: Extracción de Metadatos con Grobid

Este proyecto implementa un pipeline de extracción de texto y metadatos científicos (figuras y enlaces explícitos) a partir de artículos en formato PDF utilizando Grobid y Python.

## Instrucciones de Instalación y Uso

Este proyecto está diseñado para ser fácilmente reproducible. Requiere tener instalados **Python 3.x** y **Docker** (para levantar el servidor local de Grobid).

### 1. Prerrequisitos (Linux/Wsl)
Si no tienes las herramientas base, puedes instalarlas con los siguientes comandos:

```bash
# Instalar Python 3.x
sudo apt update && sudo apt install python3

# Instalar Docker Engine:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```
### 2. Preparación del Entorno
Primero, clona este repositorio e instala las dependencias de Python necesarias:
```bash
# Clonar el repositorio
git clone https://github.com/Pandrius/practica-ia.git
cd practica-ia

#Crear entorno virtual
sudo apt update
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate

# Instalar librerías (puedes usar uv o pip clásico, elige uno)
uv pip install -r requirements.txt
# pip install -r requirements.txt
```
### 3. Ejecución del Proyecto
Paso A: Iniciar el servidor Grobid
Inicia el contenedor de Docker para levantar la API local:

```bash
docker run -t --rm -p 8070:8070 grobid/grobid:0.8.0
#Paso B: Ejecutar el código
#Ahora abre otra ventana de la terminal, ubícate en el directorio del repositorio y ejecuta el código:
python main.py
```
En caso de que quiera analizar otros papers, asegúrese de meterlos en la carpeta data/.

### Validación

## 1. Conteo de Figuras:

En las pruebas se ha comprobado que, al ser papers físicos con mucho contenido matemático, Grobid tiene dificultades para identificar el número exacto de figuras ya que también identifica ocasionalmente las tablas, diagramas, bloques de ecuaciones y algunos símbolos como figuras <figure> por lo que en la cuenta muchas veces salen más figuras de las que hay, esto se puede arreglar añadiendo un filtrado del tipo tablas y de los tipos correspondientes al resto de figuras que se añaden de forma incorrecta a la hora de realizar el conteo. Únicamente en uno de los 10 papers empleados ha habido una cuenta por debajo porque en el xml no salían como figuras las figuras que había.

## 2. Nubes de Palabras Clave:

En cuanto a las nubes de palabras clave, se ha utilizado únicamente la parte de los abstracts de los papers para eliminar las "palabras basura", esto ha conseguido que las nubes sean bastante precisas con el contenido de los papers.

## 3. Extracción de Enlaces y DOIs:

Por último, los links la mayoría están bien y funcionan correctamente, ha habido que hacer unos pequeños ajustes en el código para que se identificasen los DOIs también como enlaces ya que no están incluidos en los ptr sino como metadatos aislados (<idno type="DOI">). Además, Grobid frecuentemente incluía signos de puntuación, años de publicación (ej. ...00119-x,2024) o metadatos de paginación de arXiv (ej. ...13908v571pp) dentro de la propia URL, rompiendo el enlace. También ha habido que filtrar el enlace del propio repositorio que aparece al principio de cada XML que genera Grobid. Se ha diseñado una capa de Data Cleaning en Python. Mediante el uso de Expresiones Regulares (Regex) y limpieza de cadenas, el código purga este "ruido de extracción", unifica los DOIs como URLs estándar y garantiza que la mayoría de los identificadores exportados funcionen correctamente.