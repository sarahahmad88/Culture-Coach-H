from .common import create
ROLE='Cultural Context Agent'
GOAL='Explain available context and limitations'
PROMPT='Use retrieve_cultural_context. Offer only general communication guidance consistent with retrieved source; do not invent country tendencies. Output guidance as a list. The controller preserves provenance and limitations.'
def factory(llm, tools): return create(ROLE,GOAL,PROMPT,llm,tools)
