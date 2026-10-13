"""
CineMatch -- Stage 9
Reusable UI components: CSS design system, movie cards, grid layouts.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------
ACCENT = "#F5A524"
BG = "#0B0E14"
SURFACE = "#141922"
BORDER = "#232A36"
TEXT = "#E6EDF3"
MUTED = "#9BA6B2"

PLACEHOLDER_SVG = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450' viewBox='0 0 300 450'>"
    "<rect width='300' height='450' fill='%23141922'/>"
    "<text x='150' y='225' font-family='sans-serif' font-size='60' "
    "text-anchor='middle' fill='%233A4555' dy='.35em'>?</text>"
    "<text x='150' y='290' font-family='sans-serif' font-size='14' "
    "text-anchor='middle' fill='%23566070'>No poster</text></svg>"
)


# ---------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------
def inject_css():
    st.markdown(
        f"""
        <style>
            #MainMenu, footer {{ visibility: hidden; }}
            /* FIXED: Changed padding-top from 1.5rem to 4rem so the title isn't cut off */
            .block-container {{ padding-top: 4rem; max-width: 1300px; }}

            /* ---------- Brand header ---------- */
            .cm-brand {{
                font-size: 2rem;
                font-weight: 800;
                letter-spacing: 0.35rem;
                background: linear-gradient(90deg, {ACCENT}, #FFD98E);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 0;
            }}
            .cm-tagline {{
                color: {MUTED};
                font-size: 0.95rem;
                margin-top: 0.15rem;
                margin-bottom: 1.25rem;
            }}

            /* ---------- Section headings ---------- */
            .cm-section {{
                font-size: 1.35rem;
                font-weight: 700;
                color: {TEXT};
                margin: 2rem 0 0.75rem 0;
                letter-spacing: 0.02rem;
            }}
            .cm-section-sub {{
                color: {MUTED};
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }}

            /* ---------- Movie card ---------- */
            .cm-card {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
                overflow: hidden;
                transition: transform .15s ease, border-color .15s ease;
                height: 100%;
            }}
            .cm-card:hover {{
                transform: translateY(-3px);
                border-color: {ACCENT};
            }}
            .cm-card img {{
                width: 100%;
                aspect-ratio: 2 / 3;
                object-fit: cover;
                display: block;
                background: {BG};
            }}
            .cm-card-body {{
                padding: 0.65rem 0.8rem 0.85rem 0.8rem;
            }}
            .cm-card-title {{
                color: {TEXT};
                font-weight: 600;
                font-size: 0.92rem;
                line-height: 1.25;
                margin: 0 0 0.25rem 0;
                height: 2.4em;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }}
            .cm-card-meta {{
                color: {MUTED};
                font-size: 0.78rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.5rem;
            }}
            .cm-card-rating {{
                color: {ACCENT};
                font-weight: 600;
            }}
            .cm-card-genres {{
                color: {MUTED};
                font-size: 0.72rem;
                margin-top: 0.35rem;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
            }}
            .cm-card-sim {{
                color: {ACCENT};
                font-size: 0.72rem;
                font-weight: 600;
                margin-top: 0.3rem;
            }}

            /* ---------- Genre chips ---------- */
            .cm-chips {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }}
            .cm-chip {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 999px;
                padding: 0.4rem 0.9rem;
                color: {TEXT};
                font-size: 0.85rem;
                text-decoration: none;
            }}

            /* ---------- Hero ---------- */
            .cm-hero {{
                background: linear-gradient(135deg, #161B26 0%, {BG} 60%);
                border: 1px solid {BORDER};
                border-radius: 16px;
                padding: 2.5rem 2rem;
                text-align: center;
                margin-bottom: 1.5rem;
            }}
            .cm-hero h1 {{
                font-size: 3rem;
                font-weight: 800;
                letter-spacing: 0.3rem;
                background: linear-gradient(90deg, {ACCENT}, #FFD98E);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 0;
            }}
            .cm-hero p {{
                color: {MUTED};
                font-size: 1.05rem;
                margin-top: 0.5rem;
            }}

            /* ---------- Detail page ---------- */
            .cm-detail-title {{
                font-size: 2rem;
                font-weight: 800;
                color: {TEXT};
                margin: 0;
            }}
            .cm-detail-meta {{
                color: {MUTED};
                font-size: 0.95rem;
                margin: 0.4rem 0 1rem 0;
            }}
            .cm-detail-overview {{
                color: {TEXT};
                line-height: 1.65;
                font-size: 0.98rem;
            }}
            .cm-detail-kv {{
                color: {MUTED};
                font-size: 0.9rem;
                margin-top: 0.35rem;
            }}
            .cm-detail-kv b {{ color: {TEXT}; font-weight: 600; }}

            /* ---------- Empty states ---------- */
            .cm-empty {{
                background: {SURFACE};
                border: 1px dashed {BORDER};
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                color: {MUTED};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Small formatting helpers
# ---------------------------------------------------------------------
def _safe(value, default="—"):
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return value


def _year(value):
    v = _safe(value, "")
    if v == "":
        return ""
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return ""


def _rating(value):
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "—"


def _poster(row):
    url = row.get("poster_url")
    if isinstance(url, str) and url.strip():
        return url
    return PLACEHOLDER_SVG


def _genres_short(row, n=3):
    g = row.get("genres", "")
    if not isinstance(g, str) or not g.strip():
        return ""
    parts = [p for p in g.split("|") if p][:n]
    return " · ".join(parts)


# ---------------------------------------------------------------------
# Card rendering
# ---------------------------------------------------------------------
def _card_html(row):
    title = html.escape(str(_safe(row.get("title"), "Untitled")))
    year = _year(row.get("year"))
    rating = _rating(row.get("vote_average"))
    genres = html.escape(_genres_short(row, 3))
    poster = _poster(row)

    sim = row.get("similarity")
    sim_line = ""
    if sim is not None and not pd.isna(sim):
        sim_line = f'<div class="cm-card-sim">Similarity {float(sim):.2f}</div>'

    return f"""
    <div class="cm-card">
      <img src="{poster}" alt="{title}" loading="lazy"/>
      <div class="cm-card-body">
        <div class="cm-card-title">{title}</div>
        <div class="cm-card-meta">
          <span>{year or "—"}</span>
          <span class="cm-card-rating">★ {rating}</span>
        </div>
        <div class="cm-card-genres">{genres}</div>
        {sim_line}
      </div>
    </div>
    """


def render_movie_grid(df: pd.DataFrame, key_prefix: str,
                      cols: int = 5, on_click=None):
    """
    Render a grid of movie cards.

    Because Streamlit buttons cannot sit *inside* custom HTML, each card
    is rendered as HTML and a thin "Open" button sits below it. Clicking
    the button calls `on_click(movie_id)` if provided.
    """
    if df is None or df.empty:
        st.markdown(
            '<div class="cm-empty">No movies to show here yet.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = list(df.iterrows())
    for start in range(0, len(rows), cols):
        chunk = rows[start:start + cols]
        columns = st.columns(cols, gap="medium")
        for col, (idx, row) in zip(columns, chunk):
            with col:
                st.markdown(_card_html(row), unsafe_allow_html=True)
                if on_click is not None:
                    label = "Open →"
                    if st.button(label, key=f"{key_prefix}_{idx}",
                                 use_container_width=True):
                        on_click(int(row["id"]))


# ---------------------------------------------------------------------
# Section header
# ---------------------------------------------------------------------
def section(title: str, subtitle: str = ""):
    st.markdown(f'<div class="cm-section">{title}</div>',
                unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="cm-section-sub">{subtitle}</div>',
                    unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Brand header
# ---------------------------------------------------------------------
def brand_header():
    st.markdown('<div class="cm-brand">CINEMATCH</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="cm-tagline">Find your next favorite movie.</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------
def render_movie_detail(row, on_back=None):
    if on_back is not None:
        if st.button("← Back", key="detail_back"):
            on_back()
            st.rerun()

    poster_col, info_col = st.columns([1, 2.2], gap="large")

    with poster_col:
        st.markdown(
            f'<img src="{_poster(row)}" style="width:100%;border-radius:12px;"/>',
            unsafe_allow_html=True,
        )

    with info_col:
        title = html.escape(str(_safe(row.get("title"), "Untitled")))
        st.markdown(f'<div class="cm-detail-title">{title}</div>',
                    unsafe_allow_html=True)

        year = _year(row.get("year"))
        rating = _rating(row.get("vote_average"))
        votes = _safe(row.get("vote_count"), "—")
        try:
            votes = f"{int(float(votes)):,}"
        except (TypeError, ValueError):
            votes = "—"
        runtime = _safe(row.get("runtime"), "")
        try:
            runtime = f"{int(float(runtime))} min"
        except (TypeError, ValueError):
            runtime = ""

        meta_bits = [b for b in [year, f"★ {rating} ({votes} votes)", runtime] if b]
        st.markdown(
            f'<div class="cm-detail-meta">{" · ".join(meta_bits)}</div>',
            unsafe_allow_html=True,
        )

        genres = row.get("genres", "")
        if isinstance(genres, str) and genres.strip():
            st.markdown(
                f'<div class="cm-detail-kv"><b>Genres:</b> '
                f'{html.escape(genres.replace("|", ", "))}</div>',
                unsafe_allow_html=True,
            )

        director = _safe(row.get("director"), "")
        if director:
            st.markdown(
                f'<div class="cm-detail-kv"><b>Director:</b> '
                f'{html.escape(str(director))}</div>',
                unsafe_allow_html=True,
            )

        cast = row.get("cast", "")
        if isinstance(cast, str) and cast.strip():
            st.markdown(
                f'<div class="cm-detail-kv"><b>Cast:</b> '
                f'{html.escape(cast.replace("|", ", "))}</div>',
                unsafe_allow_html=True,
            )

        overview = _safe(row.get("overview"), "")
        if overview:
            st.markdown(
                f'<div class="cm-detail-overview" style="margin-top:1rem;">'
                f'{html.escape(str(overview))}</div>',
                unsafe_allow_html=True,
            )