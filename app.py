import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Książka Kucharska",
    page_icon="📖",
    layout="wide"
)

# --- STYLIZACJA W STYLU STAREJ KSIĘGI Z ZŁOTYMI AKCENTAMI (CSS) ---
st.markdown("""
    <style>
    /* Tło całej aplikacji - czytelny, ciemny mahoniowy brąz */
    .stApp {
        background-color: #38241B;
        color: #F4E8D8;
        font-family: 'Georgia', serif;
    }
    
    /* Panel boczny (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #2A1A12;
        border-right: 2px solid #D4AF37;
    }
    
    /* Nagłówki - wyraziste antyczne złoto */
    h1, h2, h3 {
        font-family: 'Georgia', serif;
        color: #F3C653;
        border-bottom: 2px solid #D4AF37;
        padding-bottom: 5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    /* Pola formularzy i pola tekstowe */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #4A3326 !important;
        border: 1px solid #D4AF37 !important;
        color: #F4E8D8 !important;
        font-family: 'Georgia', serif;
    }
    
    /* Etykiety tekstowe w formularzach */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stMarkdown p, span {
        color: #EED9C4 !important;
    }
    
    /* Przyciski ze złotą ramką i eleganckim tłem */
    .stButton button {
        background-color: #5C3A29 !important;
        color: #F3C653 !important;
        border: 1px solid #D4AF37 !important;
        font-family: 'Georgia', serif;
        font-weight: bold;
        border-radius: 3px;
    }
    .stButton button:hover {
        background-color: #734A35 !important;
        color: #FFFFFF !important;
        border-color: #FFD700 !important;
    }
    
    /* Expandery (przepisy) – klimatyczne ramki ze złotym akcentem */
    .streamlit-expanderHeader {
        background-color: #4A3326 !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 3px;
        font-family: 'Georgia', serif;
        color: #F3C653 !important;
        font-weight: bold;
    }
    
    /* Komunikaty systemowe (sukces, info, ostrzeżenia) */
    .stAlert {
        background-color: #4A3326 !important;
        color: #F4E8D8 !important;
        border: 1px solid #D4AF37 !important;
    }
    </style>
""", unsafe_allow_html=True)

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

st.title("📖 Moja Domowa Książka Kucharska")

data_przepisy = ws_przepisy.get_all_records()
df_przepisy = pd.DataFrame(data_przepisy)

menu = ["Przeglądaj przepisy", "Dodaj przepis", "Lista zakupów", "Co mogę zrobić z..."]
wybor = st.sidebar.selectbox("Spis treści", menu)

# --- FUNKCJA POMOCNICZA DO PARSOWANIA SKŁADNIKÓW ---
def parse_skladnik(linijka):
    """Rozbija linijkę składnika używając ukośnika / lub \ """
    normalizowana = linijka.replace("\\", "/")
    parts = [p.strip() for p in normalizowana.split("/")]
    return parts

# --- 1. PRZEGLĄDAJ, USUŃ I EDYTUJ PRZEPISY ---
if wybor == "Przeglądaj przepisy":
    st.header("Karta Przepisów")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak zapisanych przepisów w książce.")
    else:
        dostepne_kategorie = ["Wszystkie"] + list(df_przepisy["Kategoria"].dropna().unique()) if "Kategoria" in df_przepisy.columns else ["Wszystkie"]
        wybrana_kategoria_filtr = st.selectbox("Wyszukaj po kategorii:", dostepne_kategorie)
        
        for index, row in df_przepisy.iterrows():
            nazwa = row.get("Nazwa", "Bez nazwy")
            kategoria = row.get("Kategoria", "Inne")
            skladniki_tekst = row.get("Składniki", "")
            przygotowanie = row.get("Przygotowanie", "")
            
            if wybrana_kategoria_filtr != "Wszystkie" and kategoria != wybrana_kategoria_filtr:
                continue
                
            with st.expander(f"📜 {nazwa} [{kategoria}]"):
                edytuj_klucz = f"edit_mode_{index}"
                if edytuj_klucz not in st.session_state:
                    st.session_state[edytuj_klucz] = False
                
                if not st.session_state[edytuj_klucz]:
                    st.markdown(f"**Kategoria:** {kategoria}")
                    
                    st.markdown("**Składniki:**")
                    linijki_skladnikow = [s.strip() for s in skladniki_tekst.split("\n") if s.strip()]
                    for s in linijki_skladnikow:
                        parts = parse_skladnik(s)
                        if len(parts) == 3:
                            ilosc, jednostka, produkt = parts
                            st.markdown(f"- **{ilosc} {jednostka}** – {produkt}")
                        else:
                            st.markdown(f"- {s}")
                            
                    st.markdown(f"\n**Przygotowanie:**\n{przygotowanie}")
                    
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
                        nowe_skladniki = st.text_area("Składniki", value=skladniki_tekst)
                        
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
    st.header("Dopisz nowy przepis do księgi")
    
    with st.form("form_dodania"):
        nowa_nazwa = st.text_input("Nazwa przepisu")
        kategorie_opcje = ["Śniadanie", "Obiad", "Kolacja", "Deser", "Przekąska", "Inne"]
        kategoria_input = st.selectbox("Kategoria posiłku", kategorie_opcje)
        
        przygotowanie_input = st.text_area("Przygotowanie", help="Opisz krok po kroku jak wykonać przepis.")
        
        st.markdown("### Składniki")
        st.info("Wpisz składniki w formacie: **Ilość / Jednostka / Nazwa produktu** (np. `500 / g / mąka pszenna`)")
        skladniki_input = st.text_area("Lista składników (każdy w nowej linii)")
        
        submit = st.form_submit_button("Zapisz w księdze")
        
        if submit:
            if not nowa_nazwa.strip():
                st.warning("Podaj nazwę przepisu.")
            else:
                istniejace_nazwy = df_przepisy["Nazwa"].values if not df_przepisy.empty and "Nazwa" in df_przepisy.columns else []
                
                if nowa_nazwa.strip() in istniejace_nazwy:
                    st.error(f"Przepis o nazwie '{nowa_nazwa}' już istnieje w księdze!")
                else:
                    ws_przepisy.append_row([nowa_nazwa, kategoria_input, skladniki_input, przygotowanie_input])
                    st.success(f"Dodano przepis: {nowa_nazwa}!")
                    st.rerun()

# --- 3. LISTA ZAKUPÓW Z INTELIGENTNYM SUMOWANIEM ---
elif wybor == "Lista zakupów":
    st.header("🛒 Notatnik Zakupów")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak przepisów, aby wygenerować listę zakupów.")
    else:
        st.subheader("Wybierz przepisy na nadchodzące gotowanie:")
        
        wybrane_przepisy = []
        for index, row in df_przepisy.iterrows():
            nazwa = row.get("Nazwa", "")
            if st.checkbox(f"{nazwa}", key=f"shop_{index}"):
                wybrane_przepisy.append(nazwa)
                
        if wybrane_przepisy:
            st.markdown("---")
            st.subheader("Zsumowana lista potrzebnych produktów:")
            
            slownik_zakupow = {}
            
            for nazwa in wybrane_przepisy:
                przepis_row = df_przepisy[df_przepisy["Nazwa"] == nazwa]
                if not przepis_row.empty:
                    skladniki_tekst = przepis_row.iloc[0].get("Składniki", "")
                    linijki = [s.strip() for s in skladniki_tekst.split("\n") if s.strip()]
                    
                    for linijka in linijki:
                        parts = parse_skladnik(linijka)
                        if len(parts) == 3:
                            ilosc_str, jednostka, produkt = parts
                            produkt_lower = produkt.lower()
                            jednostka_lower = jednostka.lower()
                            
                            try:
                                ilosc = float(ilosc_str.replace(",", "."))
                                
                                if jednostka_lower == "g" and ilosc >= 1000:
                                    ilosc = ilosc / 1000
                                    jednostka_lower = "kg"
                                elif jednostka_lower == "ml" and ilosc >= 1000:
                                    ilosc = ilosc / 1000
                                    jednostka_lower = "l"
                                    
                                klucz = (produkt_lower, jednostka_lower)
                                if klucz in slownik_zakupow:
                                    slownik_zakupow[klucz] += ilosc
                                else:
                                    slownik_zakupow[klucz] = ilosc
                                    
                            except ValueError:
                                klucz = (linijka, "")
                                slownik_zakupow[klucz] = 1
                        else:
                            klucz = (linijka, "")
                            slownik_zakupow[klucz] = 1
            
            zsumowane_skladniki = []
            for (produkt, jednostka), ilosc in sorted(slownik_zakupow.items()):
                if jednostka == "":
                    zsumowane_skladniki.append(f"- [ ] {produkt}")
                else:
                    ilosc_formatted = int(ilosc) if ilosc.is_integer() else round(ilosc, 2)
                    zsumowane_skladniki.append(f"- [ ] {ilosc_formatted} {jednostka} / {produkt}")
            
            tekst_listy = "\n".join(zsumowane_skladniki)
            st.markdown(tekst_listy)
            
            st.markdown("---")
            st.download_button(
                label="📥 Pobierz listę zakupów (.txt)",
                data=tekst_listy,
                file_name="lista_zakupow.txt",
                mime="text/plain"
            )
        else:
            st.info("Zaznacz przynajmniej jeden przepis powyżej, aby wygenerować listę zakupów.")

# --- 4. CO MOGĘ ZROBIĆ Z... ---
elif wybor == "Co mogę zrobić z...":
    st.header("🍳 Spiżarnia – Co ugotować?")
    
    if df_przepisy.empty or "Nazwa" not in df_przepisy.columns or len(df_przepisy) == 0:
        st.info("Brak zapisanych przepisów w księdze.")
    else:
        wszystkie_skladniki = set()
        for _, row in df_przepisy.iterrows():
            skladniki_tekst = row.get("Składniki", "")
            linijki = [s.strip().lower() for s in skladniki_tekst.split("\n") if s.strip()]
            for l in linijki:
                parts = parse_skladnik(l)
                produkt = parts[-1] if len(parts) > 0 else l.lower()
                wszystkie_skladniki.add(produkt)
                
        st.subheader("Zaznacz produkty, które masz pod ręką:")
        
        posiadane_produkty = []
        for skladnik in sorted(wszystkie_skladniki):
            if st.checkbox(f"{skladnik}", key=f"have_{skladnik}"):
                posiadane_produkty.append(skladnik)
                
        st.markdown("---")
        st.subheader("Propozycje z Twojej spiżarni:")
        
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
                        parts = parse_skladnik(s)
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
