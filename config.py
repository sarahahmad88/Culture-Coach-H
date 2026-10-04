"""Server settings. No secrets are serialized into attempts or agent prompts."""
import os
from dataclasses import dataclass
GROQ_MODEL = "openai/gpt-oss-120b"
CULTURES = ['Pakistan', 'Japan', 'Germany', 'United States', 'China', 'Australia', 'UK', 'Saudi Arabia', 'Egypt', 'Brazil', 'Mexico', 'South Africa', 'France', 'Greece']
LEVELS = {'Beginner': 3, 'Intermediate': 8, 'Advanced': 15}
PROGRESSION = {'attempts': 3, 'average': 70, 'coverage': .6}  # draft product rule
DIMENSIONS = ['Power Distance', 'Individualism/Collectivism', 'Masculinity/Achievement Orientation', 'Uncertainty Avoidance', 'Long-Term Orientation', 'Indulgence']
SAFEGUARD = 'Cultural dimensions describe broad tendencies at the cultural level. They do not predict the behavior of every individual.'
@dataclass(frozen=True)
class Settings:
    groq_api_key: str = ''
    groq_model: str = GROQ_MODEL
    supabase_url: str = ''
    supabase_key: str = ''
    norms_embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    norms_classifier_model: str = 'facebook/bart-large-mnli'
    norms_embedding_revision: str = 'main'
    norms_classifier_revision: str = 'main'
    max_calls: int = 100
    max_output_tokens: int = 200000
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-3.8-flash'
    groq_api_key_2: str = ''
    @classmethod
    def load(cls, secrets=None):
        def get(k, default=''):
            try: return str(secrets.get(k, os.getenv(k, default))) if secrets is not None else os.getenv(k, default)
            except Exception: return os.getenv(k, default)
        return cls(get('GROQ_API_KEY'), GROQ_MODEL, get('SUPABASE_URL'), get('SUPABASE_ANON_KEY'), get('NORMS_EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'),get('NORMS_CLASSIFIER_MODEL','facebook/bart-large-mnli'),get('NORMS_EMBEDDING_REVISION','main'),get('NORMS_CLASSIFIER_REVISION','main'),gemini_api_key=get('GEMINI_API_KEY'),gemini_model=get('GEMINI_MODEL','gemini-3.8-flash'),groq_api_key_2=get('GROQ_API_KEY_2'))
