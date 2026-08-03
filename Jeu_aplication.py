import streamlit as st
import requests
import random
import re  # <-- L'import manquant est bien là

# --- CONFIGURATION DE LA PAGE STREAMLIT ---
st.set_page_config(
    page_title="BIBLE QUIZ",
    # page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Configuration Supabase
SUPABASE_URL = "https://wyywkuekjakjrntqqbpn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5eXdrdWVramFranJudHFxYnBuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUwODQ2MTgsImV4cCI6MjEwMDY2MDYxOH0.nBhUnYy1RYvqbIWuNXB0xgb-jPwF6VR-GKniaeu61fE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- GESTION DE L'ÉTAT DU JEU (SESSION STATE) ---
if "score" not in st.session_state:
    st.session_state.score = 0
if "total_joue" not in st.session_state:
    st.session_state.total_joue = 0
if "questions" not in st.session_state:
    st.session_state.questions = []
if "compteur_questions" not in st.session_state:
    st.session_state.compteur_questions = {}
if "question_actuelle" not in st.session_state:
    st.session_state.question_actuelle = None
if "reponse_validee" not in st.session_state:
    st.session_state.reponse_validee = False


# --- FONCTIONS API ---
def telecharger_questions():
    try:
        url = f"{SUPABASE_URL}/rest/v1/Questions?select=*"
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
    return []

def piocher_nouvelle_question():
    if not st.session_state.questions:
        st.session_state.questions = telecharger_questions()

    if not st.session_state.questions:
        return False

    # Réinitialisation si 20 questions sont jouées
    if st.session_state.total_joue >= 20:
        st.session_state.compteur_questions.clear()
        st.session_state.total_joue = 0

    # Filtrer les questions vues moins de 2 fois
    disponibles = [
        q for q in st.session_state.questions
        if st.session_state.compteur_questions.get(q.get("id"), 0) < 1
    ]

    if not disponibles:
        st.session_state.compteur_questions.clear()
        st.session_state.total_joue = 0
        disponibles = st.session_state.questions

    st.session_state.question_actuelle = random.choice(disponibles)
    q_id = st.session_state.question_actuelle.get("id")

    st.session_state.compteur_questions[q_id] = st.session_state.compteur_questions.get(q_id, 0) + 1
    st.session_state.total_joue += 1
    st.session_state.reponse_validee = False
    return True


# --- INTERFACE UTILISATEUR ---
st.title(" BIBLE QUIZ")

# Menu de navigation par onglets
tab_jeu, tab_ajouter = st.tabs(["🎮 Jouer", "➕ Proposer une question"])

# --- ONGLET 1 : JOUER AU QUIZ ---
with tab_jeu:
    # Barre d'en-tête (Score & Progression)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Score", value=f"{st.session_state.score} pt(s)")
    with col2:
        st.metric(label="Progression", value=f"{st.session_state.total_joue} / 20")

    st.divider()

    # Démarrage de la partie
    if st.session_state.question_actuelle is None:
        if st.button("Commencer la partie", type="primary", use_container_width=True):
            if not piocher_nouvelle_question():
                st.error("Impossible de charger les questions depuis Supabase.")
            else:
                st.rerun()

    # Affichage de la question et du formulaire
    if st.session_state.question_actuelle:
        q = st.session_state.question_actuelle
        st.subheader(f"Question : {q.get('Question')}")

        with st.form("form_reponse", clear_on_submit=False):
            rep_utilisateur = st.text_input("Votre réponse :", key="champ_reponse")
            btn_valider = st.form_submit_button("Valider la réponse ", use_container_width=True, type="primary")

            if btn_valider and not st.session_state.reponse_validee:
                st.session_state.reponse_validee = True
                bonne_rep = str(q.get("réponse", "")).strip()

                # --- LOGIQUE D'EXTRACTION DE NOMBRES ---
                est_correct = False
                
                match_utilisateur = re.search(r'\d+', rep_utilisateur)
                match_bonne_rep = re.search(r'\d+', bonne_rep)

                if match_bonne_rep and match_utilisateur:
                    if match_utilisateur.group() == match_bonne_rep.group():
                        est_correct = True
                else:
                    rep_texte = rep_utilisateur.strip().lower()
                    bonne_rep_texte = bonne_rep.lower().replace(" ","").replace("ans","")
                    if rep_texte == bonne_rep_texte:
                        est_correct = True

                # --- AFFICHAGE DU RÉSULTAT ---
                if est_correct:
                    st.success(" BRAVO ! C'est la bonne réponse !")
                    st.session_state.score += 1
                    st.balloons()
                else:
                    st.error(f" Dommage ! La bonne réponse était : **{bonne_rep}**")

                ref = q.get("reference")
                if ref:
                    st.info(f"📖 **Source / Référence :** {ref}")

        # Bouton Question Suivante
        if st.session_state.reponse_validee:
            if st.button("Question Suivante ➡️", use_container_width=True):
                piocher_nouvelle_question()
                st.rerun()

# --- ONGLET 2 : PROPOSER UNE QUESTION ---
with tab_ajouter:
    st.subheader("➕ Ajouter une question à la base Supabase")

    with st.form("form_ajout"):
        nouvelle_q = st.text_input("Intitulé de la question")
        nouvelle_r = st.text_input("Réponse exacte")
        nouvelle_ref = st.text_input("Référence / Verset / Source (optionnel)")
        btn_envoyer = st.form_submit_button("Envoyer sur Supabase 🌐", use_container_width=True)

        if btn_envoyer:
            if nouvelle_q.strip() and nouvelle_r.strip():
                payload = {
                    "Question": nouvelle_q.strip(),
                    "réponse": nouvelle_r.strip(),
                    "reference": nouvelle_ref.strip()
                }
                try:
                    url = f"{SUPABASE_URL}/rest/v1/Questions"
                    res = requests.post(url, headers=HEADERS, json=payload, timeout=5)
                    if res.status_code in [200, 201]:
                        st.success("🌐 Question enregistrée avec succès !")
                        st.session_state.questions = []  # Vider le cache pour inclure la nouvelle question
                    else:
                        st.error(f"Erreur lors de l'enregistrement ({res.status_code})")
                except Exception as e:
                    st.error(f"Erreur de connexion : {e}")
            else:
                st.warning("⚠️ La question et la réponse ne peuvent pas être vides !")
