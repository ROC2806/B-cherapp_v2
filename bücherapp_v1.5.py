import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
from pathlib import Path
from PIL import Image
import uuid

# Mongo-Funktionen importieren
from mongo_2 import load_data, save_data, delete_wishlist_entry

# ----------------------------
# Initialisierung & Laden
# ----------------------------
data = load_data()
image = Image.open("logo.png")

# ----------------------------
# Sidebar & Navigation
# ----------------------------
with st.sidebar:
    st.title("Bücher App")
    st.image(image, width=120)
    st.markdown("---")

    page = option_menu(
        menu_title="Navigation",
        options=["Wunschliste", "Übersicht", "Details", "Statistik"],
        icons=["heart", "book", "search", "bar-chart"],
        default_index=0,
    )

    st.markdown("---")
    st.markdown("© **ROC**, 2025")

# ----------------------------
# Wunschliste
# ----------------------------
if page == "Wunschliste":
    st.header("Wunschliste")
    with st.form("add_wish"):
        title = st.text_input("Buchtitel")
        author = st.text_input("Autor")
        genre = st.selectbox("Genre auswählen oder eingeben", options=[
            "Roman", "Krimi & Thriller", "Fantasy & Science-Fiction", "Historisch", "Liebesgeschichte",
            "Abenteuer", "Horror & Mystery", "Biografie & Memoiren", "Sachbuch", "Ratgeber",
            "Kinder- & Jugendbuch", "Poesie & Kurzgeschichten", "Gesellschaft & Politik",
            "Spiritualität & Religion", "Klassiker", "Anderes"
        ])
        nationality = st.text_input("Nationalität des Autors")
        submit = st.form_submit_button("Zur Wunschliste hinzufügen")

        if submit and title:
            new_book = {
                "_id": str(uuid.uuid4()),
                "Titel": title,
                "Autor": author,
                "Genre": genre,
                "Wunschdatum": datetime.now().strftime("%Y-%m-%d"),
                "Status": "offen",
                "Nationalität": nationality
            }
            data["wishlist"].append(new_book)
            save_data(data)
            st.success("Buch hinzugefügt!")
            st.rerun()

    st.subheader("Deine Wunschliste")
    for i, book in enumerate(data["wishlist"]):
        st.markdown(f"**{book['Titel']}** von {book['Autor']} ({book['Genre']})")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            erhalten_durch = st.selectbox(
                "Erhalten durch",
                ["-", "gekauft", "ausgeliehen"],
                key=f"erhalten_{book['_id']}",
                label_visibility="collapsed"
            )

        with col2:
            if erhalten_durch != "-" and st.button("✅ Übernehmen", key=f"uebernehmen_{book['_id']}"):
                book["Status"] = "erledigt"
                book["Erhalten durch"] = erhalten_durch
                delete_wishlist_entry(book["_id"])
                data["read_books"].append(book)
                save_data(data)
                st.success("Buch hinzugefügt!")
                st.rerun()

        with col3:
            if st.button("🗑️ Entfernen", key=f"entfernen_{book['_id']}"):
                delete_wishlist_entry(book["_id"])
                st.success("Buch entfernt!")
                st.rerun()

# ----------------------------
# Übersicht
# ----------------------------
elif page == "Übersicht":
    st.header("Übersicht")

    df = pd.DataFrame(data["read_books"])

    if df.empty:
        st.info("Noch keine Bücher gekauft oder gelesen.")
    else:
        st.subheader("Buch filtern")

        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("Titel oder Autor suchen")

        all_genres = df["Genre"].dropna().unique()
        all_authors = df["Autor"].dropna().unique()

        with col2:
            selected_author = st.selectbox("Autor filtern", options=["Alle"] + list(all_authors))

        with col3:
            if selected_author != "Alle":
                genre_options = ["Alle"] + list(df[df["Autor"] == selected_author]["Genre"].unique())
            else:
                genre_options = ["Alle"] + list(all_genres)
            selected_genre = st.selectbox("Genre filtern", options=genre_options)

        # Nationalität-Filter
        all_nationalities = df["Nationalität"].dropna().unique()

        col_dfrom, col_dto, col_nat = st.columns(3)
        date_from = col_dfrom.date_input("Gelesen ab", value=None, key="date_from")
        date_to = col_dto.date_input("Gelesen bis", value=None, key="date_to")
        selected_nationality = col_nat.selectbox("Nationalität filtern", options=["Alle"] + list(all_nationalities))

        filtered_df = df.copy()

        if search:
            filtered_df = filtered_df[
                filtered_df["Titel"].str.contains(search, case=False) |
                filtered_df["Autor"].str.contains(search, case=False)
            ]
        if selected_author != "Alle":
            filtered_df = filtered_df[filtered_df["Autor"] == selected_author]
        if selected_genre != "Alle":
            filtered_df = filtered_df[filtered_df["Genre"] == selected_genre]

        if selected_nationality != "Alle":
            filtered_df = filtered_df[filtered_df["Nationalität"] == selected_nationality]

        if date_from and date_to:
            def match_date_range(entry):
                try:
                    if isinstance(entry, list):
                        return any(date_from <= datetime.strptime(d, "%Y-%m-%d").date() <= date_to for d in entry)
                    elif isinstance(entry, str):
                        d = datetime.strptime(entry, "%Y-%m-%d").date()
                        return date_from <= d <= date_to
                except:
                    return False
                return False
            filtered_df = filtered_df[filtered_df["Gelesen am"].apply(match_date_range)]
        st.markdown("---")
        st.markdown(f"##### Gefundene Bücher: {len(filtered_df)}")

        if "Gelesen am" in filtered_df.columns:
            filtered_df["Gelesen am (Mehrfach)"] = filtered_df["Gelesen am"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x) if pd.notnull(x) else "-"
            )
        else:
             filtered_df["Gelesen am (Mehrfach)"] = "-"

        st.dataframe(
            filtered_df[["Titel", "Autor", "Genre", "Erhalten durch", "Gelesen am (Mehrfach)", "Nationalität"]].fillna("-"),
            use_container_width=True
        )

# ----------------------------
# Details
# ----------------------------
elif page == "Details":
    st.header("Details")

    if not data["read_books"]:
        st.warning("Bitte zuerst Bücher als gekauft markieren.")
    else:
        df_details = pd.DataFrame(data["read_books"])

        st.subheader("Buch filtern")
        col1, col2 = st.columns(2)

        with col1:
            selected_author = st.selectbox("Autor auswählen", ["Alle"] + sorted(df_details["Autor"].dropna().unique().tolist()))

        with col2:
            if selected_author != "Alle":
                titles = df_details[df_details["Autor"] == selected_author]["Titel"].unique()
            else:
                titles = df_details["Titel"].unique()
            selected_title = st.selectbox("Titel auswählen", ["Alle"] + sorted(titles))

        filtered_books = data["read_books"]
        if selected_author != "Alle":
            filtered_books = [b for b in filtered_books if b["Autor"] == selected_author]
        if selected_title != "Alle":
            filtered_books = [b for b in filtered_books if b["Titel"] == selected_title]

        st.markdown("---")

        if not filtered_books:
            st.info("Keine Bücher mit diesen Filtern gefunden.")
        else:
            st.subheader("Details")
            for book in filtered_books:
                with st.expander(f"{book['Titel']} von {book['Autor']}"):
                    gelesen_am = st.date_input(
                        f"Gelesen am ({book['Titel']})",
                        value=datetime.today(),
                        key=f"date_{book['_id']}"
                    )
                    if st.button(f"💾 Speichern (Gelesen am) für {book['Titel']}", key=f"save_date_{book['_id']}"):
                        new_date = gelesen_am.strftime("%Y-%m-%d")
                        if "Gelesen am" not in book:
                            book["Gelesen am"] = []
                        if new_date not in book["Gelesen am"]:
                            book["Gelesen am"].append(new_date)
                            save_data(data)
                            st.success("Lesedatum gespeichert!")
                        else:
                            st.info("Dieses Datum wurde bereits gespeichert.")

                    if "Notizen" not in book:
                        book["Notizen"] = []

                    with st.form(f"form_{book['_id']}"):
                        note = st.text_area("Neue Anmerkung")
                        submit_note = st.form_submit_button("Speichern")
                        if submit_note and note:
                            book["Notizen"].append({
                                "Text": note,
                                "Zeit": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            save_data(data)
                            st.success("Anmerkung gespeichert!")

                    st.markdown("**Anmerkungen:**")
                    for note in book["Notizen"]:
                        st.markdown(f"- _{note['Zeit']}_: {note['Text']}")

# ----------------------------
# Speicherung (optional – hier nicht mehr zwingend nötig)
# ----------------------------
# save_data(data)  # wird gezielt aufgerufen nach Änderungen
