import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="AI Research Impact Observatory", layout="wide")

# ----------------------------
# Paths
# ----------------------------
RUN_ROOT = Path("observatory_run")  # adjust if needed
GOLD_DIR = RUN_ROOT / "data" / "gold"

PAPER_FP = GOLD_DIR / "paper_scores.parquet"
FY_FP    = GOLD_DIR / "field_year_metrics.parquet"
FIELD_FP = GOLD_DIR / "field_metrics.parquet"

@st.cache_data(show_spinner=False)
def load_data():
    paper = pd.read_parquet(PAPER_FP)
    fy = pd.read_parquet(FY_FP)
    field = pd.read_parquet(FIELD_FP)

    # basic cleanup
    for df in (paper, fy, field):
        if "field" in df.columns:
            df["field"] = df["field"].fillna("NA")

    if "publication_year" in paper.columns:
        paper["publication_year"] = paper["publication_year"].astype(int)
    if "publication_year" in fy.columns:
        fy["publication_year"] = fy["publication_year"].astype(int)

    return paper, fy, field

paper, fy, field = load_data()

# ----------------------------
# Header
# ----------------------------
st.title("AI Research Impact Observatory")
st.caption(
    "A simple view of how machine learning shows up in research: "
    "how often it appears, how strong its impact looks, and where reproducibility risk rises."
)

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filters")

all_fields = sorted(paper["field"].dropna().unique().tolist())
default_field = "ComputerScience" if "ComputerScience" in all_fields else all_fields[0]

selected_fields = st.sidebar.multiselect(
    "Choose field(s)",
    options=all_fields,
    default=[default_field]
)

min_year = int(paper["publication_year"].min())
max_year = int(paper["publication_year"].max())
year_range = st.sidebar.slider(
    "Year range",
    min_year, max_year, (min_year, max_year)
)

# thresholds
score_min, score_max = float(paper["ml_impact_score"].min()), float(paper["ml_impact_score"].max())
score_thresh = st.sidebar.slider(
    "Minimum Impact Score",
    0.0,
    float(max(0.001, score_max)),
    0.0
)

ml_prob_thresh = st.sidebar.slider(
    "Minimum Probability the paper uses ML",
    0.0, 1.0, 0.0
)

# Apply filters
paper_f = paper[
    (paper["field"].isin(selected_fields)) &
    (paper["publication_year"].between(year_range[0], year_range[1])) &
    (paper["ml_impact_score"] >= score_thresh) &
    (paper["is_ml_prob"] >= ml_prob_thresh)
].copy()

fy_f = fy[
    (fy["field"].isin(selected_fields)) &
    (fy["publication_year"].between(year_range[0], year_range[1]))
].copy()

# ----------------------------
# KPIs (plain language)
# ----------------------------
c1, c2, c3, c4 = st.columns(4)

n_papers = len(paper_f)
avg_impact = float(paper_f["ml_impact_score"].mean()) if n_papers else None
avg_risk = float(paper_f["repro_risk"].mean()) if n_papers else None

# IMPORTANT: ML share should come from the field-year aggregation (fy), not avg is_ml_prob
ml_share = float(fy_f["ml_share"].mean()) if len(fy_f) else None

with c1:
    st.metric("Papers (after filters)", f"{n_papers:,}")
with c2:
    st.metric("Average impact score", f"{avg_impact:.4f}" if avg_impact is not None else "—")
with c3:
    st.metric("Average reproducibility risk", f"{avg_risk:.4f}" if avg_risk is not None else "—")
with c4:
    st.metric("ML usage (share)", f"{ml_share*100:.2f}%" if ml_share is not None else "—")

st.divider()

# ----------------------------
# Year-by-year charts (answers the “over time” question)
# ----------------------------
st.subheader("Trends over time")

if len(fy_f) == 0:
    st.info("No field-year data for the selected filters.")
else:
    # handle p90 vs p95 naming
    top_col = None
    if "p90_ml_impact" in fy_f.columns:
        top_col = "p90_ml_impact"
        top_label = "Top 10% impact (p90)"
    elif "p95_ml_impact" in fy_f.columns:
        top_col = "p95_ml_impact"
        top_label = "Top 5% impact (p95)"
    else:
        top_label = None

    # 1) ML usage over time (by field)
    left, right = st.columns(2)

    with left:
        st.markdown("**How common is ML in papers (by year)?**")
        fig = px.line(
            fy_f.sort_values(["field", "publication_year"]),
            x="publication_year",
            y="ml_share",
            color="field",
            markers=True,
            labels={"publication_year": "Year", "ml_share": "ML usage (share)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("**How does ML impact change over time?**")
        if top_col:
            long = fy_f.melt(
                id_vars=["field", "publication_year"],
                value_vars=["avg_ml_impact", top_col],
                var_name="series",
                value_name="value",
            )
            long["series"] = long["series"].replace({
                "avg_ml_impact": "Average impact",
                top_col: top_label
            })
            fig2 = px.line(
                long.sort_values(["field", "publication_year"]),
                x="publication_year",
                y="value",
                color="field",
                line_dash="series",
                markers=True,
                labels={"publication_year": "Year", "value": "Impact score", "series": ""},
            )
        else:
            fig2 = px.line(
                fy_f.sort_values(["field", "publication_year"]),
                x="publication_year",
                y="avg_ml_impact",
                color="field",
                markers=True,
                labels={"publication_year": "Year", "avg_ml_impact": "Average impact score"},
            )
        st.plotly_chart(fig2, use_container_width=True)

    # 2) Reproducibility risk over time (by field)
    if "avg_repro_risk" in fy_f.columns:
        st.markdown("**Does reproducibility risk change over time?**")
        fig3 = px.line(
            fy_f.sort_values(["field", "publication_year"]),
            x="publication_year",
            y="avg_repro_risk",
            color="field",
            markers=True,
            labels={"publication_year": "Year", "avg_repro_risk": "Average reproducibility risk"},
        )
        st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ----------------------------
# Trade-off view (impact vs reproducibility)
# ----------------------------
st.subheader("Trade-off: Impact vs reproducibility risk")
st.caption("Each dot is a paper. This helps you spot high-impact papers that also look risky to reproduce.")

if len(paper_f) == 0:
    st.info("No papers after filtering.")
else:
    plot_df = paper_f.copy()
    if len(plot_df) > 20000:
        plot_df = plot_df.sample(20000, random_state=42)

    # more readable scatter with hover info
    hover_cols = [c for c in ["paper_id", "field", "publication_year", "is_ml_prob", "score_driver", "matched_term"] if c in plot_df.columns]
    fig_scatter = px.scatter(
        plot_df,
        x="ml_impact_score",
        y="repro_risk",
        color="field" if len(selected_fields) > 1 else None,
        hover_data=hover_cols,
        labels={"ml_impact_score": "Impact score", "repro_risk": "Reproducibility risk"},
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ----------------------------
# Leaderboards
# ----------------------------
l1, l2 = st.columns(2)

with l1:
    st.subheader("Fields ranked (overall)")
    show_cols = [c for c in ["field", "n_papers", "ml_share", "avg_ml_impact", "p95_ml_impact", "avg_repro_risk"] if c in field.columns]
    st.dataframe(
        field.sort_values(["avg_ml_impact", "ml_share", "n_papers"], ascending=False)[show_cols]
             .head(20)
             .reset_index(drop=True),
        use_container_width=True
    )

with l2:
    st.subheader("Top papers (after filters)")
    topk = st.slider("How many top papers to show?", 10, 200, 50)
    show_cols = [c for c in [
        "paper_id", "field", "publication_year", "split",
        "is_ml_prob", "ml_impact_score", "repro_risk",
        "adoption_pred", "impact_pred", "repro_pred",
        "score_driver", "matched_term"
    ] if c in paper_f.columns]

    if len(paper_f):
        st.dataframe(
            paper_f.sort_values("ml_impact_score", ascending=False)[show_cols].head(topk),
            use_container_width=True
        )
    else:
        st.info("No papers after filtering.")

st.divider()

# ----------------------------
# Paper lookup
# ----------------------------
st.subheader("Paper lookup")
st.caption("Paste a paper_id to find its row quickly (exact match).")

pid = st.text_input("Paper ID", value="")
if pid:
    hit = paper[paper["paper_id"].astype(str) == str(pid)]
    if len(hit):
        st.success(f"Found {len(hit)} row(s).")
        st.dataframe(hit, use_container_width=True)
    else:
        st.warning("No match found.")
