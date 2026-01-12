import json
import os
from groq import Groq
from dotenv import load_dotenv
from file_reader import read_file

load_dotenv()

class RecruiterAgent:
    """
    Simule un agent recruteur qui utilise un plan de questions prédéfini
    et l'analyse LLM pour décider de la prochaine action (poser la question suivante
    du plan, creuser la réponse, ou terminer l'entretien).
    """
    PROMPT_INTERVIEWER_PATH = 'prompts/prompt_interviewer.txt'

    def __init__(self, plan_entretien: list, profil_candidat: dict):
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = "llama-3.3-70b-versatile"
        self.plan = plan_entretien 
        self.profil = profil_candidat
        self.index_question = 0 
        self.historique = [] # Historique des échanges

    def _penser(self, prompt_systeme: str, input_user: str) -> dict:
        chat = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_systeme},
                {"role": "user", "content": input_user}
            ],
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.2 
        )
        return json.loads(chat.choices[0].message.content)

    
    def decider_prochaine_action(self, derniere_reponse_candidat: str) -> dict:
        # Mise à jour de l'historique (conservé pour la clarté même si non utilisé par le LLM ici)
        if derniere_reponse_candidat:
            self.historique.append({"role": "candidat", "content": derniere_reponse_candidat})

        # CAS 1 : Début de l'entretien
        if not derniere_reponse_candidat:
            question_actuelle = self.plan[self.index_question]['question']
            return {"action": "POSER_QUESTION_PLAN", "contenu": question_actuelle}

        # CAS 2 : Analyse de la réponse et décision
        prompt_mission = read_file(self.PROMPT_INTERVIEWER_PATH) 
        question_precedente = self.plan[self.index_question]['question']
        
        system_prompt = f"""
                            CONTEXTE DU CANDIDAT : {json.dumps(self.profil)}
                            DERNIÈRE QUESTION POSÉE : "{question_precedente}"
                            RÉPONSE DU CANDIDAT : "{derniere_reponse_candidat}"
                            TA MISSION : "{prompt_mission}"
                        """

        decision = self._penser(system_prompt, "Analyse et décide.")
        
        # Le résultat doit être stocké dans l'historique
        self.historique.append({"role": "recruteur", "content": decision.get('phrase_a_dire', decision.get('decision'))})
        
        # Logique de transition
        if decision.get('decision') == "VALIDER_ET_SUIVANT":
            self.index_question += 1 # On avance dans le plan
            
            # Vérifier si on a fini le plan
            if self.index_question >= len(self.plan):
                return {"action": "FIN", "contenu": decision.get('phrase_a_dire', "Merci, l'entretien est terminé.")}
            
            # Sinon, on prépare la prochaine question du plan
            prochaine_du_plan = self.plan[self.index_question]['question']
            # On combine la transition de l'IA avec la question du plan
            phrase_mixte = f"{decision.get('phrase_a_dire', '')} \n\nMaintenant, {prochaine_du_plan}"
            return {"action": "CONTINUER", "contenu": phrase_mixte.strip()}
            
        else:
            # Si on CREUSE ou RECADRE, on n'avance pas l'index. (Action: RELANCE)
            return {"action": "RELANCE", "contenu": decision.get('phrase_a_dire', 'Pouvez-vous préciser votre réponse ?')}