"""
CineMatch -- Stage 8
Content-based movie recommender using TF-IDF + cosine similarity.
"""

from __future__ import annotations

import difflib
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parent
MOVIES_CSV = ROOT / "data" / "movies.csv"


@st.cache_data(show_spinner=False)
def load_movies() -> pd.DataFrame:
    if not MOVIES_CSV.exists():
        raise FileNotFoundError(
            f"{MOVIES_CSV} not found. Run `python build_dataset.py` first."
        )
    df = pd.read_csv(MOVIES_CSV)
    for col in ("vote_average", "vote_count", "popularity", "runtime", "year"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["title"] = df["title"].fillna("").astype(str)
    df["soup"] = df["soup"].fillna("").astype(str)
    return df


@st.cache_resource(show_spinner="Building TF-IDF matrix...")
def build_tfidf(_movies: pd.DataFrame):
    vectorizer = TfidfVectorizer(
        stop_words="english",
        min_df=2,
        max_df=0.85,
        sublinear_tf=True,
        ngram_range=(1, 1),
        dtype=np.float32,
    )
    matrix = vectorizer.fit_transform(_movies["soup"])
    return vectorizer, matrix


def get_index_by_title(title, movies):
    if not title or not title.strip():
        return None
    q = title.strip().lower()

    mask = movies["title"].str.lower() == q
    if mask.any():
        return int(movies.index[mask][0])

    if "original_title" in movies.columns:
        mask = movies["original_title"].fillna("").str.lower() == q
        if mask.any():
            return int(movies.index[mask][0])

    mask = movies["title"].str.lower().str.contains(q, regex=False, na=False)
    if mask.any():
        return int(movies.index[mask][0])

    if "original_title" in movies.columns:
        mask = movies["original_title"].fillna("").str.lower() \
                    .str.contains(q, regex=False, na=False)
        if mask.any():
            return int(movies.index[mask][0])

    titles_lower = movies["title"].str.lower().tolist()
    close = difflib.get_close_matches(q, titles_lower, n=1, cutoff=0.72)
    if close:
        mask = movies["title"].str.lower() == close[0]
        if mask.any():
            return int(movies.index[mask][0])

    return None


def search(query, movies, limit=30):
    if not query or not query.strip():
        return movies.iloc[0:0]
    q = query.strip().lower()

    def has(series):
        return series.fillna("").astype(str).str.lower() \
                     .str.contains(q, regex=False, na=False)

    rank = pd.Series(0, index=movies.index)
    rank = rank + has(movies["title"]).astype(int) * 3
    if "original_title" in movies.columns:
        rank = rank + has(movies["original_title"]).astype(int) * 2
    if "cast" in movies.columns:
        rank = rank + has(movies["cast"]).astype(int)
    if "director" in movies.columns:
        rank = rank + has(movies["director"]).astype(int)

    hits = movies[rank > 0].copy()
    if not hits.empty:
        hits["_rank"] = rank[rank > 0]
        hits = hits.sort_values(
            ["_rank", "vote_count"], ascending=[False, False]
        ).drop(columns="_rank")
        return hits.head(limit)

    titles_lower = movies["title"].str.lower().tolist()
    close = difflib.get_close_matches(q, titles_lower, n=limit, cutoff=0.60)
    if not close:
        return movies.iloc[0:0]

    order_map = {t: i for i, t in enumerate(close)}
    mask = movies["title"].str.lower().isin(close)
    fuz = movies[mask].copy()
    fuz["_fr"] = fuz["title"].str.lower().map(order_map)
    fuz = fuz.sort_values("_fr").drop(columns="_fr")
    return fuz.head(limit)


def recommend(movie_title, movies, tfidf_matrix, top_n=10, min_votes=50):
    idx = get_index_by_title(movie_title, movies)
    if idx is None:
        empty = movies.iloc[0:0].copy()
        empty["similarity"] = []
        return empty

    query_vec = tfidf_matrix[idx]
    scores = (tfidf_matrix @ query_vec.T).toarray().ravel()
    scores[idx] = 0.0

    if min_votes > 0 and "vote_count" in movies.columns:
        low_votes = movies["vote_count"].fillna(0).values < min_votes
        scores[low_votes] = 0.0

    k = min(top_n, len(scores) - 1)
    top_idx = np.argpartition(scores, -k)[-k:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

    result = movies.iloc[top_idx].copy()
    result["similarity"] = scores[top_idx]
    result = result[result["similarity"] > 0]
    return result.reset_index(drop=True)


def weighted_rating(movies, m_min_votes=None):
    df = movies.copy()
    C = df["vote_average"].mean()
    if m_min_votes is None:
        m_min_votes = int(df["vote_count"].quantile(0.80))
    v = df["vote_count"]
    R = df["vote_average"]
    df["weighted_rating"] = (v / (v + m_min_votes)) * R + \
                            (m_min_votes / (v + m_min_votes)) * C
    return df.sort_values("weighted_rating", ascending=False)