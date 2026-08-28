st.markdown("""
    <style>
    /* Import czcionki pisanej odręcznie przez pióro */
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@600&family=Reenie+Beanie&family=IM+Fell+English+SC&display=swap');

    /* Tło z mocnym cieniowaniem krawędzi (efekt starej zwiniętej karty / fototapety) */
    .stApp {
        background-color: #D4B895;
        background-image: 
            radial-gradient(circle, rgba(255,243,224,0.3) 20%, rgba(70,35,10,0.75) 90%),
            linear-gradient(to right, rgba(50,20,5,0.6), transparent 15%, transparent 85%, rgba(50,20,5,0.6));
    }

    /* Panel boczny (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #E2CEB1;
        border-right: 3px solid #5C2C16;
    }

    /* Nagłówki */
    h1, h2, h3 {
        font-family: 'Caveat', cursive !important;
        color: #3D1C06 !important;
        font-weight: bold;
        letter-spacing: 1px;
        border-bottom: 2px dashed #704214;
        padding-bottom: 5px;
    }

    h1 {
        font-size: 3.5rem !important;
    }

    /* Teksty, etykiety i składniki - czcionka imitująca pismo odręczne piórem */
    p, span, label, div, .stMarkdown, .stMarkdown p, li {
        font-family: 'Caveat', cursive !important;
        font-size: 1.35rem !important;
        color: #2C1203 !important;
    }

    /* Expandery jako karty przepisów */
    .streamlit-expanderHeader {
        background-color: #EFE0C4 !important;
        border: 1px solid #704214 !important;
        border-radius: 4px;
        font-family: 'Caveat', cursive !important;
        font-size: 1.4rem !important;
        color: #3D1C06 !important;
        font-weight: bold;
    }

    /* Pola formularzy */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFDF9 !important;
        border: 1px solid #704214 !important;
        color: #2C1203 !important;
        font-family: 'Caveat', cursive !important;
        font-size: 1.25rem !important;
    }

    /* Przyciski */
    .stButton button {
        background-color: #704214 !important;
        color: #F9F1E6 !important;
        border: 1px solid #3D1C06 !important;
        font-family: 'IM Fell English SC', serif;
        font-weight: bold;
        border-radius: 4px;
    }
    .stButton button:hover {
        background-color: #8B4513 !important;
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)
