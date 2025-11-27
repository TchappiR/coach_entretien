import os
import json
from groq import Groq
from dotenv import load_dotenv
from file_reader import read_file 

load_dotenv()
    
class InterviewPreparer:

    PROMPT_ANALYSE_PATH = "prompts/prompt_analyse.txt"
    PROMPT_QUESTIONS_PATH = "prompts/prompt_questions.txt"
    
    def __init__(self, cv_text: str, offer_text: str):
        self.cv_text = cv_text
        self.offer_text = offer_text
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = "llama-3.3-70b-versatile" 
        self.analysis_result = {} 
        self.questions_generees = []

    
    def _call_llm(self, system_prompt: str, user_content: str) -> dict: 
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": user_content}
            ],
            model=self.model,
            response_format={"type": "json_object"}, 
            temperature=0.1 
        )
        # Parse le contenu en supposant qu'il est toujours JSON valide
        return json.loads(chat_completion.choices[0].message.content)


    def analyser_fit(self) -> dict:
        """Phase 1 : Analyse le CV et l'offre. Suppose que le fichier prompt existe."""
        
        system_prompt = read_file(self.PROMPT_ANALYSE_PATH)

        user_content = f"""
                            --- OFFRE D'EMPLOI ---
                            {self.offer_text}

                            --- CV DU CANDIDAT ---
                            {self.cv_text}
                        """
        result = self._call_llm(system_prompt, user_content)
        self.analysis_result = result
        return result

            
    def generer_questions(self, nombre_questions: int = 10) -> list[dict]:
        """Phase 2 : Génère une liste de questions. Suppose que l'analyse a réussi."""

        if not self.analysis_result:
            self.analyser_fit()

        system_prompt = read_file(self.PROMPT_QUESTIONS_PATH)

        # On donne à l'IA le résultat de l'étape 1 (l'analyse)
        user_content = f"""
Voici l'analyse du candidat :
{json.dumps(self.analysis_result)}
Génère {nombre_questions} questions maintenant.
"""

        result = self._call_llm(system_prompt, user_content)
        
        self.questions_generees = result.get("plan_entretien", []) 
        return self.questions_generees