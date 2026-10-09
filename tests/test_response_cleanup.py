import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.services import rag as rag_service
from rag import rag_pipeline


def test_answer_query_deduplicates_exact_sources_and_preserves_graph_results(monkeypatch):
    graph_results = {
        "results": [
            {"food": "Soy protein isolate", "amount": 88.32, "unit": "g"}
        ],
        "notes": ["Ranked by protein per 100 g."],
    }
    monkeypatch.setattr(
        rag_service,
        "answer_question",
        AsyncMock(
            return_value={
                "answer": "Retrieved foods include bison.",
                "sources": [
                    {
                        "food_name": "Game meat, bison, raw",
                        "nutrition": {"protein": 21.62},
                        "document": "Food: Game meat, bison, raw\nProtein: 21.62 g",
                    },
                    {
                        "food_name": " game meat, BISON, raw ",
                        "nutrition": {"protein": 21.62},
                        "document": "Food: game meat, BISON, raw\nProtein: 21.62 g",
                    },
                    {
                        "food_name": "Game meat, bison, raw",
                        "nutrition": {"protein": 20.0},
                        "document": "Food: Game meat, bison, raw\nProtein: 20.0 g",
                    },
                ],
                "graph_context": graph_results,
            }
        ),
    )

    response = asyncio.run(rag_service.answer_query("What foods are high in protein?"))

    assert response["sources"] == [
        {
            "name": "Game meat, bison, raw",
            "detail": "21.62 g protein",
            "score": None,
            "food_id": None,
            "food_type": None,
            "nutrition": {"protein": 21.62},
            "basis": None,
            "source": None,
        },
        {
            "name": "Game meat, bison, raw",
            "detail": "20.0 g protein",
            "score": None,
            "food_id": None,
            "food_type": None,
            "nutrition": {"protein": 20.0},
            "basis": None,
            "source": None,
        },
    ]
    assert response["graph_results"] is graph_results


def test_rag_prompt_requires_retrieved_context_support(monkeypatch):
    graph_results = {"results": [{"food": "Soy protein isolate", "amount": 88.32}]}
    generate_answer = AsyncMock(return_value="Soy protein isolate contains 88.32 g protein.")
    monkeypatch.setattr(rag_pipeline, "retrieve_foods", lambda _query: [
        {
            "food": "Bison, raw",
            "nutrient": "protein",
            "value": 21.62,
            "document": "Food: Bison, raw\nProtein: 21.62 g",
        }
    ])
    monkeypatch.setattr(rag_pipeline, "retrieve_from_graph", lambda _query: graph_results)
    monkeypatch.setattr(rag_pipeline, "generate_answer", generate_answer)

    asyncio.run(rag_pipeline.answer_question("What foods are high in protein?"))

    prompt = generate_answer.await_args.args[0]
    assert "using ONLY the nutrition data" in prompt
    assert "directly supported by a retrieved record" in prompt
    assert "Do not add general nutrition knowledge" in prompt
    assert "Food: Bison, raw" in prompt
    assert "Soy protein isolate" in prompt


def test_rag_replaces_answer_with_values_outside_retrieved_context(monkeypatch):
    graph_results = {
        "results": [
            {
                "food": "Soy protein isolate",
                "amount": 88.32,
                "unit": "g",
                "nutrient": "Protein",
                "basis": "per 100 g",
            }
        ]
    }
    monkeypatch.setattr(rag_pipeline, "retrieve_foods", lambda _query: [
        {
            "food": "Bison, raw",
            "nutrient": "protein",
            "value": 21.62,
            "document": "Food: Bison, raw\nProtein: 21.62 g",
        }
    ])
    monkeypatch.setattr(rag_pipeline, "retrieve_from_graph", lambda _query: graph_results)
    monkeypatch.setattr(
        rag_pipeline,
        "generate_answer",
        AsyncMock(return_value="Salmon contains 20.32 g protein."),
    )

    response = asyncio.run(rag_pipeline.answer_question("What foods are high in protein?"))

    assert "Salmon" not in response["answer"]
    assert "20.32" not in response["answer"]
    assert "Bison, raw: 21.62 g protein" in response["answer"]
    assert "Soy protein isolate: 88.32 g Protein (per 100 g)" in response["answer"]
    assert response["graph_context"] is graph_results


def test_grounding_check_allows_rounding_of_retrieved_values():
    assert not rag_pipeline._has_unsupported_numbers(
        "Bison contains 19.88 g protein.",
        "Protein: 19.8813 g",
    )


def test_comparison_answer_and_sources_use_the_same_food_records(monkeypatch):
    graph_result = {
        "intent": "food_comparison",
        "entities": {"nutrients": ["protein"], "foods": [
            {"fdc_id": 1, "name": "Chicken breast, raw", "data_type": "foundation_food"},
            {"fdc_id": 2, "name": "Lentils, cooked", "data_type": "sr_legacy_food"},
        ]},
        "results": [
            {"fdc_id": 1, "food": "Chicken breast, raw", "nutrient_key": "protein", "nutrient": "Protein", "amount": 22.5, "unit": "g", "basis": "per 100 g"},
            {"fdc_id": 2, "food": "Lentils, cooked", "nutrient_key": "protein", "nutrient": "Protein", "amount": 9.0, "unit": "g", "basis": "per 100 g"},
        ],
    }
    monkeypatch.setattr(rag_pipeline, "retrieve_foods", lambda _query: [])
    monkeypatch.setattr(rag_pipeline, "retrieve_from_graph", lambda _query: graph_result)
    generate = AsyncMock()
    monkeypatch.setattr(rag_pipeline, "generate_answer", generate)

    result = asyncio.run(rag_pipeline.answer_question("Compare chicken and lentils for protein"))

    assert "Chicken breast, raw | 22.5 g" in result["answer"]
    assert "Lentils, cooked | 9 g" in result["answer"]
    assert "13.5 g more protein" in result["answer"]
    assert [source["food_id"] for source in result["sources"]] == [1, 2]
    assert generate.await_count == 0


@pytest.mark.parametrize(
    ("rows", "expected"),
    [([], "Not available"), ([
        {"fdc_id": 1, "food": "Chicken, raw", "nutrient_key": "protein", "nutrient": "Protein", "amount": 20.0, "unit": "g"},
        {"fdc_id": 2, "food": "Chicken, cooked", "nutrient_key": "protein", "nutrient": "Protein", "amount": 30.0, "unit": "g"},
    ], "Preparation labels differ")],
)
def test_comparison_marks_missing_values_and_preparation_differences(rows, expected):
    result = rag_pipeline._structured_answer({
        "intent": "food_comparison",
        "query": "Compare chicken for protein",
        "entities": {"nutrients": ["protein"], "foods": [
            {"fdc_id": 1, "name": "Chicken, raw"}, {"fdc_id": 2, "name": "Chicken, cooked"},
        ]},
        "results": rows,
    })
    assert expected in result


def test_serving_question_keeps_per_100g_basis_when_portion_data_is_absent():
    answer = rag_pipeline._structured_answer({
        "intent": "food_nutrient_amount",
        "query": "How much protein is in one egg?",
        "entities": {"nutrients": ["protein"]},
        "results": [{"fdc_id": 1, "food": "Egg, whole, raw", "nutrient_key": "protein", "nutrient": "Protein", "amount": 12.6, "unit": "g", "basis": "per 100 g"}],
    })
    assert "12.6 g" in answer
    assert "per 100 g" in answer
    assert "No matching gram-weight portion data is available" in answer


def test_graph_sources_deduplicate_same_food_identifier_and_keep_metadata():
    sources = rag_pipeline._graph_sources({
        "results": [
            {"fdc_id": 12, "food": "Milk", "data_type": "foundation_food", "nutrient_key": "protein", "amount": 3.2, "unit": "g", "basis": "per 100 g", "source": "USDA FoodData Central"},
            {"fdc_id": 12, "food": "Milk", "data_type": "foundation_food", "nutrient_key": "calcium", "amount": 113, "unit": "mg", "basis": "per 100 g", "source": "USDA FoodData Central"},
        ]
    })
    assert len(sources) == 1
    assert sources[0]["food_id"] == 12
    assert sources[0]["nutrition"] == {"protein": 3.2, "calcium": 113}


@pytest.mark.parametrize(
    "answer",
    [
        "| Fish, salmon | 20.32 g protein |",
        "These whole foods provide protein.",
        "Retrieved values range from 78–88 g.",
    ],
)
def test_grounding_check_rejects_unsupported_foods_bases_and_ranges(answer):
    assert rag_pipeline._has_unsupported_numbers(
        answer,
        "Soy protein isolate: 88.32 g protein per 100 g.",
    )
