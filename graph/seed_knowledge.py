"""
CURATED knowledge layer  --  NOT derived from USDA.

USDA FoodData Central says how much of a nutrient a food has. It does NOT say
what a nutrient is *for*. The Nutrient -> Goal links below are hand-written,
deliberately small, and limited to well-established, textbook-level statements
(of the kind found in NIH Office of Dietary Supplements fact sheets and
EU-authorised nutrition claims).

Rules for editing this file:
  * Add a link only if you can defend it in one plain sentence.
  * Describe a nutrient's role; never promise an outcome ("prevents", "cures").
  * Every link is stored with curated=True and source="manual_curation" so it
    can never be confused with USDA data.

Team note: have someone read the `basis` sentences once before the demo and
delete any link the group is not comfortable defending.
"""
from __future__ import annotations

CURATED_SOURCE = "manual_curation"

GOALS = [
    # key, display name, description, aliases the retriever recognises
    ("muscle_growth", "Muscle Growth", "Building and maintaining muscle tissue.",
     ("muscle growth", "muscle building", "build muscle", "muscle gain", "muscle mass")),
    ("bone_health", "Bone Health", "Maintaining healthy, strong bones.",
     ("bone health", "bone strength", "strong bones", "bones", "bone")),
    ("digestive_health", "Digestive Health", "Normal digestive function.",
     ("digestive health", "digestion", "gut health")),
    ("red_blood_cell_formation", "Red Blood Cell Formation", "Formation of healthy red blood cells.",
     ("red blood cell formation", "red blood cells", "red blood cell", "blood cell formation", "blood health")),
    ("immune_function", "Immune Function", "Normal function of the immune system.",
     ("immune function", "immune system", "immunity", "immune health", "immune")),
    ("muscle_heart_function", "Normal Muscle and Heart Function", "Normal muscle contraction and heart function.",
     ("muscle and heart function", "muscle function", "heart function", "normal heart function")),
]

# (nutrient_key, goal_key, one-sentence basis)
SUPPORTS = [
    ("protein", "muscle_growth",
     "Dietary protein supplies the amino acids used to build and maintain muscle tissue."),
    ("calcium", "bone_health",
     "Calcium is a major structural component of bone."),
    ("vitamin_d", "bone_health",
     "Vitamin D helps the body absorb calcium, which bone needs."),
    ("magnesium", "bone_health",
     "Magnesium contributes to the maintenance of normal bones."),
    ("fiber", "digestive_health",
     "Dietary fiber contributes to normal bowel function."),
    ("iron", "red_blood_cell_formation",
     "Iron is a component of hemoglobin, the oxygen-carrying protein in red blood cells."),
    ("vitamin_b12", "red_blood_cell_formation",
     "Vitamin B12 is needed for normal red blood cell formation."),
    ("folate", "red_blood_cell_formation",
     "Folate is needed for normal blood cell formation."),
    ("vitamin_c", "immune_function",
     "Vitamin C contributes to the normal function of the immune system."),
    ("zinc", "immune_function",
     "Zinc contributes to the normal function of the immune system."),
    ("potassium", "muscle_heart_function",
     "Potassium is an electrolyte involved in normal muscle contraction and heart rhythm."),
]

GOAL_BY_KEY = {g[0]: g for g in GOALS}


def seed_rows():
    goal_rows = [{"key": k, "name": n, "description": d} for k, n, d, _ in GOALS]
    link_rows = [
        {"nutrient": n, "goal": g, "basis": b, "source": CURATED_SOURCE}
        for n, g, b in SUPPORTS
    ]
    return goal_rows, link_rows


def seed_knowledge(session) -> None:
    """Idempotently write Goal nodes and SUPPORTS relationships."""
    goal_rows, link_rows = seed_rows()
    session.execute_write(lambda tx: tx.run(
        "UNWIND $rows AS row "
        "MERGE (g:Goal {key: row.key}) "
        "SET g.name = row.name, g.description = row.description, g.source = 'manual_curation'",
        rows=goal_rows).consume())
    session.execute_write(lambda tx: tx.run(
        "UNWIND $rows AS row "
        "MATCH (n:Nutrient {key: row.nutrient}) "
        "MATCH (g:Goal {key: row.goal}) "
        "MERGE (n)-[r:SUPPORTS]->(g) "
        "SET r.basis = row.basis, r.curated = true, r.source = row.source",
        rows=link_rows).consume())
