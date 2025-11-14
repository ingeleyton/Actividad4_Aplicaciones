## Taller 4 – App de análisis de mortalidad

Aplicación web construida con Dash + Plotly para analizar las defunciones no fetales ocurridas en Colombia durante 2019. A partir de los anexos oficiales se genera un único DataFrame enriquecido que alimenta un dashboard con 7 visualizaciones obligatorias (mapa por departamento, serie temporal, barras/pie para ciudades, tabla de causas, barras apiladas por sexo y distribución por categoría de edad).

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
- Librerías listadas en `requirements.txt` (`pandas`, `openpyxl`, `plotly`, `dash`, `dash-bootstrap-components`).

### Instalación y ejecución local

```bash
python -m venv .venv
source .venv/bin/activate           # En Windows usar .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La app quedará disponible en `http://127.0.0.1:8050/`. El layout incluye:

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
