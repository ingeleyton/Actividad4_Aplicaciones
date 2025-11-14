"""Transformaciones para preparar datos agregados de los gráficos."""
from __future__ import annotations

from typing import Optional

import pandas as pd


ALL_VALUE = "ALL"
HOMICIDIO_CODE_PREFIX = "X95"
AGE_CATEGORY_ORDER: list[str] = [
    "Mortalidad neonatal",
    "Mortalidad infantil",
    "Primera infancia",
    "Niñez",
    "Adolescencia",
    "Juventud",
    "Adultez temprana",
    "Adultez intermedia",
    "Vejez",
    "Longevidad / Centenarios",
    "Edad desconocida",
]


def _apply_filters(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
) -> pd.DataFrame:
    filtered = df.copy()

    if sexo and sexo != ALL_VALUE:
        filtered = filtered[filtered["SEXO_DESC"] == sexo]

    if departamento and departamento != ALL_VALUE:
        filtered = filtered[filtered["DEPARTAMENTO"] == departamento]

    if categoria_edad and categoria_edad != ALL_VALUE:
        filtered = filtered[filtered["categoria_edad"] == categoria_edad]

    return filtered


def _filter_by_manera(df: pd.DataFrame, manera: Optional[str]) -> pd.DataFrame:
    if not manera or manera == ALL_VALUE:
        return df
    return df[df["MANERA_MUERTE"].str.upper() == manera.upper()]


def _filter_homicidios(df: pd.DataFrame) -> pd.DataFrame:
    codigos = df["COD_MUERTE"].fillna("").astype(str).str.upper()
    maneras = df["MANERA_MUERTE"].fillna("").astype(str).str.upper()
    homicidio_mask = maneras.eq("HOMICIDIO") | codigos.str.startswith(HOMICIDIO_CODE_PREFIX)
    return df[homicidio_mask]


def get_mapa_departamentos(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
    manera_muerte: Optional[str] = None,
) -> pd.DataFrame:
    filtered = _apply_filters(df, sexo, departamento, categoria_edad)
    filtered = _filter_by_manera(filtered, manera_muerte)

    grouped = (
        filtered.groupby(["COD_DEPARTAMENTO", "DEPARTAMENTO"], dropna=False)
        .size()
        .reset_index(name="muertes")
    )
    grouped["DEPARTAMENTO"] = grouped["DEPARTAMENTO"].fillna("SIN REGISTRO")
    grouped = grouped[grouped["COD_DEPARTAMENTO"].notna()]
    return grouped.sort_values("muertes", ascending=False)


def get_series_mensuales(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
) -> pd.DataFrame:
    filtered = _apply_filters(df, sexo, departamento, categoria_edad)
    grouped = (
        filtered.groupby("MES")
        .size()
        .reset_index(name="muertes")
        .sort_values("MES")
    )
    grouped["MES"] = grouped["MES"].astype("Int64")
    return grouped


def get_top5_ciudades_violentas(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
) -> pd.DataFrame:
    filtered = _apply_filters(df, sexo, departamento, categoria_edad)
    violentas = _filter_homicidios(filtered)
    grouped = (
        violentas.groupby(["MUNICIPIO", "DEPARTAMENTO"], dropna=False)
        .size()
        .reset_index(name="muertes")
    )
    grouped = grouped[grouped["MUNICIPIO"].notna()]
    grouped["DEPARTAMENTO"] = grouped["DEPARTAMENTO"].fillna("SIN REGISTRO")
    return grouped.sort_values("muertes", ascending=False).head(5)


def get_bottom10_ciudades_menos_muertes(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
) -> pd.DataFrame:
    filtered = _apply_filters(df, sexo, departamento, categoria_edad)
    grouped = (
        filtered.groupby(["MUNICIPIO", "DEPARTAMENTO"], dropna=False)
        .size()
        .reset_index(name="muertes")
    )
    grouped = grouped[
        grouped["MUNICIPIO"].notna() & grouped["muertes"].gt(0)
    ]
    grouped["DEPARTAMENTO"] = grouped["DEPARTAMENTO"].fillna("SIN REGISTRO")
    return grouped.sort_values("muertes", ascending=True).head(10)


def get_top10_causas(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
) -> pd.DataFrame:
    filtered = _apply_filters(df, sexo, departamento, categoria_edad)
    grouped = (
        filtered.groupby(
            ["COD_MUERTE", "DESCRIPCION_COD_MUERTE"], dropna=False
        )
        .size()
        .reset_index(name="muertes")
    )
    grouped["DESCRIPCION_COD_MUERTE"] = grouped["DESCRIPCION_COD_MUERTE"].fillna(
        "Descripción no disponible"
    )
    grouped["COD_MUERTE"] = grouped["COD_MUERTE"].fillna("Sin código")
    return grouped.sort_values("muertes", ascending=False).head(10)


def get_barras_apiladas_sexo(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
) -> pd.DataFrame:
    filtered = _apply_filters(df, sexo, departamento, categoria_edad)
    grouped = (
        filtered.groupby(["DEPARTAMENTO", "SEXO_DESC"], dropna=False)
        .size()
        .reset_index(name="muertes")
    )
    grouped["DEPARTAMENTO"] = grouped["DEPARTAMENTO"].fillna("SIN REGISTRO")
    grouped["SEXO_DESC"] = grouped["SEXO_DESC"].fillna("Sin información")
    return grouped.sort_values("muertes", ascending=False)


def get_histograma_categorias_edad(
    df: pd.DataFrame,
    sexo: Optional[str] = None,
    departamento: Optional[str] = None,
    categoria_edad: Optional[str] = None,
) -> pd.DataFrame:
    filtered = _apply_filters(df, sexo, departamento, categoria_edad)
    grouped = (
        filtered.groupby("categoria_edad", dropna=False)
        .size()
        .reset_index(name="muertes")
    )
    grouped["categoria_edad"] = pd.Categorical(
        grouped["categoria_edad"],
        categories=AGE_CATEGORY_ORDER,
        ordered=True,
    )
    return grouped.sort_values("categoria_edad")
