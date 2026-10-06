// Temporary UI-test data. Numbers are approximate; delete with the mock path in api.js.
import { detectFocusNutrient } from "@/lib/utils";

const food = (food_id, food_name, food_type, nutrition) => ({
  food_id,
  food_name,
  food_type,
  nutrition,
});

const BY_NUTRIENT = {
  protein_g: {
    answer:
      "Several foods in the retrieved nutrition data have high protein values. Yellowfin tuna and raw chicken breast lead the results at roughly 22–24 g of protein, followed by lean bison and farmed Atlantic salmon at about 20–22 g.\n\nThe records differ most in fat: bison and chicken breast are lean, while salmon has substantially more fat and calories for a similar amount of protein.",
    sources: [
      food("mock-001", "Fish, tuna, yellowfin, raw", "Fish", { protein_g: 24.4, calories_kcal: 109, fat_g: 0.49, carbs_g: 0, sodium_mg: 39 }),
      food("mock-002", "Chicken, broilers or fryers, breast, meat only, raw", "Poultry", { protein_g: 22.5, calories_kcal: 120, fat_g: 2.62, carbs_g: 0, sodium_mg: 45 }),
      food("mock-003", "Game meat, bison, separable lean only, raw", "Game meat", { protein_g: 21.62, calories_kcal: 143, fat_g: 2.4, carbs_g: 0, sodium_mg: 57 }),
      food("mock-004", "Fish, salmon, Atlantic, farm raised, raw", "Fish", { protein_g: 20.32, calories_kcal: 208, fat_g: 13.4, carbs_g: 0, sodium_mg: 59 }),
    ],
  },
  calcium_mg: {
    answer:
      "Hard cheese is the richest calcium source in the retrieved records, with parmesan at over 1,100 mg. Calcium-set tofu and canned sardines (eaten with the bones) follow, and plain yogurt provides a smaller but still meaningful amount.\n\nNote the trade-offs: parmesan is also very high in sodium, while tofu offers high calcium with very little.",
    sources: [
      food("mock-101", "Cheese, parmesan, hard", "Dairy", { calcium_mg: 1184, calories_kcal: 392, protein_g: 35.75, fat_g: 25.83, sodium_mg: 1529 }),
      food("mock-102", "Tofu, raw, firm, prepared with calcium sulfate", "Legumes", { calcium_mg: 683, calories_kcal: 144, protein_g: 17.3, fat_g: 8.72, sodium_mg: 14 }),
      food("mock-103", "Fish, sardine, Atlantic, canned in oil, drained, with bone", "Fish", { calcium_mg: 382, calories_kcal: 208, protein_g: 24.62, fat_g: 11.45, sodium_mg: 307 }),
      food("mock-104", "Yogurt, plain, whole milk", "Dairy", { calcium_mg: 121, calories_kcal: 61, protein_g: 3.47, fat_g: 3.25, sodium_mg: 46 }),
    ],
  },
  iron_mg: {
    answer:
      "Shellfish and organ meats provide the most iron in the retrieved records, with cooked clams far ahead at about 14 mg. Beef liver, cooked lentils and raw spinach are also good sources, giving plant-based options alongside animal ones.",
    sources: [
      food("mock-201", "Mollusks, clam, mixed species, cooked, moist heat", "Shellfish", { iron_mg: 13.98, calories_kcal: 148, protein_g: 25.55, fat_g: 1.97, sodium_mg: 112 }),
      food("mock-202", "Beef, variety meats and by-products, liver, raw", "Beef", { iron_mg: 4.9, calories_kcal: 135, protein_g: 20.36, fat_g: 3.63, sodium_mg: 69 }),
      food("mock-203", "Lentils, mature seeds, cooked, boiled, without salt", "Legumes", { iron_mg: 3.33, calories_kcal: 116, protein_g: 9.02, fat_g: 0.38, sodium_mg: 2 }),
      food("mock-204", "Spinach, raw", "Vegetables", { iron_mg: 2.71, calories_kcal: 23, protein_g: 2.86, fat_g: 0.39, sodium_mg: 79 }),
    ],
  },
  vitamin_c_mg: {
    answer:
      "Tropical fruit and bell peppers dominate the vitamin C results. Guava is highest at over 200 mg, followed by raw red sweet pepper, kiwifruit and oranges, all of which are low in calories.",
    sources: [
      food("mock-301", "Guavas, common, raw", "Fruits", { vitamin_c_mg: 228.3, calories_kcal: 68, protein_g: 2.55, fat_g: 0.95, sodium_mg: 2 }),
      food("mock-302", "Peppers, sweet, red, raw", "Vegetables", { vitamin_c_mg: 127.7, calories_kcal: 31, protein_g: 0.99, fat_g: 0.3, sodium_mg: 4 }),
      food("mock-303", "Kiwifruit, green, raw", "Fruits", { vitamin_c_mg: 92.7, calories_kcal: 61, protein_g: 1.14, fat_g: 0.52, sodium_mg: 3 }),
      food("mock-304", "Oranges, raw, all commercial varieties", "Fruits", { vitamin_c_mg: 53.2, calories_kcal: 47, protein_g: 0.94, fat_g: 0.12, sodium_mg: 0 }),
    ],
  },
};

const COMPARE = {
  answer:
    "Per the retrieved records, raw chicken breast and farmed Atlantic salmon have similar protein (about 22.5 g vs 20.3 g), but differ sharply in fat: salmon has roughly 13 g against under 3 g for chicken, which accounts for most of the calorie gap (208 vs 120 kcal).\n\nChicken is the leaner choice per gram of protein; the retrieved salmon record carries more total fat.",
  sources: [
    food("mock-002", "Chicken, broilers or fryers, breast, meat only, raw", "Poultry", { protein_g: 22.5, calories_kcal: 120, fat_g: 2.62, carbs_g: 0, sodium_mg: 45 }),
    food("mock-004", "Fish, salmon, Atlantic, farm raised, raw", "Fish", { protein_g: 20.32, calories_kcal: 208, fat_g: 13.4, carbs_g: 0, sodium_mg: 59 }),
  ],
};

export async function getMockResponse(question) {
  await new Promise((resolve) => setTimeout(resolve, 1200));

  // Type "error" or "fail" in a question to exercise the error state.
  if (/\b(error|fail)\b/i.test(question)) {
    throw new Error("Mock failure");
  }

  const isComparison = /\b(compare|versus|vs)\b/i.test(question);
  const focus = detectFocusNutrient(question);
  const data = isComparison ? COMPARE : BY_NUTRIENT[focus] ?? BY_NUTRIENT.protein_g;

  return {
    question,
    ...data,
    graph_context: [],
    retrieval_metadata: { mock: true },
  };
}
