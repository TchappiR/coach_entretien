# app.py

import streamlit as st
import json
import os
import time
from datetime import datetime # Nouveau pour le timestamp dans le log

# Importation des modules locaux (assurez-vous que ces fichiers sont au même niveau)
from extraction_cv_informations import analyze_cv
from extraction_job_information import scrape_job_offer
from brain import InterviewPreparer
from interviewer import RecruiterAgent

# --- Configuration et État de la Session ---

st.set_page_config(page_title="Coach d'Entretien IA 🤖", layout="wide")

# Initialisation de l'état de la session pour la conversation et l'Agent
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'plan_entretien' not in st.session_state:
    st.session_state.plan_entretien = None
if 'profil_candidat' not in st.session_state:
    st.session_state.profil_candidat = None
if 'log_filename' not in st.session_state:
    st.session_state.log_filename = None

# --- Nouvelle Fonction de Log ---

def log_conversation_turn(role: str, content: str, action: str = None):
    """Écrit une ligne dans le fichier de log de l'entretien."""
    if not st.session_state.log_filename:
        # Ceci ne devrait pas arriver si l'initialisation se passe bien, mais sécurité
        return 

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Formatage de l'entrée de log
    log_entry = {
        "timestamp": timestamp,
        "role": role,
        "action": action if action else "TALK",
        "content": content
    }
    
    # Écriture dans le fichier de log (mode 'a' pour append/ajouter)
    try:
        with open(st.session_state.log_filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        st.warning(f"⚠️ Impossible d'écrire dans le fichier de log : {e}")


# --- Fonctions Principales ---

def initialiser_entretien(cv_file_path, job_url):
    """
    Étape 1 & 2 : Extrait les données et prépare le plan d'entretien.
    """
    
    # NOUVEAUTÉ: Création du nom de fichier de log unique au démarrage
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.log_filename = os.path.join(log_dir, f"entretien_{timestamp_start}.jsonl")
    st.info(f"💾 Journal de l'entretien créé : {st.session_state.log_filename}")

    with st.spinner("1/3 - Extraction des informations du CV et de l'offre d'emploi..."):
        # 1. Extraction du CV (via le module extraction_cv_informations)
        try:
            cv_data = analyze_cv(cv_file_path)
            cv_text = json.dumps(cv_data) # On utilise le JSON structuré comme texte pour le Brain
            st.success("✅ Informations du CV extraites par l'IA.")
            log_conversation_turn("SYSTEM", "Extraction CV réussie", "DATA_EXTRACT")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse du CV : {e}")
            log_conversation_turn("ERROR", str(e), "CV_FAILURE")
            return False

        # 2. Extraction de l'Offre (via le module extraction_job_information)
        try:
            job_data = scrape_job_offer(job_url, timeout=20_000)
            job_text = json.dumps(job_data) # On utilise le JSON structuré comme texte pour le Brain
            st.success("✅ Informations de l'offre extraites par Firecrawl.")
            log_conversation_turn("SYSTEM", "Extraction Offre réussie", "DATA_EXTRACT")
        except Exception as e:
            st.error(f"❌ Erreur lors du scraping de l'offre d'emploi : {e}")
            log_conversation_turn("ERROR", str(e), "OFFER_FAILURE")
            return False


    with st.spinner("2/3 - Le Cerveau IA ('brain') analyse le 'fit' et crée le plan d'entretien..."):
        # 3. Préparation de l'Entretien (via le module brain)
        try:
            preparer = InterviewPreparer(cv_text, job_text)
            plan = preparer.generer_questions(nombre_questions=8) 
            profil = preparer.analysis_result
            
            st.session_state.plan_entretien = plan
            st.session_state.profil_candidat = profil
            st.success(f"✅ Plan d'entretien généré avec succès ({len(plan)} questions).")
            log_conversation_turn("SYSTEM", f"Plan d'entretien généré: {len(plan)} questions.", "PREP_SUCCESS")
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la préparation de l'entretien (Brain) : {e}")
            log_conversation_turn("ERROR", str(e), "PREP_FAILURE")
            return False

    with st.spinner("3/3 - Initialisation de l'Agent Recruteur ('interviewer')..."):
        # 4. Initialisation de l'Agent Recruteur (via le module interviewer)
        try:
            st.session_state.agent = RecruiterAgent(
                plan_entretien=st.session_state.plan_entretien, 
                profil_candidat=st.session_state.profil_candidat
            )
            st.success("✅ Agent Recruteur prêt pour l'entretien !")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'initialisation de l'Agent : {e}")
            log_conversation_turn("ERROR", str(e), "AGENT_INIT_FAILURE")
            return False
            
    # Lancement de la première question
    st.session_state.messages = []
    reponse_agent = st.session_state.agent.decider_prochaine_action(None)
    
    # CORRECTION & NOUVEAUTÉ: Enregistrement et Log de la première question
    st.session_state.messages.append({
        "role": "assistant", 
        "content": reponse_agent['contenu'],
        "action": reponse_agent.get('action')
    })
    log_conversation_turn("assistant", reponse_agent['contenu'], reponse_agent.get('action'))
    
    st.toast("Entretien démarré ! Répondez à la première question.", icon="🗣️")
    return True


# --- Interface Streamlit (UI) ---

st.title("🗣️ Coach d'Entretien Piloté par IA")
st.markdown("Pratiquez votre entretien d'embauche. L'IA analyse votre CV et l'offre d'emploi pour générer des questions ciblées.")

## 📝 Configuration de l'Entretien
with st.expander("Configurer et Démarrer", expanded=True):
    # 1. Téléversement du CV
    uploaded_file = st.file_uploader("📂 Téléversez votre CV (Format PDF)", type="pdf")
    
    # 2. URL de l'Offre
    job_url = st.text_input("🔗 Lien vers l'offre d'emploi (Ex: LinkedIn, Indeed, etc.)")
    
    # 3. Bouton de Démarrage
    if st.button("🚀 Démarrer la Simulation", type="primary", disabled=(uploaded_file is None or not job_url)):
        if uploaded_file and job_url:
            # Sauvegarde temporaire du PDF corrigée
            temp_pdf_path = os.path.join(os.getcwd(), uploaded_file.name)
            
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.read())
            
            initialiser_entretien(temp_pdf_path, job_url)

## 💬 Conversation
if st.session_state.agent:
    st.markdown("---")
    
    current_question_index = st.session_state.agent.index_question
    total_questions = len(st.session_state.plan_entretien)
    header_text = f"Entretien : Question {current_question_index + 1} / {total_questions}"
    if current_question_index >= total_questions:
         header_text = "Entretien Terminé"
    st.header(header_text)

    # Affichage de l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Champ de saisie pour la réponse du candidat
    last_message_action = st.session_state.messages[-1].get("action") if st.session_state.messages else None

    if last_message_action != "FIN":
        user_response = st.chat_input("Votre réponse au recruteur...")
        
        if user_response:
            # 1. Afficher et LOG la réponse de l'utilisateur
            with st.chat_message("user"):
                st.markdown(user_response)
            st.session_state.messages.append({"role": "user", "content": user_response})
            log_conversation_turn("user", user_response) # NOUVEAUTÉ: Log de la réponse utilisateur

            # 2. L'Agent décide de l'action suivante
            with st.spinner("🤖 L'Agent Recruteur réfléchit à la prochaine question..."):
                time.sleep(1) 
                reponse_agent = st.session_state.agent.decider_prochaine_action(user_response)

            # 3. Afficher la réponse de l'Agent
            with st.chat_message("assistant"):
                st.markdown(reponse_agent['contenu'])
            
            # 4. Mettre à jour et LOG l'état de la session
            st.session_state.messages.append({
                "role": "assistant",
                "content": reponse_agent['contenu'],
                "action": reponse_agent.get('action') 
            })
            log_conversation_turn("assistant", reponse_agent['contenu'], reponse_agent.get('action')) # NOUVEAUTÉ: Log de la réponse agent

            if reponse_agent.get("action") == "FIN":
                st.balloons()
                st.info("🎉 L'entretien est terminé. Vous pouvez recharger la page pour recommencer.")
    else:
        # Message après la fin
        st.markdown("### L'entretien est terminé. Merci de votre participation ! 👋")

else:
    st.info("Veuillez configurer et démarrer la simulation ci-dessus.")