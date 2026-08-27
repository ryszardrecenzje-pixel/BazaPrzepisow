import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# --- KONFIGURACJA POŁĄCZENIA Z GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_connection():
    # Pobieranie poświadczeń z tajemnic Streamlit (lub bezpośrednio z pliku credentials.json)
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Wpisz dokładną nazwę swojego pliku w Google Sheets
    sheet = client.open("PrzepisyBaza")
    return sheet

try:
    sheet = init_connection()
    ws_przepisy = sheet.worksheet("Przepisy")
    ws_zakupy = sheet.worksheet("Zakupy")
except Exception as e:
    st.error(f"Błąd połączenia z Google Sheets: {e}")
    st.stop()

# --- INTERFEJS APLIKACI (STREAMLIT) ---
st.title("🍳 Moja Książka Kucharska i Lista Zakupów")

menu = st.sidebar.selectbox("Wybierz zakładkę", ["📖 Przeglądaj przepisy", "➕ Dodaj przepis", "🛒 Lista zakupów"])

# --- ZAKŁADKA 1: PRZEGLĄDANIE I WYSZUKIWARKA ---
if menu == "📖 Przeglądaj przepisy":
    st.header("Przeglądaj zapisane przepisy")
    
    data = ws_przepisy.get_all_records()
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("Brak zapisanych przepisów w bazie.")
    else:
        # Wyszukiwarka
        search_query = st.text_input("🔍 Szukaj przepisu po nazwie lub składniku:")
        
        if search_query:
            filtered_df = df[
                df['Nazwa'].str.contains(search_query, case=False, na=False) |
                df['Składniki'].str.contains(search_query, case=False, na=False)
            ]
        else:
            filtered_df = df
            
        st.write(f"Znaleziono przepisów: {len(filtered_df)}")
        
        for index, row in filtered_df.iterrows():
            with st.expander(f"🍽️ {row['Nazwa']} ({row['Kategoria']})"):
                st.markdown(f"**Składniki:**\n{row['Składniki']}")
                st.markdown(f"**Przygotowanie:**\n{row['Przygotowanie']}")

# --- ZAKŁADKA 2: DODAWANIE PRZEPISU I LISTA ZAKUPÓW ---
elif menu == "➕ Dodaj przepis":
    st.header("Dodaj nowy przepis")
    
    with st.form("add_recipe_form"):
        nazwa = st.text_input("Nazwa przepisu")
        kategoria = st.selectbox("Kategoria", ["Obiad", "Śniadanie", "Kolacja", "Deser", "Inne"])
        składniki = st.text_area("Składniki (wypisz w osobnych liniach)")
        przygotowanie = st.text_area("Sposób przygotowania")
        
        dodaj_do_zakupów = st.checkbox("Automatycznie dodaj składniki do listy zakupów", value=True)
        
        submit = st.form_submit_button("Zapisz przepis")
        
        if submit:
            if nazwa and składniki:
                # Zapis do Google Sheets (Przepisy)
                ws_przepisy.append_row([nazwa, kategoria, składniki, przygotowanie])
                
                # Automatyczne dodanie składników do listy zakupów
                if dodaj_do_zakupów:
                    linie_składników = składniki.split("\n")
                    for skladnik in linie_składników:
                        if skladnik.strip():
                            ws_zakupy.append_row([skladnik.strip(), "Nie"])
                            
                st.success(f"Przepis '{nazwa'}' został pomyślnie zapisany!")
            else:
                st.warning("Uzupełnij nazwę przepisu oraz składniki.")

# --- ZAKŁADKA 3: LISTA ZAKUPÓW ---
elif menu == "🛒 Lista zakupów":
    st.header("Twoja Lista Zakupów")
    
    zakupy_data = ws_zakupy.get_all_records()
    df_zakupy = pd.DataFrame(zakupy_data)
    
    if df_zakupy.empty:
        st.info("Twoja lista zakupów jest pusta.")
    else:
        st.write("Zaznacz produkty, które zostały kupione, lub usuń całą listę:")
        
        # Wyświetlanie listy z interaktywnymi checkboxami (symulacja)
        updated_rows = []
        for index, row in df_zakupy.iterrows():
            col1, col2 = st.columns([0.8, 0.2])
            is_checked = col2.checkbox("Kupione", value=(row['Kupione'] == "Tak"), key=f"shop_{index}")
            
            status_text = "Tak" if is_checked else "Nie"
            updated_rows.append([row['Składnik'], status_text])
            
            if is_checked:
                col1.markdown(f"~~{row['Składnik']}~~")
            else:
                col1.markdown(f"**{row['Składnik']}**")
                
        if st.button("Zaktualizuj status zakupów"):
            # Aktualizacja całej tabeli w Google Sheets
            ws_zakupy.clear()
            ws_zakupy.append_row(["Składnik", "Kupione"])
            for r in updated_rows:
                ws_zakupy.append_row(r)
            st.success("Zaktualizowano listę zakupów!")
