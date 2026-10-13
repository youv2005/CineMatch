"""
CineMatch -- Stage 5
Build data/movies.csv from the raw Kaggle files.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "movies.csv"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"


def parse_list(raw):
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []


def extract_genres(raw):
    return [d["name"] for d in parse_list(raw)
            if isinstance(d, dict) and d.get("name")]


def extract_keywords(raw):
    return [d["name"] for d in parse_list(raw)
            if isinstance(d, dict) and d.get("name")]


def extract_top_cast(raw, n=5):
    items = parse_list(raw)
    items = sorted(items, key=lambda d: d.get("order", 999)) if items else []
    return [d["name"] for d in items[:n]
            if isinstance(d, dict) and d.get("name")]


def extract_director(raw):
    for d in parse_list(raw):
        if isinstance(d, dict) and d.get("job") == "Director":
            return d.get("name", "")
    return ""


def collapse(text):
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def clean_overview(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def to_pipe(names):
    return "|".join(str(n) for n in names) if isinstance(names, list) else ""


def main():
    print("Reading raw files ...")
    movies = pd.read_csv(RAW / "movies_metadata.csv",
                         dtype={"id": str}, low_memory=False)
    credits = pd.read_csv(RAW / "credits.csv", dtype={"id": str})
    keywords = pd.read_csv(RAW / "keywords.csv", dtype={"id": str})
    print(f"   movies_metadata : {len(movies):,} rows")
    print(f"   credits         : {len(credits):,} rows")
    print(f"   keywords        : {len(keywords):,} rows")

    def clean_id(df):
        df["id"] = pd.to_numeric(df["id"], errors="coerce")
        df = df.dropna(subset=["id"]).copy()
        df["id"] = df["id"].astype("int64")
        return df.drop_duplicates(subset=["id"], keep="first")

    movies = clean_id(movies)
    credits = clean_id(credits)
    keywords = clean_id(keywords)
    print(f"   movies after id cleaning : {len(movies):,} rows")

    print("Parsing genres / cast / director / keywords ...")
    movies["genres_list"] = movies["genres"].apply(extract_genres)
    credits["cast_list"] = credits["cast"].apply(extract_top_cast)
    credits["director"] = credits["crew"].apply(extract_director)
    keywords["keywords_list"] = keywords["keywords"].apply(extract_keywords)

    movies = movies.merge(
        credits[["id", "cast_list", "director"]], on="id", how="left")
    movies = movies.merge(
        keywords[["id", "keywords_list"]], on="id", how="left")

    movies["genres"]   = movies["genres_list"].apply(to_pipe)
    movies["cast"]     = movies["cast_list"].apply(to_pipe)
    movies["keywords"] = movies["keywords_list"].apply(to_pipe)
    movies["director"] = movies["director"].fillna("")

    movies["release_date"] = pd.to_datetime(
        movies["release_date"], errors="coerce")
    movies["year"] = movies["release_date"].dt.year
    movies["vote_average"] = pd.to_numeric(
        movies["vote_average"], errors="coerce").fillna(0.0)
    movies["vote_count"] = pd.to_numeric(
        movies["vote_count"], errors="coerce").fillna(0).astype("int64")
    movies["popularity"] = pd.to_numeric(
        movies["popularity"], errors="coerce").fillna(0.0)
    movies["runtime"] = pd.to_numeric(
        movies["runtime"], errors="coerce").fillna(0.0)

    movies["poster_path"] = movies["poster_path"].fillna("")
    movies["poster_url"] = movies["poster_path"].apply(
        lambda p: f"{POSTER_BASE}{p}" if p else "")

    movies["overview"] = movies["overview"].fillna("")
    movies["overview_clean"] = movies["overview"].apply(clean_overview)

    # -----------------------------------------------------------------
    # build_soup:
    #   - genres are separate tokens (NOT fused) so 'science fiction'
    #     and 'adventure' can match across movies
    #   - each field is repeated a few times to give it real weight
    #     against the long natural-language overview
    # -----------------------------------------------------------------
    def build_soup(row):
        parts = []

        if row["genres"]:
            tokens = [collapse(g) for g in row["genres"].split("|") if g]
            parts.append(" ".join(tokens * 5))

        if row["director"]:
            d = collapse(row["director"])
            parts.append(" ".join([d] * 4))

        if row["cast"]:
            tokens = [collapse(c) for c in row["cast"].split("|") if c]
            parts.append(" ".join(tokens * 3))

        if row["keywords"]:
            tokens = [collapse(k) for k in row["keywords"].split("|") if k]
            parts.append(" ".join(tokens * 3))

        if row["overview_clean"]:
            parts.append(row["overview_clean"])

        return " ".join(parts).strip()

    print("Building TF-IDF text ('soup') for each movie ...")
    movies["soup"] = movies.apply(build_soup, axis=1)

    if "original_language" not in movies.columns:
        movies["original_language"] = ""
    movies["original_language"] = movies["original_language"].fillna("")

    keep = [
        "id", "title", "original_title", "overview", "genres",
        "keywords", "cast", "director",
        "vote_average", "vote_count", "popularity",
        "release_date", "year", "original_language", "runtime",
        "poster_url", "soup",
    ]
    out = movies[[c for c in keep if c in movies.columns]].copy()
    out = out[out["title"].notna() & (out["title"].astype(str).str.strip() != "")]
    out = out[out["soup"].str.len() > 0]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print()
    print(f"Wrote {len(out):,} movies -> {OUT}")
    print()
    print("Sample rows:")
    print(out[["title", "year", "vote_average", "director"]].head(8).to_string(index=False))


if __name__ == "__main__":
    main()