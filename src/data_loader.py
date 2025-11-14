"""Funciones para cargar y preparar los datos de mortalidad."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Final, Iterable

import pandas as pd


DATA_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "data"
FILES: Final = {
    "mortalidad": "Anexo1.NoFetal2019_CE_15-03-23.xlsx",
    "codigos": "Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx",
    "divipola": "Divipola_CE_.xlsx",
}
SHEET_NO_FETALES: Final[str] = "No_Fetales_2019"


AGE_CATEGORY_LABELS: Final = {
    **{code: "Mortalidad neonatal" for code in range(0, 5)},
    **{code: "Mortalidad infantil" for code in range(5, 7)},
    **{code: "Primera infancia" for code in range(7, 9)},
    **{code: "Niñez" for code in range(9, 11)},
    11: "Adolescencia",
    **{code: "Juventud" for code in range(12, 14)},
    **{code: "Adultez temprana" for code in range(14, 17)},
    **{code: "Adultez intermedia" for code in range(17, 20)},
    **{code: "Vejez" for code in range(20, 25)},
    **{code: "Longevidad / Centenarios" for code in range(25, 29)},
    29: "Edad desconocida",
}
DEFAULT_AGE_CATEGORY: Final[str] = "Edad desconocida"
SEXO_MAP: Final = {
    1: "Masculino",
    2: "Femenino",
}
SEXO_DEFAULT: Final[str] = "Sin información"


def _load_excel(filename: str, **kwargs) -> pd.DataFrame:
    """Carga cualquier archivo Excel con openpyxl como motor."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {path}")
    return pd.read_excel(path, engine="openpyxl", **kwargs)


def load_mortalidad() -> pd.DataFrame:
    """Carga el anexo de mortalidad no fetal 2019."""
    return _load_excel(
        FILES["mortalidad"],
        sheet_name=SHEET_NO_FETALES,
    )


CODE_COLUMNS: Final[list[str]] = [
    "Capítulo",
    "Nombre capítulo",
    "Código de la CIE-10 tres caracteres",
    "Descripción  de códigos mortalidad a tres caracteres",
    "Código de la CIE-10 cuatro caracteres",
    "Descripcion  de códigos mortalidad a cuatro caracteres",
]


def load_codigos_muerte() -> pd.DataFrame:
    """Carga el catálogo de códigos CIE-10 con sus descripciones."""
    df = _load_excel(FILES["codigos"], header=None, skiprows=5, names=CODE_COLUMNS)
    df = df.rename(
        columns={
            "Código de la CIE-10 tres caracteres": "codigo_tres",
            "Descripción  de códigos mortalidad a tres caracteres": "descripcion_tres",
            "Código de la CIE-10 cuatro caracteres": "codigo_cuatro",
            "Descripcion  de códigos mortalidad a cuatro caracteres": "descripcion_cuatro",
        }
    )
    df = df.dropna(subset=["codigo_cuatro"])
    df["codigo_cuatro"] = (
        df["codigo_cuatro"].astype("string").str.strip().str.upper()
    )
    return df


def load_divipola() -> pd.DataFrame:
    """Carga la tabla DIVIPOLA de municipios."""
    return _load_excel(FILES["divipola"])


def _normalize_numeric_code(series: pd.Series, width: int | None = None) -> pd.Series:
    """Convierte columnas con códigos numéricos a strings conservando ceros a la izquierda."""
    normalized = (
        pd.to_numeric(series, errors="coerce")
        .astype("Int64")
        .astype("string")
    )
    normalized = normalized.str.replace(r"\.0$", "", regex=True)
    if width:
        normalized = normalized.str.zfill(width)
    return normalized


def _map_categoria_edad(code: object) -> str:
    if pd.isna(code):
        return DEFAULT_AGE_CATEGORY
    try:
        int_code = int(code)
    except (TypeError, ValueError):
        return DEFAULT_AGE_CATEGORY
    return AGE_CATEGORY_LABELS.get(int_code, DEFAULT_AGE_CATEGORY)


def _clean_string(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def _select_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Devuelve solo las columnas solicitadas si existen."""
    existing = [column for column in columns if column in df.columns]
    return df[existing].copy()


@lru_cache(maxsize=1)
def build_full_dataset() -> pd.DataFrame:
    """
    Construye un único DataFrame enriquecido con DIVIPOLA y descripciones CIE-10.

    Retorna:
        DataFrame listo para alimentar los gráficos de la aplicación.
    """
    mortalidad = load_mortalidad().copy()
    codigos = load_codigos_muerte()
    divipola = load_divipola()

    mortalidad["COD_DANE"] = _normalize_numeric_code(mortalidad["COD_DANE"], width=5)
    mortalidad["COD_DEPARTAMENTO"] = _normalize_numeric_code(
        mortalidad["COD_DEPARTAMENTO"], width=2
    )
    mortalidad["COD_MUNICIPIO"] = _normalize_numeric_code(
        mortalidad["COD_MUNICIPIO"], width=3
    )
    mortalidad["COD_MUERTE"] = _clean_string(mortalidad["COD_MUERTE"]).str.upper()
    mortalidad["MANERA_MUERTE"] = _clean_string(mortalidad["MANERA_MUERTE"])
    mortalidad["SEXO"] = pd.to_numeric(mortalidad["SEXO"], errors="coerce").astype("Int64")

    divipola = divipola.rename(
        columns={
            "DEPARTAMENTO": "NOMBRE_DEPARTAMENTO",
            "MUNICIPIO": "NOMBRE_MUNICIPIO",
        }
    )
    divipola["COD_DANE"] = _normalize_numeric_code(divipola["COD_DANE"], width=5)
    divipola["COD_DEPARTAMENTO"] = _normalize_numeric_code(
        divipola["COD_DEPARTAMENTO"], width=2
    )
    divipola["COD_MUNICIPIO"] = _normalize_numeric_code(
        divipola["COD_MUNICIPIO"], width=3
    )

    dataset = mortalidad.merge(
        _select_columns(
            divipola,
            ["COD_DANE", "NOMBRE_DEPARTAMENTO", "NOMBRE_MUNICIPIO", "COD_DEPARTAMENTO"],
        ),
        on="COD_DANE",
        how="left",
        suffixes=("", "_DIVI"),
    )
    dataset = dataset.rename(
        columns={
            "NOMBRE_DEPARTAMENTO": "DEPARTAMENTO",
            "NOMBRE_MUNICIPIO": "MUNICIPIO",
        }
    )
    # Si el merge encontró un código más limpio de departamento, lo usamos.
    dataset["COD_DEPARTAMENTO"] = dataset["COD_DEPARTAMENTO_DIVI"].combine_first(
        dataset["COD_DEPARTAMENTO"]
    )
    dataset = dataset.drop(columns=[col for col in dataset.columns if col.endswith("_DIVI")])

    dataset = dataset.merge(
        _select_columns(
            codigos,
            [
                "Capítulo",
                "Nombre capítulo",
                "codigo_tres",
                "descripcion_tres",
                "codigo_cuatro",
                "descripcion_cuatro",
            ],
        ),
        left_on="COD_MUERTE",
        right_on="codigo_cuatro",
        how="left",
    )

    dataset = dataset.rename(
        columns={
            "Capítulo": "CAPITULO_CIE10",
            "Nombre capítulo": "NOMBRE_CAPITULO_CIE10",
            "descripcion_cuatro": "DESCRIPCION_COD_MUERTE",
            "codigo_tres": "CODIGO_CIE10_TRES",
            "descripcion_tres": "DESCRIPCION_CIE10_TRES",
        }
    )

    dataset["categoria_edad"] = dataset["GRUPO_EDAD1"].apply(_map_categoria_edad)
    dataset["DEPARTAMENTO"] = _clean_string(dataset["DEPARTAMENTO"]).str.upper()
    dataset["MUNICIPIO"] = _clean_string(dataset["MUNICIPIO"]).str.upper()
    dataset["SEXO_DESC"] = dataset["SEXO"].map(SEXO_MAP).fillna(SEXO_DEFAULT)

    return dataset
