## Taller 4 – App de análisis de mortalidad

### Introducción
Aplicación web construida con Dash + Plotly para explorar la mortalidad no fetal en Colombia durante 2019 a partir de los anexos oficiales suministrados para el taller. Todo el procesamiento se implementa en Python para garantizar reproducibilidad.

### Objetivo
Brindar un dashboard interactivo que permita identificar patrones demográficos y regionales de las defunciones (tiempo, lugar, sexo, edad y causa), resaltando los homicidios (códigos X95) y las categorías de edad derivadas de `GRUPO_EDAD1`.

### Estructura del proyecto

```
mortalidad_app/
├── app.py                     # aplicación Dash
├── requirements.txt           # dependencias
├── README.md
├── assets/
│   └── styles.css
├── data/
│   ├── Anexo1.NoFetal2019_CE_15-03-23.xlsx
│   ├── Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx
│   ├── Divipola_CE_.xlsx
│   └── colombia_departamentos.geojson   # geometría para el mapa
└── src/
    ├── data_loader.py         # carga/merge y creación de df_full
    └── transforms.py          # agregaciones para cada gráfica
```

### Datos utilizados

1. **Anexo 1** – defunciones no fetales (hoja `No_Fetales_2019`).  
2. **Anexo 2** – catálogo de códigos CIE-10 a cuatro caracteres.  
3. **Divipola** – nombres oficiales de departamentos y municipios.  
4. **GeoJSON** – límites departamentales (fuente GADM 4.1) para pintar el mapa coroplético.

`src/data_loader.py` construye `df_full` realizando:

- Normalización de códigos DANE, codificación de sexo y limpieza de cadenas.
- Enriquecimiento con nombres de departamento/municipio vía DIVIPOLA.
- Unión con el catálogo CIE-10 para obtener descripciones y capítulos.
- Creación de la columna `categoria_edad` según la tabla suministrada.

`src/transforms.py` aplica los filtros globales (sexo, departamento, categoría de edad y manera de muerte para el mapa) y expone funciones agregadas para cada visualización solicitada.

### Requisitos

- Python 3.10 o superior.
- Librerías listadas en `requirements.txt` (`pandas`, `openpyxl`, `plotly`, `dash`, `dash-bootstrap-components`, `gunicorn`).

### Software utilizado

- Python 3.11 (entorno de desarrollo).
- Dash 3.3.0 y Plotly 6.4.0 para el frontend interactivo.
- Pandas 2.3.3 + OpenPyXL 3.1.5 para la manipulación de datos.
- Dash Bootstrap Components 2.0.4 para la UI.
- Gunicorn 23.0.0 para despliegue productivo.

### Instalación y ejecución local

```bash
git clone https://github.com/ingeleyton/Actividad4_Aplicaciones.git
cd Actividad4_Aplicaciones/mortalidad_app
python -m venv .venv
source .venv/bin/activate           # En Windows usar .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

También puedes usar el Makefile:

```bash
make install   # instala dependencias
make run       # python app.py
make serve     # gunicorn app:server
```

La app quedará disponible en `https://mortalidad-app-326684895868.us-central1.run.app/`. El layout incluye:

- Panel de filtros globales (sexo, departamento, categoría de edad).
- Mapa interactivo por departamento con filtro adicional por manera de muerte.
- Serie temporal mensual, top de ciudades con más homicidios, pie chart de menor mortalidad.
- Tabla de las 10 causas más frecuentes, barras apiladas por sexo/departamento.
- Histograma por categorías de edad derivadas de `GRUPO_EDAD1`.

### Despliegue en una PaaS

1. Publicar este directorio en GitHub o similar.
2. Configurar la plataforma (Render, Railway, etc.) para usar Python 3.11+.
3. Comando de inicio sugerido:

```bash
gunicorn app:server
```

4. Asegurarse de que el directorio `data/` esté incluido en el repo (o usar un bucket seguro si es necesario).

Para Render, por ejemplo:

- **Environment**: Python 3.11  
- **Build Command**: `pip install -r requirements.txt`  
- **Start Command**: `gunicorn app:server`

### Notas

- Los archivos Excel originales no deben modificarse; cualquier preprocesamiento adicional debe implementarse en `data_loader.py`.
- Si se desea agregar nuevas visualizaciones, solo es necesario crear la transformación en `src/transforms.py` y añadir el componente correspondiente en `app.py`.

### Visualizaciones destacadas (capturas)

**Captura 1 – Visión general**
- ![Captura 1: mapa y serie mensual](images/Captura%20Nro%201.png)
- *Mapa por departamento*: el coroplético muestra que Bogotá, Antioquia y Valle del Cauca concentran la mayor mortalidad; el gradiente en tonos rojos facilita ubicar los departamentos críticos mientras los filtros globales redistribuyen los conteos en vivo.
- *Serie mensual de muertes*: la serie revela picos entre mayo-julio y diciembre, con mínimos a inicios de año, lo que sugiere una estacionalidad marcada en 2019.

**Captura 2 – Distribución por categoría de edad**
- ![Captura 2: distribución por edad](images/Captura%20Nro%202.png)
- El histograma generado a partir de `GRUPO_EDAD1` evidencia que la vejez (60‑84 años) y la longevidad/centenarios son los segmentos con más defunciones, mientras que las etapas infantiles representan porcentajes menores. Esta vista orienta la toma de decisiones hacia la población adulta mayor.

**Captura 3 – Ciudades con más/menos muertes**
- ![Captura 3: ciudades violentas y menor mortalidad](images/Captura%20Nro%203.png)
- *Top 5 ciudades violentas (homicidios)*: calcula homicidios mezclando la variable `MANERA_MUERTE` y los códigos CIE‑10 X95. Cali y Bogotá lideran, seguidas de Medellín, Barranquilla y Cúcuta, resaltando la concentración urbana de la violencia.
- *10 ciudades con menor mortalidad*: el gráfico de dona lista municipios con uno o pocos registros (Taraíra, San Fernando, Margarita, etc.), útil para contrastar territorios de muy baja mortalidad frente a las grandes urbes.
