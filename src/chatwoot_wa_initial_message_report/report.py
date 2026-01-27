from __future__ import annotations

import os
from dataclasses import asdict
from typing import Iterable, Tuple

import pandas as pd

from .extractor import InitialMessage


def _ensure_data_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_reports(records: Iterable[InitialMessage]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_df = pd.DataFrame([asdict(r) for r in records])
    if raw_df.empty:
        table_literal = pd.DataFrame(columns=["initial_message_literal", "cantidad", "porcentaje_total"])
        table_category = pd.DataFrame(columns=["category", "cantidad", "porcentaje_total"])
        return raw_df, table_literal, table_category

    total = len(raw_df)

    literal_counts = raw_df["initial_message_literal"].value_counts().reset_index()
    literal_counts.columns = ["initial_message_literal", "cantidad"]
    literal_counts["porcentaje_total"] = (literal_counts["cantidad"] / total * 100).round(2)

    category_counts = raw_df["category"].value_counts().reset_index()
    category_counts.columns = ["category", "cantidad"]
    category_counts["porcentaje_total"] = (category_counts["cantidad"] / total * 100).round(2)

    return raw_df, literal_counts, category_counts


def write_reports(
    data_dir: str,
    raw_df: pd.DataFrame,
    literal_df: pd.DataFrame,
    category_df: pd.DataFrame,
) -> None:
    _ensure_data_dir(data_dir)
    raw_df.to_csv(os.path.join(data_dir, "initial_messages_raw.csv"), index=False)
    literal_df.to_csv(os.path.join(data_dir, "initial_messages_table_literal.csv"), index=False)
    category_df.to_csv(os.path.join(data_dir, "initial_messages_table_category.csv"), index=False)
