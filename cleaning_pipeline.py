import pandas as pd
import numpy as np


def clean_agent_data(txns: pd.DataFrame, agents: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """
    Audits, cleans, flags, and enriches mobile money agent transaction data.

    Parameters
    ----------
    txns : pd.DataFrame
        Raw transaction records from the legacy mobile-money system.
    agents : pd.DataFrame
        Master agent register containing valid agent_id, county, and onboarded date.

    Returns
    -------
    tuple[pd.DataFrame, list[dict]]
        - clean_df: Cleaned and merged transaction DataFrame with quality flags.
        - log: List of dictionaries documenting each cleaning step and row counts affected.
    """
    df = txns.copy()
    log = []

    def record_step(step: str, dimension: str, action: str, rows_affected: int):
        log.append({
            "step": step,
            "dimension": dimension,
            "action": action,
            "rows_affected": int(rows_affected)
        })

    initial_rows = len(df)
    record_step("0. Load", "All", f"Initial raw transaction count: {initial_rows}", initial_rows)

    # 1. Uniqueness: Remove duplicate transactions based on txn_id
    # Note: Using subset=['txn_id'] ensures duplicates are caught even if agent_id was altered post-duplication
    dup_count = df.duplicated(subset=["txn_id"]).sum()
    df = df.drop_duplicates(subset=["txn_id"], keep="first").reset_index(drop=True)
    record_step(
        "1. Deduplication",
        "Uniqueness",
        "Dropped duplicate txn_id rows (kept first occurrence)",
        dup_count
    )

    # 2. Consistency: Standardise txn_type to 'Deposit' and 'Withdrawal'
    raw_types = df["txn_type"].astype(str)
    cleaned_types = raw_types.str.strip().str.title()
    inconsistent_count = (df["txn_type"] != cleaned_types).sum()
    df["txn_type"] = cleaned_types
    record_step(
        "2. Standardise Transaction Type",
        "Consistency",
        "Stripped whitespace and applied title case ('Deposit', 'Withdrawal')",
        inconsistent_count
    )

    # 3. Validity: Parse txn_date to ISO format (YYYY-MM-DD)
    slash_dates = df["txn_date"].astype(str).str.contains("/").sum()
    df["txn_date"] = pd.to_datetime(df["txn_date"].astype(str).str.replace("/", "-"), format="%Y-%m-%d", errors="coerce")
    df["txn_date"] = df["txn_date"].dt.strftime("%Y-%m-%d")
    record_step(
        "3. Standardise Dates",
        "Validity",
        "Replaced '/' with '-' and parsed txn_date to ISO YYYY-MM-DD format",
        slash_dates
    )

    # 4. Validity & Completeness: Convert amount to numeric and impute missing/invalid values
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["amount_imputed"] = df["amount"].isna()
    imputed_count = df["amount_imputed"].sum()

    # Impute missing amounts using median per txn_type (robust to extreme KES 250,000 outliers)
    medians = df.groupby("txn_type")["amount"].transform("median")
    df["amount"] = df["amount"].fillna(medians).round(2)
    record_step(
        "4. Numeric Amount & Imputation",
        "Completeness / Validity",
        "Coerced amount to float; imputed missing values with median by txn_type and flagged in amount_imputed",
        imputed_count
    )

    # 5. Accuracy / Outliers: Flag suspicious amounts using the IQR method
    q1 = df["amount"].quantile(0.25)
    q3 = df["amount"].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    df["is_outlier"] = (df["amount"] < lower_bound) | (df["amount"] > upper_bound)
    outlier_count = df["is_outlier"].sum()
    record_step(
        "5. Outlier Detection (IQR)",
        "Accuracy",
        f"Flagged amounts outside [{lower_bound:.2f}, {upper_bound:.2f}] in is_outlier (retained for audit)",
        outlier_count
    )

    # 6. Referential Integrity: Left merge with agents register
    df = df.merge(agents[["agent_id", "county", "onboarded"]], on="agent_id", how="left")
    unknown_agents_count = df["county"].isna().sum()
    df["county"] = df["county"].fillna("Unknown")
    record_step(
        "6. Agent Register Merge",
        "Integrity / Accuracy",
        "Left-joined with agents register; labelled unmatched agent_id records as 'Unknown' county",
        unknown_agents_count
    )

    return df, log
