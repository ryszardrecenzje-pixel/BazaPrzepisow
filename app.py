import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURACJA POŁĄCZENIA Z GOOGLE SHEETS ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    # Odczyt danych z sekretów Streamlit Cloud (format TOML)
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    
    # Otwarcie arkusza (zmień "PrzepisyBaza" jeśli Twój arkusz nazywa się inaczej)
    sheet = client.open("PrzepisyBaza")
    
    # Pobieramy lub tworzymy arkusze na przepisy i składniki
    try:
        ws_przepisy = sheet.worksheet("Przepisy")
    except gspread.exceptions.WorksheetNotFound:
        ws_przepisy = sheet.add_worksheet(title="Przepisy", rows="100", cols="5")
        ws_przepisy.append_row(["Nazwa", "Składniki", "Instrukcja"])

    try:
        ws_skladniki = sheet.worksheet("Skladniki")
    except gspread.exceptions.WorksheetNotFound:
        ws_skladniki = sheet.add_worksheet(title="Skladniki", rows="100", cols="5")
        ws_skladniki.append_row(["Przepis", "Składnik"])

except Exception as e:
    st.error(f"Błąd połączenia z Google Sheets: {e}")
    st.stop()

st.title("📖 Moja Baza Przepisów i Lista Zakupów")

# Pobranie aktualnych danych
data_przepisy = ws_przepisy.get_all_records()
df_przepisy = pd.DataFrame(data_przepisy)

menu = ["Przeglądaj przepisy", "Dodaj przepis", "Lista zakupów"]
wybor = st.sidebar.selectbox("Menu", menu)

# --- 1. PRZEGLĄDAJ I USUŃ PRZEPISY ---
if wybor == "Przeglądaj przepisy":
    st.header("Twoje przepisy")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak zapisanych przepisów.")
    else:
        for index, row in df_przepisy.iterrows():
            nazwa = row.get("Nazwa", "Bez nazwy")
            skladniki = row.get("Składniki", "")
            instrukcja = row.get("Instrukcja", "")
            
            with st.expander(f"🍽️ {nazwa}"):
                st.markdown(f"**Składniki:**\n{skladniki}")
                st.markdown(f"**Przygotowanie:**\n{instrukcja}")
                
                # Przycisk usuwania przepisu
                if st.button(f"Usuń przepis: {nazwa}", key=f"del_{index}"):
                    # gspread rows są 1-indexed, a nagłówek to wiersz 1, więc index wiersza to index + 2
                    ws_przepisy.delete_rows(index + 2)
                    st.success(f"Usunięto przepis: {nazwa}")
                    st.rerun()

# --- 2. DODAJ PRZEPIS (BEZ DUPLIKATÓW) ---
elif wybor == "Dodaj przepis":
    st.header("Dodaj nowy przepis")
    
    with st.form("form_dodania"):
        nowa_nazwa = st.text_input("Nazwa przepisu")
        skladniki_input = st.text_area("Składniki (każdy w nowej linii)", help="Wpisz składniki, każdy w osobnej linii.")
        instrukcja_input = st.text_area("Sposób przygotowania")
        submit = st.form_submit_button("Zapisz przepis")
        
        if submit:
            if not nowa_nazwa.strip():
                st.warning("Podaj nazwę przepisu.")
            else:
                # Sprawdzenie czy przepis już istnieje (zabezpieczenie przed duplikatami)
                istniejace_nazwy = df_przepisy["Nazwa"].values if not df_przepisy.empty and "Nazwa" in df_przepisy.columns else []
                
                if nowa_nazwa.strip() in istniejace_nazwy:
                    st.error(f"Przepis o nazwie '{nowa_nazwa}' już istnieje w bazie! Wybierz inną nazwę.")
                else:
                    # Dodanie do arkusza Przepisy
                    ws_przepisy.append_row([nowa_nazwa, skladniki_input, instrukcja_input])
                    
                    # Opcjonalnie rozbijamy składniki do osobnego arkusza, jeśli potrzebne
                    linijki_skladnikow = [s.strip() for s in skladniki_input.split("\n") if s.strip()]
                    for s in linijki_skladnikow:
                        ws_skladniki.append_row([nowa_nazwa, s])
                        
                    st.success(f"Dodano przepis: {nowa_nazwa}!")
                    st.rerun()

# --- 3. LISTA ZAKUPÓW Z WYBOREM PRZEPISÓW I POBIERANIEM ---
elif wybor == "Lista zakupów":
    st.header("🛒 Generator Listy Zakupów")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak przepisów, aby wygenerować listę zakupów.")
    else:
        st.subheader("Wybierz przepisy, które chcesz ugotować:")
        
        # Tworzymy checkboxy dla każdego przepisu
        wybrane_przepisy = []
        for index, row in df_przepisy.iterrows():
            nazwa = row.get("Nazwa", "")
            if st.checkbox(f"{nazwa}", key=f"shop_{index}"):
                wybrane_przepisy.append(nazwa)
                
        if wybrane_przepisy:
            st.markdown("---")
            st.subheader("Składniki do kupienia:")
            
            # Zbieramy składniki z wybranych przepisów
            zsumowane_skladniki = []
            for nazwa in wybrane_przepisy:
                przepis_row = df_przepisy[df_przepisy["Nazwa"] == nazwa]
                if not przepis_row.empty:
                    skladniki_tekst = przepis_row.iloc[0].get("Składniki", "")
                    linijki = [s.strip() for s in skladniki_tekst.split("\n") if s.strip()]
                    for linijka in linijki:
                        zsumowane_skladniki.append(f"- [ ] {linijka} ({nazwa})")
            
            # Wyświetlenie listy na ekranie
            tekst_listy = "\n".join(zsumowane_skladniki)
            st.markdown(tekst_listy)
            
            st.markdown("---")
            # Przycisk do pobrania listy w formie notatnika (TXT)
            st.download_button(
                label="📥 Pobierz listę zakupów jako notatnik (.txt)",
                data=tekst_listy,
                file_name="lista_zakupow.txt",
                mime="text/plain"
            )
        else:
            st.info("Zaznacz przynajmniej jeden przepis powyżej, aby wygenerować listę zakupów.")
