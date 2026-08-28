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
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    
    sheet = client.open("PrzepisyBaza")
    
    try:
        ws_przepisy = sheet.worksheet("Przepisy")
    except gspread.exceptions.WorksheetNotFound:
        ws_przepisy = sheet.add_worksheet(title="Przepisy", rows="100", cols="5")
        ws_przepisy.append_row(["Nazwa", "Składniki", "Instrukcja"])

except Exception as e:
    st.error(f"Błąd połączenia z Google Sheets: {e}")
    st.stop()

st.title("📖 Moja Baza Przepisów i Lista Zakupów")

# Pobranie aktualnych danych
data_przepisy = ws_przepisy.get_all_records()
df_przepisy = pd.DataFrame(data_przepisy)

menu = ["Przeglądaj przepisy", "Dodaj przepis", "Lista zakupów", "Co mogę zrobić z..."]
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
                
                if st.button(f"Usuń przepis: {nazwa}", key=f"del_{index}"):
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
                istniejace_nazwy = df_przepisy["Nazwa"].values if not df_przepisy.empty and "Nazwa" in df_przepisy.columns else []
                
                if nowa_nazwa.strip() in istniejace_nazwy:
                    st.error(f"Przepis o nazwie '{nowa_nazwa}' już istnieje w bazie! Wybierz inną nazwę.")
                else:
                    ws_przepisy.append_row([nowa_nazwa, skladniki_input, instrukcja_input])
                    st.success(f"Dodano przepis: {nowa_nazwa}!")
                    st.rerun()

# --- 3. LISTA ZAKUPÓW Z WYBOREM PRZEPISÓW I POBIERANIEM ---
elif wybor == "Lista zakupów":
    st.header("🛒 Generator Listy Zakupów")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak przepisów, aby wygenerować listę zakupów.")
    else:
        st.subheader("Wybierz przepisy, które chcesz ugotować:")
        
        wybrane_przepisy = []
        for index, row in df_przepisy.iterrows():
            nazwa = row.get("Nazwa", "")
            if st.checkbox(f"{nazwa}", key=f"shop_{index}"):
                wybrane_przepisy.append(nazwa)
                
        if wybrane_przepisy:
            st.markdown("---")
            st.subheader("Składniki do kupienia:")
            
            zsumowane_skladniki = []
            for nazwa in wybrane_przepisy:
                przepis_row = df_przepisy[df_przepisy["Nazwa"] == nazwa]
                if not przepis_row.empty:
                    skladniki_tekst = przepis_row.iloc[0].get("Składniki", "")
                    linijki = [s.strip() for s in skladniki_tekst.split("\n") if s.strip()]
                    for linijka in linijki:
                        zsumowane_skladniki.append(f"- [ ] {linijka} ({nazwa})")
            
            tekst_listy = "\n".join(zsumowane_skladniki)
            st.markdown(tekst_listy)
            
            st.markdown("---")
            st.download_button(
                label="📥 Pobierz listę zakupów jako notatnik (.txt)",
                data=tekst_listy,
                file_name="lista_zakupow.txt",
                mime="text/plain"
            )
        else:
            st.info("Zaznacz przynajmniej jeden przepis powyżej, aby wygenerować listę zakupów.")

# --- 4. CO MOGĘ ZROBIĆ Z... (DOPASOWYWANIE SKŁADNIKÓW) ---
elif wybor == "Co mogę zrobić z...":
    st.header("🍳 Co mogę ugotować z tego, co mam?")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak zapisanych przepisów w bazie.")
    else:
        # Zbieramy wszystkie unikalne składniki ze wszystkich przepisów, aby stworzyć listę wyboru
        wszystkie_skladniki = set()
        for _, row in df_przepisy.iterrows():
            skladniki_tekst = row.get("Składniki", "")
            linijki = [s.strip().lower() for s in skladniki_tekst.split("\n") if s.strip()]
            for l in linijki:
                wszystkie_skladniki.add(l)
                
        st.subheader("Zaznacz produkty, które masz pod ręką:")
        
        # Wyświetlamy checkboxy dla znalezionych składników w kolumnach lub pod spodem
        posiadane_produkty = []
        
        # Użyjemy kontenera z przewijaniem lub zwykłej pętli
        for skladnik in sorted(wszystkie_skladniki):
            if st.checkbox(f"{skladnik}", key=f"have_{skladnik}"):
                posiadane_produkty.append(skladnik)
                
        st.markdown("---")
        st.subheader("Wyniki - co możesz zrobić:")
        
        if not posiadane_produkty:
            st.warning("Zaznacz przynajmniej jeden produkt powyżej, aby sprawdzić dostępne przepisy.")
        else:
            mozliwe_przepisy = 0
            
            for _, row in df_przepisy.iterrows():
                nazwa = row.get("Nazwa", "")
                skladniki_tekst = row.get("Składniki", "")
                
                # Wyciągamy składniki danego przepisu
                skladniki_przepisu = [s.strip().lower() for s in skladniki_tekst.split("\n") if s.strip()]
                
                if skladniki_przepisu:
                    # Sprawdzamy, które składniki przepisu posiadamy, a których brakuje
                    posiadane_w_przepisie = [s for s in skladniki_przepisu if s in posiadane_produkty]
                    brakujące_w_przepisie = [s for s in skladniki_przepisu if s not in posiadane_produkty]
                    
                    # Logika dopasowania: np. pokazujemy przepisy, do których masz WSZYSTKIE składniki LUB większość
                    # Tutaj zrobimy czytelny podział:
                    procent_posiadanych = len(posiadane_w_przepisie) / len(skladniki_przepisu) * 100
                    
                    if len(brakujące_w_przepisie) == 0:
                        st.success(f"🎉 **{nazwa}** (Masz 100% składników!)")
                        mozliwe_przepisy += 1
                    elif procent_posiadanych >= 50:
                        st.info(f"💡 **{nazwa}** (Masz {int(procent_posiadanych)}% składników. Brakuje: {', '.join(brakujące_w_przepisie)})")
                        mozliwe_przepisy += 1
                        
            if mozliwe_przepisy == 0:
                st.error("Nie znaleziono przepisów pasujących do zaznaczonych składników (spróbuj zaznaczyć ich więcej).")
