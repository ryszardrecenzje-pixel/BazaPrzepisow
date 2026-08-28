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
        ws_przepisy = sheet.add_worksheet(title="Przepisy", rows="100", cols="6")
        ws_przepisy.append_row(["Nazwa", "Kategoria", "Składniki", "Przygotowanie"])

except Exception as e:
    st.error(f"Błąd połączenia z Google Sheets: {e}")
    st.stop()

st.title("📖 Moja Baza Przepisów i Lista Zakupów")

data_przepisy = ws_przepisy.get_all_records()
df_przepisy = pd.DataFrame(data_przepisy)

menu = ["Przeglądaj przepisy", "Dodaj przepis", "Lista zakupów", "Co mogę zrobić z..."]
wybor = st.sidebar.selectbox("Menu", menu)

# --- 1. PRZEGLĄDAJ, USUŃ I EDYTUJ PRZEPISY ---
if wybor == "Przeglądaj przepisy":
    st.header("Twoje przepisy")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak zapisanych przepisów.")
    else:
        dostepne_kategorie = ["Wszystkie"] + list(df_przepisy["Kategoria"].dropna().unique()) if "Kategoria" in df_przepisy.columns else ["Wszystkie"]
        wybrana_kategoria_filtr = st.selectbox("Filtruj według kategorii:", dostepne_kategorie)
        
        for index, row in df_przepisy.iterrows():
            nazwa = row.get("Nazwa", "Bez nazwy")
            kategoria = row.get("Kategoria", "Inne")
            skladniki = row.get("Składniki", "")
            przygotowanie = row.get("Przygotowanie", "")
            
            if wybrana_kategoria_filtr != "Wszystkie" and kategoria != wybrana_kategoria_filtr:
                continue
                
            with st.expander(f"🍽️ {nazwa} ({kategoria})"):
                edytuj_klucz = f"edit_mode_{index}"
                if edytuj_klucz not in st.session_state:
                    st.session_state[edytuj_klucz] = False
                
                if not st.session_state[edytuj_klucz]:
                    st.markdown(f"**Kategoria:** {kategoria}")
                    st.markdown(f"**Składniki:**\n{skladniki}")
                    st.markdown(f"**Przygotowanie:**\n{przygotowanie}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ Edytuj", key=f"btn_edit_{index}"):
                            st.session_state[edytuj_klucz] = True
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ Usuń", key=f"del_{index}"):
                            ws_przepisy.delete_rows(index + 2)
                            st.success(f"Usunięto przepis: {nazwa}")
                            st.rerun()
                else:
                    st.subheader("Edycja przepisu")
                    with st.form(key=f"form_edit_{index}"):
                        nowa_nazwa = st.text_input("Nazwa przepisu", value=nazwa)
                        
                        kategorie_opcje = ["Śniadanie", "Obiad", "Kolacja", "Deser", "Przekąska", "Inne"]
                        kat_index = kategorie_opcje.index(kategoria) if kategoria in kategorie_opcje else 0
                        nowa_kategoria = st.selectbox("Kategoria posiłku", kategorie_opcje, index=kat_index)
                        
                        nowe_przygotowanie = st.text_area("Przygotowanie", value=przygotowanie)
                        nowe_skladniki = st.text_area("Składniki", value=skladniki)
                        
                        col_zapisz, col_anuluj = st.columns(2)
                        zapisz_zmiany = col_zapisz.form_submit_button("Zapisz zmiany")
                        anuluj = col_anuluj.form_submit_button("Anuluj")
                        
                        if zapisz_zmiany:
                            row_num = index + 2
                            ws_przepisy.update_cell(row_num, 1, nowa_nazwa)
                            ws_przepisy.update_cell(row_num, 2, nowa_kategoria)
                            ws_przepisy.update_cell(row_num, 3, nowe_skladniki)
                            ws_przepisy.update_cell(row_num, 4, nowe_przygotowanie)
                            
                            st.session_state[edytuj_klucz] = False
                            st.success("Zaktualizowano przepis!")
                            st.rerun()
                            
                        if anuluj:
                            st.session_state[edytuj_klucz] = False
                            st.rerun()

# --- 2. DODAJ PRZEPIS ---
elif wybor == "Dodaj przepis":
    st.header("Dodaj nowy przepis")
    
    with st.form("form_dodania"):
        nowa_nazwa = st.text_input("Nazwa przepisu")
        kategorie_opcje = ["Śniadanie", "Obiad", "Kolacja", "Deser", "Przekąska", "Inne"]
        kategoria_input = st.selectbox("Kategoria posiłku", kategorie_opcje)
        
        przygotowanie_input = st.text_area("Przygotowanie", help="Opisz krok po kroku jak wykonać przepis.")
        
        st.markdown("### Składniki")
        st.info("Wpisz składniki w formacie: **Ilość | Jednostka | Nazwa produktu** (np. `500 | g | mąka pszenna`)")
        skladniki_input = st.text_area("Lista składników (każdy w nowej linii)")
        
        submit = st.form_submit_button("Zapisz przepis")
        
        if submit:
            if not nowa_nazwa.strip():
                st.warning("Podaj nazwę przepisu.")
            else:
                istniejace_nazwy = df_przepisy["Nazwa"].values if not df_przepisy.empty and "Nazwa" in df_przepisy.columns else []
                
                if nowa_nazwa.strip() in istniejace_nazwy:
                    st.error(f"Przepis o nazwie '{nowa_nazwa}' już istnieje w bazie!")
                else:
                    ws_przepisy.append_row([nowa_nazwa, kategoria_input, skladniki_input, przygotowanie_input])
                    st.success(f"Dodano przepis: {nowa_nazwa}!")
                    st.rerun()

# --- 3. LISTA ZAKUPÓW Z INTELIGENTNYM SUMOWANIEM ---
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
            st.subheader("Zsumowana lista zakupów:")
            
            # Słownik do przechowywania zsumowanych produktów: { (produkt, jednostka): suma }
            slownik_zakupow = {}
            
            for nazwa in wybrane_przepisy:
                przepis_row = df_przepisy[df_przepisy["Nazwa"] == nazwa]
                if not przepis_row.empty:
                    skladniki_tekst = przepis_row.iloc[0].get("Składniki", "")
                    linijki = [s.strip() for s in skladniki_tekst.split("\n") if s.strip()]
                    
                    for linijka in linijki:
                        # Rozbijamy wpis po |
                        parts = [p.strip() for p in linijka.split("|")]
                        if len(parts) == 3:
                            ilosc_str, jednostka, produkt = parts
                            produkt_lower = produkt.lower()
                            jednostka_lower = jednostka.lower()
                            
                            try:
                                ilosc = float(ilosc_str.replace(",", "."))
                                
                                # Inteligentne przeliczanie gramów na kilogramy
                                if jednostka_lower == "g" and ilosc >= 1000:
                                    ilosc = ilosc / 1000
                                    jednostka_lower = "kg"
                                # Przeliczanie mililitrów na litry
                                elif jednostka_lower == "ml" and ilosc >= 1000:
                                    ilosc = ilosc / 1000
                                    jednostka_lower = "l"
                                    
                                klucz = (produkt_lower, jednostka_lower)
                                if klucz in slownik_zakupow:
                                    slownik_zakupow[klucz] += ilosc
                                else:
                                    slownik_zakupow[klucz] = ilosc
                                    
                            except ValueError:
                                # Jeśli ilość nie jest liczbą, traktujemy wpis tekstowo
                                klucz = (linijka, "")
                                slownik_zakupow[klucz] = 1
                        else:
                            # Jeśli brak formatu z |, dodajemy w całości
                            klucz = (linijka, "")
                            slownik_zakupow[klucz] = 1
            
            # Generujemy ostateczną listę do wyświetlenia i pobrania
            zsumowane_skladniki = []
            for (produkt, jednostka), ilosc in sorted(slownik_zakupow.items()):
                if jednostka == "":
                    zsumowane_skladniki.append(f"- [ ] {produkt}")
                else:
                    # Ładne wyświetlanie liczb (usuwanie zbędnych .0 jeśli to całkowita liczba)
                    ilosc_formatted = int(ilosc) if ilosc.is_integer() else round(ilosc, 2)
                    zsumowane_skladniki.append(f"- [ ] {ilosc_formatted} {jednostka} | {produkt}")
            
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

# --- 4. CO MOGĘ ZROBIĆ Z... ---
elif wybor == "Co mogę zrobić z...":
    st.header("🍳 Co mogę ugotować z tego, co mam?")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak zapisanych przepisów w bazie.")
    else:
        wszystkie_skladniki = set()
        for _, row in df_przepisy.iterrows():
            skladniki_tekst = row.get("Składniki", "")
            linijki = [s.strip().lower() for s in skladniki_tekst.split("\n") if s.strip()]
            for l in linijki:
                parts = [p.strip().lower() for p in l.split("|")]
                produkt = parts[-1] if len(parts) > 0 else l.lower()
                wszystkie_skladniki.add(produkt)
                
        st.subheader("Zaznacz produkty, które masz pod ręką:")
        
        posiadane_produkty = []
        for skladnik in sorted(wszystkie_skladniki):
            if st.checkbox(f"{skladnik}", key=f"have_{skladnik}"):
                posiadane_produkty.append(skladnik)
                
        st.markdown("---")
        st.subheader("Wyniki - co możesz zrobić:")
        
        if not posiadane_produkty:
            st.warning("Zaznacz przynajmniej jeden produkt powyżej.")
        else:
            mozliwe_przepisy = 0
            for _, row in df_przepisy.iterrows():
                nazwa = row.get("Nazwa", "")
                kategoria = row.get("Kategoria", "Inne")
                skladniki_tekst = row.get("Składniki", "")
                
                skladniki_przepisu = []
                for s in skladniki_tekst.split("\n"):
                    if s.strip():
                        parts = [p.strip().lower() for p in s.split("|")]
                        produkt = parts[-1] if len(parts) > 0 else s.strip().lower()
                        skladniki_przepisu.append(produkt)
                
                if skladniki_przepisu:
                    posiadane_w_przepisie = [s for s in skladniki_przepisu if s in posiadane_produkty]
                    brakujące_w_przepisie = [s for s in skladniki_przepisu if s not in posiadane_produkty]
                    
                    procent_posiadanych = len(posiadane_w_przepisie) / len(skladniki_przepisu) * 100
                    
                    if len(brakujące_w_przepisie) == 0:
                        st.success(f"🎉 **{nazwa}** [{kategoria}] (Masz 100% składników!)")
                        mozliwe_przepisy += 1
                    elif procent_posiadanych >= 50:
                        st.info(f"💡 **{nazwa}** [{kategoria}] (Masz {int(procent_posiadanych)}% składników. Brakuje: {', '.join(brakujące_w_przepisie)})")
                        mozliwe_przepisy += 1
                        
            if mozliwe_przepisy == 0:
                st.error("Brak przepisów pasujących do wybranych składników.")
