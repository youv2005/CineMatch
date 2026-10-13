"""
CineMatch -- Stage 9
Main application: navigation + pages + wiring to the recommender.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import ui
from recommender import (
    build_tfidf,
    get_index_by_title,
    load_movies,
    recommend,
    search,
    weighted_rating,
)

st.set_page_config(
    page_title="CineMatch",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ui.inject_css()


def _init_state():
    defaults = {
        "page": "Home",
        "selected_movie_id": None,
        "watchlist": set(),
        "watched": set(),
        "home_search": "",
        "genre_filter": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


_init_state()

try:
    movies = load_movies()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

_, tfidf_matrix = build_tfidf(movies)


def movie_by_id(mid):
    hit = movies[movies["id"] == mid]
    return hit.iloc[0] if not hit.empty else None


def open_detail(mid):
    st.session_state["selected_movie_id"] = int(mid)
    st.session_state["page"] = "Detail"


def back_from_detail():
    st.session_state["selected_movie_id"] = None
    st.session_state["page"] = "Home"


def add_to_watchlist(mid):
    st.session_state["watchlist"].add(int(mid))


def remove_from_watchlist(mid):
    st.session_state["watchlist"].discard(int(mid))


def mark_watched(mid):
    st.session_state["watched"].add(int(mid))


def unmark_watched(mid):
    st.session_state["watched"].discard(int(mid))


PAGES = ["Home", "Explore", "Genres", "Watchlist", "Watched", "About"]

ui.brand_header()

if st.session_state["page"] != "Detail":
    cur = st.session_state["page"]
    idx = PAGES.index(cur) if cur in PAGES else 0
    nav = st.radio("Navigation", PAGES, index=idx,
                   horizontal=True, label_visibility="collapsed",
                   key="nav_radio")
    if nav != cur:
        st.session_state["page"] = nav
        st.session_state["selected_movie_id"] = None
        st.rerun()
def render_home():
    st.markdown(
        """
        <div class="cm-hero">
          <h1>CINEMATCH</h1>
          <p>Find your next favorite movie.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    q = st.text_input(
        "Search movies, actors, directors...",
        placeholder="Try Interstellar, Nolan, or Tom Hardy",
        label_visibility="collapsed",
        key="home_search_input",
    )

    if q and q.strip():
        results = search(q, movies, limit=30)
        if results.empty:
            st.warning("No matches for " + q + ". Try another title, actor, or director.")
        else:
            ui.section("Search results for " + q, str(len(results)) + " matches")
            ui.render_movie_grid(results, key_prefix="search",
                                 cols=5, on_click=open_detail)
        return

    ui.section("Popular Movies", "Most popular on TMDB")
    pop = movies.dropna(subset=["popularity"]) \
               .sort_values("popularity", ascending=False).head(10)
    ui.render_movie_grid(pop, key_prefix="pop", cols=5, on_click=open_detail)

    ui.section("Top Rated", "Weighted rating (vote-count adjusted)")
    top = weighted_rating(movies).head(10)
    ui.render_movie_grid(top, key_prefix="top", cols=5, on_click=open_detail)

    ui.section("Recent Releases", "Newest in the dataset")
    recent = movies.dropna(subset=["year"]) \
                  .query("year >= 2015") \
                  .sort_values("release_date", ascending=False).head(10)
    ui.render_movie_grid(recent, key_prefix="recent",
                         cols=5, on_click=open_detail)

    ui.section("Explore Genres", "Click a genre to browse")
    genres = [
        "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
        "Drama", "Family", "Fantasy", "Horror", "Mystery", "Romance",
        "Science Fiction", "Thriller", "War", "Western",
    ]
    chip_cols = st.columns(8)
    for i, g in enumerate(genres):
        with chip_cols[i % 8]:
            if st.button(g, key="chip_" + g, use_container_width=True):
                st.session_state["genre_filter"] = g
                st.session_state["page"] = "Genres"
                st.rerun()

    ui.section("AI Movie Recommendations",
               "Pick a movie you love, get content-similar films")
    rec_q = st.text_input(
        "Choose a movie you love",
        placeholder="e.g. Interstellar",
        label_visibility="collapsed",
        key="rec_query_input",
    )
    col_a, col_b = st.columns([1, 4])
    with col_a:
        go = st.button("Get Recommendations", type="primary",
                       use_container_width=True)
    with col_b:
        min_votes = st.slider("Minimum votes", 0, 5000, 200, step=50)

    if go:
        if not rec_q.strip():
            st.warning("Type a movie title first.")
        else:
            idx = get_index_by_title(rec_q, movies)
            if idx is None:
                st.error("Could not find " + rec_q + " in the dataset.")
            else:
                picked = movies.iloc[idx]
                yr = picked["year"]
                yr_str = str(int(yr)) if pd.notna(yr) else "-"
                st.success("Because you liked " + str(picked["title"]) +
                           " (" + yr_str + "):")
                recs = recommend(rec_q, movies, tfidf_matrix,
                                 top_n=10, min_votes=min_votes)
                if recs.empty:
                    st.info("No sufficiently-similar movies above the vote threshold.")
                else:
                    ui.render_movie_grid(recs, key_prefix="rec",
                                         cols=5, on_click=open_detail)

ALL_GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "TV Movie", "Thriller", "War", "Western",
]


def render_explore():
    ui.section("Explore Movies", "Filter and sort 45,000+ movies")

    with st.expander("Filters and sorting", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            genre = st.selectbox("Genre", ["Any"] + ALL_GENRES)
            min_rating = st.slider("Minimum rating", 0.0, 10.0, 0.0, 0.1)
        with col2:
            year_min, year_max = st.slider(
                "Release year", 1900, 2030, (1950, 2030), step=1)
            min_votes = st.number_input("Minimum votes", 0, 50000, 0, step=50)
        with col3:
            languages = sorted(
                [l for l in movies["original_language"].dropna().unique()
                 if isinstance(l, str) and l.strip()])
            lang = st.selectbox("Language", ["Any"] + languages)
            sort_by = st.selectbox(
                "Sort by",
                ["Popularity", "Rating", "Release date", "Votes", "Title"])

    df = movies.copy()
    if genre != "Any":
        df = df[df["genres"].fillna("").str.contains(genre, regex=False)]
    df = df[df["vote_average"].fillna(0) >= min_rating]
    df = df[df["vote_count"].fillna(0) >= min_votes]
    if "year" in df.columns:
        df = df[(df["year"].fillna(0) >= year_min) &
                (df["year"].fillna(0) <= year_max)]
    if lang != "Any":
        df = df[df["original_language"] == lang]

    sort_map = {
        "Popularity": ("popularity", False),
        "Rating": ("vote_average", False),
        "Release date": ("release_date", False),
        "Votes": ("vote_count", False),
        "Title": ("title", True),
    }
    col, asc = sort_map[sort_by]
    df = df.dropna(subset=[col]).sort_values(col, ascending=asc)

    st.caption(str(len(df)) + " movies match your filters.")
    ui.render_movie_grid(df.head(40), key_prefix="explore",
                         cols=5, on_click=open_detail)


def render_genres():
    ui.section("Browse by Genre", "Click a genre to see movies")
    current = st.session_state.get("genre_filter")

    chip_cols = st.columns(8)
    for i, g in enumerate(ALL_GENRES):
        with chip_cols[i % 8]:
            label = ("* " + g) if g == current else g
            if st.button(label, key="gen_" + g, use_container_width=True):
                st.session_state["genre_filter"] = None if g == current else g
                st.rerun()

    if not current:
        st.info("Select a genre above to browse.")
        return

    df = movies[movies["genres"].fillna("").str.contains(current, regex=False)]
    df = df.sort_values(["vote_count", "vote_average"],
                        ascending=[False, False])
    ui.section(current, str(len(df)) + " movies")
    ui.render_movie_grid(df.head(40), key_prefix="gen_" + current,
                         cols=5, on_click=open_detail)


def render_watchlist():
    ui.section("My Watchlist", "Movies you have saved")
    ids = st.session_state["watchlist"]
    if not ids:
        st.markdown(
            '<div class="cm-empty">Your watchlist is empty. '
            'Open a movie and click Add to Watchlist.</div>',
            unsafe_allow_html=True)
        return
    df = movies[movies["id"].isin(ids)]
    ui.render_movie_grid(df, key_prefix="watch", cols=5, on_click=open_detail)


def render_watched():
    ui.section("Watched", "Movies you have marked as seen")
    ids = st.session_state["watched"]
    if not ids:
        st.markdown(
            '<div class="cm-empty">Nothing marked watched yet.</div>',
            unsafe_allow_html=True)
        return
    df = movies[movies["id"].isin(ids)]
    ui.render_movie_grid(df, key_prefix="seen", cols=5, on_click=open_detail)


def render_about():
    ui.section("About CineMatch",
               "Movie discovery plus content-based recommendation")
    st.markdown(
        "### What is this?\n\n"
        "CineMatch is a movie discovery website built with **Python** and "
        "**Streamlit**, powered by a content-based recommendation engine.\n\n"
        "### Technology\n\n"
        "| Layer | Tool |\n"
        "|---|---|\n"
        "| Data | pandas, numpy |\n"
        "| ML | scikit-learn: TF-IDF vectorizer, cosine similarity |\n"
        "| UI | Streamlit plus custom CSS |\n"
        "| Data source | TMDB The Movies Dataset (45,000+ real movies) |\n\n"
        "### How the recommender works\n\n"
        "```\n"
        "Movie metadata  (genres, overview, keywords, cast, director)\n"
        "        |\n"
        "Preprocessing   (lowercase, tokenise, squash multi-word names)\n"
        "        |\n"
        "Feature combination  ->  one text soup per movie\n"
        "        |\n"
        "TF-IDF vectorization  ->  sparse document-term matrix\n"
        "        |\n"
        "Cosine similarity  ->  score against a chosen movie\n"
        "        |\n"
        "Top-K recommendations  (filtered by minimum votes)\n"
        "```\n\n"
        "### Honest limitations\n\n"
        "- **Content-based only.** No collaborative filtering, so we "
        "cannot infer taste from other users.\n"
        "- **Vocabulary mismatch.** A film tagged Sci-Fi won't match one "
        "tagged Science Fiction unless they share other tokens.\n"
        "- **Popularity bias.** Mainstream films have richer metadata "
        "and therefore match more things."
    )


def render_detail():
    mid = st.session_state.get("selected_movie_id")
    if mid is None:
        st.session_state["page"] = "Home"
        st.rerun()
        return

    row = movie_by_id(mid)
    if row is None:
        st.error("Movie not found.")
        if st.button("Back"):
            back_from_detail()
            st.rerun()
        return

    ui.render_movie_detail(row, on_back=back_from_detail)

    c1, c2 = st.columns(2)
    in_watch = mid in st.session_state["watchlist"]
    is_seen = mid in st.session_state["watched"]

    with c1:
        if in_watch:
            if st.button("In Watchlist (remove)", use_container_width=True):
                remove_from_watchlist(mid)
                st.rerun()
        else:
            if st.button("Add to Watchlist", type="primary",
                         use_container_width=True):
                add_to_watchlist(mid)
                st.rerun()

    with c2:
        if is_seen:
            if st.button("Watched (unmark)", use_container_width=True):
                unmark_watched(mid)
                st.rerun()
        else:
            if st.button("Mark Watched", use_container_width=True):
                mark_watched(mid)
                st.rerun()

    ui.section("Similar Movies", "Generated by TF-IDF plus cosine similarity")
    recs = recommend(row["title"], movies, tfidf_matrix,
                     top_n=10, min_votes=100)
    if recs.empty:
        st.info("No similar movies found above the vote threshold.")
    else:
        ui.render_movie_grid(recs, key_prefix="detail_rec",
                             cols=5, on_click=open_detail)


page = st.session_state["page"]
if page == "Home":
    render_home()
elif page == "Explore":
    render_explore()
elif page == "Genres":
    render_genres()
elif page == "Watchlist":
    render_watchlist()
elif page == "Watched":
    render_watched()
elif page == "About":
    render_about()
elif page == "Detail":
    render_detail()
else:
    st.error("Unknown page: " + str(page))
