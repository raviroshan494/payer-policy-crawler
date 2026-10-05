from pathlib import Path
import pandas as pd


CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "payer_seed_list.csv"
)

REQUIRED_COLUMNS = {"payer_name", "hint_host"}


def load_payers() -> list[dict]:
    df = pd.read_csv(CONFIG_PATH)

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError("Payer seed list is empty")

    if df["payer_name"].isna().any():
        raise ValueError("payer_name cannot be empty")

    if df["hint_host"].isna().any():
        raise ValueError("hint_host cannot be empty")

    if df["payer_name"].duplicated().any():
        raise ValueError("Duplicate payer_name found")

    return df.to_dict(orient="records")