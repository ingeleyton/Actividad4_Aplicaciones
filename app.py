"""Aplicación Dash para analizar la mortalidad no fetal en Colombia."""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Dict, List

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html, dash_table

from src.data_loader import build_full_dataset
from src.transforms import (
    AGE_CATEGORY_ORDER,
    ALL_VALUE,
    get_barras_apiladas_sexo,
    get_bottom10_ciudades_menos_muertes,
    get_histograma_categorias_edad,
    get_mapa_departamentos,
    get_series_mensuales,
    get_top10_causas,
    get_top5_ciudades_violentas,
)


external_stylesheets = [dbc.themes.FLATLY]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Mortalidad Colombia 2019"
server = app.server  # Exponer el objeto WSGI para gunicorn

DF_FULL = build_full_dataset()
DATA_DIR = Path(__file__).resolve().parent / "data"
GEOJSON_PATH = DATA_DIR / "colombia_departamentos.geojson"
GEOJSON_DATA = json.loads(GEOJSON_PATH.read_text())


def _normalize_geo_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return "".join(filter(str.isalnum, normalized.upper()))


GEO_LOOKUP: Dict[str, str] = {
    _normalize_geo_name(feature["properties"]["NAME_1"]): feature["properties"]["GID_1"]
    for feature in GEOJSON_DATA["features"]
}
SPECIAL_NAME_FIXES = {
    "ARCHIPIELAGODESANANDRESPROVIDENCIAYSANTACATALINA": "SANANDRESYPROVIDENCIA",
}


def _department_to_geo_id(departamento: str | None) -> str | None:
    if dep := departamento:
        normalized = _normalize_geo_name(dep)
        normalized = SPECIAL_NAME_FIXES.get(normalized, normalized)
        return GEO_LOOKUP.get(normalized)
    return None


def _build_options(items: List[str], include_all: bool = True):
    options = [{"label": item, "value": item} for item in items]
    if include_all:
        options.insert(0, {"label": "Todos", "value": ALL_VALUE})
    return options


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
        xref="paper",
        yref="paper",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    return fig


sexo_options = sorted(DF_FULL["SEXO_DESC"].dropna().unique())
departamento_options = sorted(DF_FULL["DEPARTAMENTO"].dropna().unique())
categoria_options = [cat for cat in AGE_CATEGORY_ORDER if cat in DF_FULL["categoria_edad"].unique()]
manera_options = sorted(DF_FULL["MANERA_MUERTE"].dropna().unique())


def card_block(title: str, children):
    if not isinstance(children, list):
        children = [children]
    return dbc.Card(
        [
            dbc.CardHeader(html.H4(title, className="mb-0")),
            dbc.CardBody(children),
        ],
        className="graph-card h-100",
    )


app.layout = dbc.Container(
    [
        html.H1("Mortalidad en Colombia 2019 – Aplicación Interactiva", className="mb-2"),
        html.P(
            "Explora la mortalidad no fetal de 2019 por departamento, sexo, edad y causa de muerte.",
            className="lead mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="sexo-filter",
                        options=_build_options(sexo_options),
                        value=ALL_VALUE,
                        clearable=False,
                        placeholder="Sexo",
                        className="filter-dropdown",
                    ),
                    md=4,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="departamento-filter",
                        options=_build_options(departamento_options),
                        value=ALL_VALUE,
                        clearable=False,
                        placeholder="Departamento",
                        className="filter-dropdown",
                    ),
                    md=4,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="edad-filter",
                        options=_build_options(categoria_options),
                        value=ALL_VALUE,
                        clearable=False,
                        placeholder="Categoría de edad",
                        className="filter-dropdown",
                    ),
                    md=4,
                ),
            ],
            className="gy-3 filters-row mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    card_block(
                        "Distribución por departamento",
                        [
                            dcc.Dropdown(
                                id="manera-filter",
                                options=_build_options(manera_options),
                                value=ALL_VALUE,
                                clearable=False,
                                placeholder="Manera de muerte",
                                className="mb-3",
                            ),
                            dcc.Graph(
                                id="mapa-departamentos",
                                style={"height": "420px"},
                            ),
                        ],
                    ),
                    md=7,
                ),
                dbc.Col(
                    card_block(
                        "Serie mensual de muertes",
                        dcc.Graph(id="serie-mensual", style={"height": "420px"}),
                    ),
                    md=5,
                ),
            ],
            className="gy-4 mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    card_block(
                        "Top 5 ciudades más violentas (homicidios)",
                        dcc.Graph(
                            id="top-ciudades-violentas",
                            style={"height": "380px"},
                        ),
                    ),
                    md=6,
                ),
                dbc.Col(
                    card_block(
                        "10 ciudades con menor mortalidad",
                        dcc.Graph(
                            id="bottom-ciudades-pie",
                            style={"height": "380px"},
                        ),
                    ),
                    md=6,
                ),
            ],
            className="gy-4 mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    card_block(
                        "Principales causas de muerte (Top 10)",
                        dash_table.DataTable(
                            id="tabla-causas",
                            columns=[
                                {"name": "Código CIE-10", "id": "COD_MUERTE"},
                                {"name": "Descripción", "id": "DESCRIPCION_COD_MUERTE"},
                                {"name": "Total de muertes", "id": "muertes", "type": "numeric"},
                            ],
                            data=[],
                            page_size=10,
                            style_cell={"textAlign": "left", "padding": "0.5rem"},
                            style_header={"fontWeight": "bold"},
                            style_table={"overflowX": "auto"},
                            style_as_list_view=True,
                        ),
                    ),
                    md=6,
                ),
                dbc.Col(
                    card_block(
                        "Muertes por sexo y departamento",
                        dcc.Graph(
                            id="barras-sexo",
                            style={"height": "420px"},
                        ),
                    ),
                    md=6,
                ),
            ],
            className="gy-4 mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    card_block(
                        "Distribución por categorías de edad",
                        dcc.Graph(
                            id="histograma-edad",
                            style={"height": "380px"},
                        ),
                    ),
                    md=12,
                )
            ],
            className="gy-4 mb-5",
        ),
    ],
    fluid=True,
    className="main-container py-4",
)


@app.callback(
    Output("mapa-departamentos", "figure"),
    Output("serie-mensual", "figure"),
    Output("top-ciudades-violentas", "figure"),
    Output("bottom-ciudades-pie", "figure"),
    Output("tabla-causas", "data"),
    Output("barras-sexo", "figure"),
    Output("histograma-edad", "figure"),
    Input("sexo-filter", "value"),
    Input("departamento-filter", "value"),
    Input("edad-filter", "value"),
    Input("manera-filter", "value"),
)
def update_dashboard(sexo, departamento, categoria_edad, manera):
    mapa_df = get_mapa_departamentos(DF_FULL, sexo, departamento, categoria_edad, manera)
    mapa_df["geo_id"] = mapa_df["DEPARTAMENTO"].apply(_department_to_geo_id)
    mapa_df = mapa_df.dropna(subset=["geo_id"])

    if not mapa_df.empty:
        mapa_fig = px.choropleth(
            mapa_df,
            geojson=GEOJSON_DATA,
            locations="geo_id",
            color="muertes",
            featureidkey="properties.GID_1",
            hover_data={"DEPARTAMENTO": True, "muertes": True},
            color_continuous_scale="Reds",
        )
        mapa_fig.update_geos(fitbounds="locations", visible=False)
        mapa_fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    else:
        mapa_fig = _empty_figure("Sin datos para los filtros seleccionados.")

    mensual_df = get_series_mensuales(DF_FULL, sexo, departamento, categoria_edad)
    if not mensual_df.empty:
        serie_fig = px.line(
            mensual_df,
            x="MES",
            y="muertes",
            markers=True,
            labels={"MES": "Mes", "muertes": "Muertes"},
        ).update_layout(margin=dict(l=0, r=0, t=20, b=0))
    else:
        serie_fig = _empty_figure("No hay datos mensuales.")

    top5_df = get_top5_ciudades_violentas(DF_FULL, sexo, departamento, categoria_edad)
    if not top5_df.empty:
        top_fig = px.bar(
            top5_df,
            x="muertes",
            y="MUNICIPIO",
            orientation="h",
            color="DEPARTAMENTO",
            labels={"muertes": "Homicidios", "MUNICIPIO": "Municipio"},
        ).update_layout(margin=dict(l=0, r=0, t=20, b=0))
    else:
        top_fig = _empty_figure("No hay registros de homicidios con estos filtros.")

    bottom_df = get_bottom10_ciudades_menos_muertes(DF_FULL, sexo, departamento, categoria_edad)
    if not bottom_df.empty:
        pie_fig = px.pie(
            bottom_df,
            values="muertes",
            names="MUNICIPIO",
            hover_data=["DEPARTAMENTO"],
            hole=0.3,
        ).update_layout(margin=dict(l=0, r=0, t=20, b=0))
    else:
        pie_fig = _empty_figure("No hay ciudades disponibles.")

    causas_df = get_top10_causas(DF_FULL, sexo, departamento, categoria_edad)
    causas_data = causas_df.to_dict("records")

    barras_df = get_barras_apiladas_sexo(DF_FULL, sexo, departamento, categoria_edad)
    if not barras_df.empty:
        barras_fig = px.bar(
            barras_df,
            x="DEPARTAMENTO",
            y="muertes",
            color="SEXO_DESC",
            barmode="stack",
            labels={"muertes": "Muertes", "DEPARTAMENTO": "Departamento", "SEXO_DESC": "Sexo"},
        ).update_layout(xaxis={"tickangle": -45}, margin=dict(l=0, r=0, t=20, b=120))
    else:
        barras_fig = _empty_figure("Sin datos para construir la comparación por sexo.")

    edad_df = get_histograma_categorias_edad(DF_FULL, sexo, departamento, categoria_edad)
    if not edad_df.empty:
        edad_fig = px.bar(
            edad_df,
            x="categoria_edad",
            y="muertes",
            labels={"categoria_edad": "Categoría de edad", "muertes": "Muertes"},
        ).update_layout(margin=dict(l=0, r=0, t=20, b=80))
    else:
        edad_fig = _empty_figure("No existen registros para las categorías seleccionadas.")

    return (
        mapa_fig,
        serie_fig,
        top_fig,
        pie_fig,
        causas_data,
        barras_fig,
        edad_fig,
    )


if __name__ == "__main__":
    app.run_server(debug=True)
