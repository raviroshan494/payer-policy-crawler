import json
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"

OUTPUT_CSV = OUTPUT_DIR / "output.csv"
SUMMARY_JSON = OUTPUT_DIR / "summary.json"
RUN_LOG = OUTPUT_DIR / "run_log.jsonl"
CHECKPOINT = DATA_DIR / "checkpoint.json"


# ============================================================
# Page
# ============================================================

st.set_page_config(
    page_title="Payer Policy Crawler",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Payer Policy Crawler")
st.caption("Crawler run and document discovery dashboard")


# ============================================================
# Loaders
# ============================================================

@st.cache_data(ttl=5)
def load_summary():
    if not SUMMARY_JSON.exists():
        return {}

    return json.loads(
        SUMMARY_JSON.read_text()
    )


@st.cache_data(ttl=5)
def load_checkpoint():
    if not CHECKPOINT.exists():
        return {}

    return json.loads(
        CHECKPOINT.read_text()
    )


@st.cache_data(ttl=5)
def load_documents():
    if not OUTPUT_CSV.exists():
        return pd.DataFrame()

    return pd.read_csv(
        OUTPUT_CSV,
        dtype=str,
        keep_default_na=False,
    )


@st.cache_data(ttl=5)
def load_logs():
    if not RUN_LOG.exists():
        return []

    records = []

    with RUN_LOG.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                records.append(
                    json.loads(line)
                )
            except json.JSONDecodeError:
                continue

    return records


summary = load_summary()
checkpoint = load_checkpoint()
documents = load_documents()
logs = load_logs()


# ============================================================
# Sidebar
# ============================================================

st.sidebar.header("Navigation")

page = st.sidebar.radio(
    "View",
    [
        "Dashboard",
        "Payers",
        "Documents",
        "Run Logs",
    ],
)


if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()


# ============================================================
# Dashboard
# ============================================================

if page == "Dashboard":

    st.subheader("Run Overview")

    payer_summaries = summary.get(
        "payers",
        [],
    )

    status_counts = {}

    for payer in payer_summaries:
        status = payer.get(
            "status",
            "unknown",
        )

        status_counts[status] = (
            status_counts.get(status, 0) + 1
        )

    total_documents = len(documents)

    total_candidates = sum(
        int(p.get("candidates", 0) or 0)
        for p in payer_summaries
    )

    total_failed = sum(
        int(p.get("failed_documents", 0) or 0)
        for p in payer_summaries
    )

    completed = status_counts.get(
        "completed",
        0,
    )

    blocked = status_counts.get(
        "blocked",
        0,
    )

    no_documents = status_counts.get(
        "no_documents_found",
        0,
    )

    failed = status_counts.get(
        "failed",
        0,
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Payers",
        len(payer_summaries),
    )

    col2.metric(
        "Documents",
        total_documents,
    )

    col3.metric(
        "Candidates",
        total_candidates,
    )

    col4.metric(
        "Failed / Skipped",
        total_failed,
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Completed",
        completed,
    )

    col2.metric(
        "Blocked",
        blocked,
    )

    col3.metric(
        "No Documents",
        no_documents,
    )

    col4.metric(
        "Crawler Errors",
        failed,
    )

    st.divider()

    st.subheader("Payer Status")

    if payer_summaries:
        payer_df = pd.DataFrame(
            payer_summaries
        )

        columns = [
            "payer_name",
            "status",
            "candidates",
            "successful_documents",
            "failed_documents",
        ]

        available = [
            c for c in columns
            if c in payer_df.columns
        ]

        st.dataframe(
            payer_df[available],
            width="stretch",
            hide_index=True,
        )

    else:
        st.info(
            "No summary data available."
        )


# ============================================================
# Payers
# ============================================================

elif page == "Payers":

    st.subheader("Payer Status")

    payer_summaries = summary.get(
        "payers",
        [],
    )

    if not payer_summaries:
        st.info("No payer data available.")
    else:

        payer_names = [
            p.get("payer_name", "")
            for p in payer_summaries
        ]

        selected = st.selectbox(
            "Select payer",
            payer_names,
        )

        payer = next(
            (
                p
                for p in payer_summaries
                if p.get("payer_name") == selected
            ),
            {},
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Status",
            payer.get(
                "status",
                "unknown",
            ),
        )

        col2.metric(
            "Candidates",
            payer.get(
                "candidates",
                0,
            ),
        )

        col3.metric(
            "Successful",
            payer.get(
                "successful_documents",
                0,
            ),
        )

        col4.metric(
            "Failed / Skipped",
            payer.get(
                "failed_documents",
                0,
            ),
        )

        st.subheader("Notes")

        notes = payer.get(
            "notes",
            [],
        )

        if notes:
            for note in notes:
                st.write(
                    f"• {note}"
                )
        else:
            st.write("No notes.")

        st.subheader("Checkpoint")

        st.write(
            checkpoint.get(
                selected,
                "pending",
            )
        )


# ============================================================
# Documents
# ============================================================

elif page == "Documents":

    st.subheader("Discovered Documents")

    if documents.empty:
        st.info(
            "No documents available."
        )
    else:

        df = documents.copy()

        col1, col2, col3 = st.columns(3)

        payer_options = sorted(
            df["payer_name"]
            .dropna()
            .unique()
            .tolist()
        )

        type_options = sorted(
            df["document_type"]
            .dropna()
            .unique()
            .tolist()
        )

        lob_options = sorted(
            df["line_of_business"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_payers = col1.multiselect(
            "Payer",
            payer_options,
        )

        selected_types = col2.multiselect(
            "Document Type",
            type_options,
        )

        selected_lob = col3.multiselect(
            "Line of Business",
            lob_options,
        )

        search = st.text_input(
            "Search title / URL",
        )

        if selected_payers:
            df = df[
                df["payer_name"].isin(
                    selected_payers
                )
            ]

        if selected_types:
            df = df[
                df["document_type"].isin(
                    selected_types
                )
            ]

        if selected_lob:
            df = df[
                df["line_of_business"].isin(
                    selected_lob
                )
            ]

        if search:
            mask = (
                df["document_title"]
                .str.contains(
                    search,
                    case=False,
                    na=False,
                )
                |
                df["document_url"]
                .str.contains(
                    search,
                    case=False,
                    na=False,
                )
            )

            df = df[mask]

        st.write(
            f"Showing {len(df):,} document(s)"
        )

        display_columns = [
            "payer_name",
            "state_or_region",
            "line_of_business",
            "document_title",
            "document_type",
            "document_url",
            "file_type",
            "policy_number",
            "effective_date",
            "last_updated_date",
            "http_status",
            "confidence_score",
            "render_mode",
        ]

        display_columns = [
            c
            for c in display_columns
            if c in df.columns
        ]

        st.dataframe(
            df[display_columns],
            width="stretch",
            hide_index=True,
        )


# ============================================================
# Run Logs
# ============================================================

elif page == "Run Logs":

    st.subheader("Crawler Run Logs")

    if not logs:
        st.info(
            "No run logs available."
        )
    else:

        log_df = pd.DataFrame(logs)

        if "timestamp" in log_df.columns:
            log_df = log_df.sort_values(
                "timestamp",
                ascending=False,
            )

        col1, col2 = st.columns(2)

        if "event" in log_df.columns:
            event_options = sorted(
                log_df["event"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_events = col1.multiselect(
                "Event",
                event_options,
            )

            if selected_events:
                log_df = log_df[
                    log_df["event"].isin(
                        selected_events
                    )
                ]

        if "payer_name" in log_df.columns:
            payer_options = sorted(
                log_df["payer_name"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_payers = col2.multiselect(
                "Payer",
                payer_options,
            )

            if selected_payers:
                log_df = log_df[
                    log_df["payer_name"].isin(
                        selected_payers
                    )
                ]

        st.write(
            f"{len(log_df):,} log event(s)"
        )

        st.dataframe(
            log_df,
            width="stretch",
            hide_index=True,
        )

        st.subheader("Raw Event")

        if len(log_df) > 0:

            selected_index = st.selectbox(
                "Select event",
                log_df.index.tolist(),
            )

            event = log_df.loc[
                selected_index
            ].to_dict()

            st.json(event)