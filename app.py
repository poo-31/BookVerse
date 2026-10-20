
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="BookVerse Analytics",
    page_icon="📚",
    layout="wide"
)

# ---------- SAMPLE DATA ----------
def sample_data():
    return pd.DataFrame({
        "title": [
            "The Silent Patient", "Atomic Habits",
            "The Alchemist", "Educated", "1984",
            "Dune", "The Hobbit", "Sapiens",
            "Pride and Prejudice", "The Book Thief",
            "Deep Work", "It Ends with Us",
            "The Psychology of Money", "Ikigai",
            "The Great Gatsby", "The Midnight Library",
            "Harry Potter", "Little Women",
            "Thinking, Fast and Slow", "The Kite Runner"
        ],
        "authors": [
            "Alex Michaelides", "James Clear",
            "Paulo Coelho", "Tara Westover",
            "George Orwell", "Frank Herbert",
            "J.R.R. Tolkien", "Yuval Noah Harari",
            "Jane Austen", "Markus Zusak",
            "Cal Newport", "Colleen Hoover",
            "Morgan Housel", "Hector Garcia",
            "F. Scott Fitzgerald", "Matt Haig",
            "J.K. Rowling", "Louisa May Alcott",
            "Daniel Kahneman", "Khaled Hosseini"
        ],
        "genre": [
            "Thriller", "Self-help", "Fiction", "Memoir",
            "Dystopian", "Fantasy", "Fantasy", "History",
            "Romance", "Historical Fiction", "Productivity",
            "Romance", "Finance", "Self-help", "Classic",
            "Fantasy", "Fantasy", "Classic", "Psychology",
            "Fiction"
        ],
        "average_rating": [
            4.2, 4.3, 3.9, 4.5, 4.2, 4.3, 4.3, 4.4,
            4.3, 4.4, 4.2, 4.0, 4.2, 3.9, 3.9, 4.0,
            4.5, 4.1, 4.2, 4.3
        ],
        "ratings_count": [
            500000, 700000, 300000, 450000, 900000,
            600000, 850000, 650000, 800000, 500000,
            250000, 400000, 350000, 200000, 600000,
            300000, 1200000, 450000, 280000, 550000
        ],
        "publication_year": [
            2019, 2018, 1988, 2018, 1949, 1965, 1937,
            2011, 1813, 2005, 2016, 2016, 2020, 2016,
            1925, 2020, 1997, 1868, 2011, 2003
        ],
        "language": ["English"] * 20
    })


# ---------- DATA LOADING ----------
def prepare_data(data):
    data = data.copy()

    # Normalize common column names from book datasets.
    data.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in data.columns
    ]

    aliases = {
        "title": ["book_title", "original_title", "name"],
        "authors": ["author", "book_author"],
        "genre": ["genres", "category", "categories"],
        "average_rating": ["rating", "avg_rating"],
        "ratings_count": ["ratings", "work_ratings_count"],
        "publication_year": [
            "original_publication_year", "year", "published_year"
        ],
        "language": ["language_code", "lang"]
    }

    for standard, alternatives in aliases.items():
        if standard not in data.columns:
            for alt in alternatives:
                if alt in data.columns:
                    data = data.rename(columns={alt: standard})
                    break

    if "title" not in data.columns:
        raise ValueError("Your CSV needs a title or book_title column.")

    defaults = {
        "authors": "Unknown",
        "genre": "Unknown",
        "average_rating": 0,
        "ratings_count": 0,
        "publication_year": None,
        "language": "Unknown"
    }

    for column, default in defaults.items():
        if column not in data.columns:
            data[column] = default

    for column in ["average_rating", "ratings_count", "publication_year"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["title"] = data["title"].fillna("Untitled").astype(str)
    data["authors"] = data["authors"].fillna("Unknown").astype(str)
    data["genre"] = data["genre"].fillna("Unknown").astype(str)
    data["language"] = data["language"].fillna("Unknown").astype(str)
    data["average_rating"] = data["average_rating"].fillna(0)
    data["ratings_count"] = data["ratings_count"].fillna(0)

    # Keep usable years only.
    data.loc[
        ~data["publication_year"].between(1000, 2100),
        "publication_year"
    ] = None

    return data


# ---------- HEADER ----------
st.title("📚 BookVerse Analytics")
st.caption(
    "Explore book ratings, authors, genres and publication trends."
)

with st.sidebar:
    st.header("Data & Filters")
    uploaded_file = st.file_uploader(
        "Upload your book CSV",
        type=["csv"]
    )

try:
    if uploaded_file is not None:
        df = prepare_data(pd.read_csv(uploaded_file))
        st.sidebar.success("Your CSV is loaded.")
    else:
        df = sample_data()
        st.sidebar.info("Showing demonstration data.")
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()

# ---------- FILTERS ----------
with st.sidebar:
    genre_options = sorted(df["genre"].unique().tolist())
    selected_genres = st.multiselect(
        "Genre",
        genre_options,
        default=genre_options
    )

    min_rating = st.slider(
        "Minimum average rating",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.1
    )

    search = st.text_input("Search title or author")

filtered = df[
    df["genre"].isin(selected_genres)
    & (df["average_rating"] >= min_rating)
].copy()

if search.strip():
    match = (
        filtered["title"].str.contains(search, case=False, na=False)
        | filtered["authors"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[match]

# ---------- KPI CARDS ----------
total_books = len(filtered)
avg_rating = (
    filtered["average_rating"].mean() if total_books else 0
)
total_ratings = filtered["ratings_count"].sum()
total_authors = filtered["authors"].nunique()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Books", f"{total_books:,}")
c2.metric("Average Rating", f"{avg_rating:.2f} / 5")
c3.metric("Total Ratings", f"{total_ratings:,.0f}")
c4.metric("Unique Authors", f"{total_authors:,}")

st.divider()

if filtered.empty:
    st.warning("No books match these filters. Try changing them.")
    st.stop()

# ---------- CHARTS ----------
left, right = st.columns(2)

with left:
    st.subheader("Books by Genre")
    genre_counts = (
        filtered.groupby("genre")
        .size()
        .reset_index(name="books")
        .sort_values("books", ascending=False)
    )
    fig_genre = px.bar(
        genre_counts,
        x="genre",
        y="books",
        color="books",
        title="Number of Books in Each Genre",
        labels={"genre": "Genre", "books": "Number of Books"}
    )
    fig_genre.update_layout(
        showlegend=False,
        xaxis_title=None
    )
    st.plotly_chart(fig_genre, use_container_width=True)

with right:
    st.subheader("Rating Distribution")
    fig_rating = px.histogram(
        filtered,
        x="average_rating",
        nbins=15,
        title="Distribution of Average Book Ratings",
        labels={"average_rating": "Average Rating"}
    )
    st.plotly_chart(fig_rating, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Publication Trends")
    yearly = (
        filtered.dropna(subset=["publication_year"])
        .groupby("publication_year")
        .size()
        .reset_index(name="books")
        .sort_values("publication_year")
    )
    if not yearly.empty:
        fig_year = px.line(
            yearly,
            x="publication_year",
            y="books",
            markers=True,
            title="Books Published by Year"
        )
        st.plotly_chart(fig_year, use_container_width=True)
    else:
        st.info("Publication-year data is unavailable.")

with right:
    st.subheader("Ratings vs Popularity")
    fig_scatter = px.scatter(
        filtered,
        x="ratings_count",
        y="average_rating",
        hover_name="title",
        color="genre",
        title="Popularity and Average Rating",
        labels={
            "ratings_count": "Number of Ratings",
            "average_rating": "Average Rating"
        }
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ---------- BOOK EXPLORER ----------
st.divider()
st.header("🔎 Explore Books")

sort_by = st.selectbox(
    "Sort books by",
    ["average_rating", "ratings_count", "publication_year", "title"]
)

ascending = sort_by in ["title", "publication_year"]

book_table = filtered.sort_values(
    sort_by,
    ascending=ascending,
    na_position="last"
)

st.dataframe(
    book_table[
        [
            "title", "authors", "genre", "average_rating",
            "ratings_count", "publication_year", "language"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

csv_data = book_table.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered books as CSV",
    data=csv_data,
    file_name="bookverse_filtered_books.csv",
    mime="text/csv"
)

# ---------- BASIC RECOMMENDATIONS ----------
st.divider()
st.header("✨ Discover a Book")

preferred_genre = st.selectbox(
    "Choose a genre for recommendations",
    sorted(df["genre"].unique())
)

recommendations = df[
    (df["genre"] == preferred_genre)
    & (df["average_rating"] >= 4.0)
].sort_values(
    ["average_rating", "ratings_count"],
    ascending=False
).head(5)

if recommendations.empty:
    st.info("No books match this genre and rating. Try another genre.")
else:
    st.caption(
        "Books with a rating of at least 4.0, ranked by rating "
        "and then popularity. This is a rule-based recommendation, "
        "not a trained AI model."
    )
    st.dataframe(
        recommendations[
            ["title", "authors", "genre", "average_rating", "ratings_count"]
        ],
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "BookVerse Analytics | Demonstration data is illustrative. "
    "Upload a real dataset for meaningful analysis."
)

