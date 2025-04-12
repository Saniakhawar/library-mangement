
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
import plotly.express as px
from streamlit_lottie import st_lottie
import requests

st.set_page_config(
    page_title="Personal Library Management System",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

if 'library' not in st.session_state:
    st.session_state.library = []

if 'search_results' not in st.session_state:
    st.session_state.search_results = []

if 'book_added' not in st.session_state:
    st.session_state.book_added = False

if 'book_removed' not in st.session_state:
    st.session_state.book_removed = False

if 'current_view' not in st.session_state:
    st.session_state.current_view = "library"

def load_library():
    try:
        if os.path.exists('library.json'):
            with open('library.json', 'r') as file:
                st.session_state.library = json.load(file)
            return True
        return False
    except Exception as e:
        st.error(f"Error Loading Library: {e}")
        return False

def save_library():
    try:
        with open('library.json', 'w') as file:
            json.dump(st.session_state.library, file)
        return True
    except Exception as e:
        st.error(f"Error Saving Library: {e}")
        return False

def add_book(title, author, publication_year, genre, read_status):
    book = {
        "title": title,
        "author": author,
        "publication_year": publication_year,
        "genre": genre,
        "read_status": read_status,
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.library.append(book)
    save_library()
    st.session_state.book_added = True
    time.sleep(0.5)

def remove_book(index):
    if 0 <= index < len(st.session_state.library):
        del st.session_state.library[index]
        save_library()
        st.session_state.book_removed = True
        return True
    return False

def search_books(search_term, search_by):
    search_term = search_term.lower()
    results = []
    for book in st.session_state.library:
        if search_by == "Title" and search_term in book["title"].lower():
            results.append(book)
        elif search_by == "Author" and search_term in book["author"].lower():
            results.append(book)
        elif search_by == "Genre" and search_term in book["genre"].lower():
            results.append(book)
    st.session_state.search_results = results

def get_library_stats():
    total_books = len(st.session_state.library)
    read_books = sum(1 for book in st.session_state.library if book["read_status"])
    percent_read = (read_books / total_books) * 100 if total_books > 0 else 0
    genres, authors, decades = {}, {}, {}

    for book in st.session_state.library:
        genres[book["genre"]] = genres.get(book["genre"], 0) + 1
        authors[book["author"]] = authors.get(book["author"], 0) + 1
        decade = (int(book['publication_year']) // 10) * 10
        decades[decade] = decades.get(decade, 0) + 1

    return {
        "total_books": total_books,
        "read_books": read_books,
        "percent_read": percent_read,
        "genres": dict(sorted(genres.items(), key=lambda x: x[1], reverse=True)),
        "authors": dict(sorted(authors.items(), key=lambda x: x[1], reverse=True)),
        "decades": dict(sorted(decades.items(), key=lambda x: x[1], reverse=True))
    }

def create_visualizations(stats):
    if stats['genres']:
        genres_df = pd.DataFrame({"Genre": list(stats['genres'].keys()), "Count": list(stats['genres'].values())})
        fig_genres = px.bar(genres_df, x="Genre", y="Count", color="Count", title="Top Genres")
        st.plotly_chart(fig_genres, use_container_width=True)

    if stats['decades']:
        decades_df = pd.DataFrame({"Decade": [f"{d}s" for d in stats['decades'].keys()], "Count": list(stats['decades'].values())})
        fig_decades = px.line(decades_df, x="Decade", y="Count", markers=True, title="Books by Publication Decade")
        st.plotly_chart(fig_decades, use_container_width=True)

load_library()

st.sidebar.title("Navigation")
nav_option = st.sidebar.radio("Choose an option", ["View Library", "Add Book", "Search Books", "Library Statistics"])
st.session_state.current_view = nav_option

st.title("📚 Personal Library Manager")

if st.session_state.current_view == "Add Book":
    with st.form("add_book_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Book Title")
            author = st.text_input("Book Author")
            publication_year = st.number_input("Publication Year", min_value=1000, max_value=datetime.now().year, step=1, value=2023)
        with col2:
            genre = st.selectbox("Genre", ["Fiction", "Non-Fiction", "Science", "Technology"])
            read_status = st.radio("Read Status", ["Read", "Unread"], horizontal=True)
        submitted = st.form_submit_button("Add Book")
        if submitted and title and author:
            add_book(title, author, publication_year, genre, read_status == "Read")
            st.success("Book added successfully!")
            st.balloons()

elif st.session_state.current_view == "View Library":
    st.subheader("Your Library")
    if not st.session_state.library:
        st.warning("Your library is empty!")
    else:
        for i, book in enumerate(st.session_state.library):
            with st.container():
                st.markdown(f"**{book['title']}** by {book['author']} ({book['publication_year']})")
                st.markdown(f"*Genre:* {book['genre']}, *Status:* {'Read' if book['read_status'] else 'Unread'}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Remove", key=f"remove_{i}"):
                        if remove_book(i):
                            st.rerun()
                with col2:
                    new_status = not book['read_status']
                    label = "Mark as Read" if not book['read_status'] else "Mark as Unread"
                    if st.button(label, key=f"toggle_{i}"):
                        st.session_state.library[i]['read_status'] = new_status
                        save_library()
                        st.rerun()

elif st.session_state.current_view == "Search Books":
    st.subheader("Search Books")
    search_by = st.selectbox("Search by", ["Title", "Author", "Genre"])
    search_term = st.text_input("Enter search term")
    if st.button("Search"):
        if search_term:
            search_books(search_term, search_by)
    if st.session_state.search_results:
        st.write(f"Found {len(st.session_state.search_results)} result(s):")
        for book in st.session_state.search_results:
            st.markdown(f"**{book['title']}** by {book['author']} ({book['publication_year']})")
            st.markdown(f"*Genre:* {book['genre']}, *Status:* {'Read' if book['read_status'] else 'Unread'}")
    elif search_term:
        st.warning("No results found.")

elif st.session_state.current_view == "Library Statistics":
    st.subheader("Library Statistics")
    if not st.session_state.library:
        st.warning("No books in library. Add some to see statistics.")
    else:
        stats = get_library_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Books", stats['total_books'])
        with col2:
            st.metric("Read Books", stats['read_books'])
        with col3:
            st.metric("% Read", f"{stats['percent_read']:.1f}%")
        create_visualizations(stats)

st.markdown("---")
st.caption("Copyright © 2025 Sania Khawar | Personal Library Manager")
