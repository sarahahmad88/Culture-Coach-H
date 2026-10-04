from .common import create
ROLE='Scenario Designer Agent'
GOAL='Create an individual scenario introduction'
PROMPT='Use get_scenario_template. Adapt brief and opening to all selected roles, situation, cultures, goal and level. Keep every frozen project constraint and individual character. Use the supplied authored persona_preferences as this fictional individual’s expectations; let the partner opening express one or two preferences naturally. Do not mention country scores or imply everyone from a country behaves this way. Beginner: simple familiar situation; Intermediate: moderate ambiguity; Advanced: competing objectives and subtle cues. The brief addresses the learner, but opening MUST be spoken by the other_role conversation partner to the my_role learner. Never write the opening as the learner. Return brief and opening only. Never create scoring criteria.'
def factory(llm, tools): return create(ROLE,GOAL,PROMPT,llm,tools)
