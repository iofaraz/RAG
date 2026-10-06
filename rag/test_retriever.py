from retriever import retrieve_foods


questions = [
    "What foods are high in protein?",
    "Which foods are rich in calcium?",
    "Which foods contain a lot of iron?"
]


for question in questions:

    print("\n" + "=" * 70)
    print(question)
    print("=" * 70)

    results = retrieve_foods(question)

    for i, result in enumerate(results, start=1):

        print(
            f"{i}. {result['food']} "
            f"— {result['value']} "
            f"({result['nutrient']})"
        )