from rag_pipeline import answer_question


questions = [
    "What foods are high in protein?",
    "Which foods are rich in calcium?",
    "Which foods contain a lot of iron?"
]


for question in questions:

    print("\n" + "=" * 70)
    print("QUESTION")
    print("=" * 70)
    print(question)

    result = answer_question(question)

    print("\n" + "=" * 70)
    print("AI ANSWER")
    print("=" * 70)
    print(result["answer"])

    print("\n" + "=" * 70)
    print("SOURCES")
    print("=" * 70)

    for source in result["sources"]:
        print(
            f"- {source['food_name']} "
            f"({source['nutrition']})"
        )