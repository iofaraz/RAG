export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

export const NUTRIENTS = {
  calories_kcal: { label: "Calories", unit: "kcal" },
  protein_g: { label: "Protein", unit: "g" },
  fat_g: { label: "Fat", unit: "g" },
  carbs_g: { label: "Carbs", unit: "g" },
  fiber_g: { label: "Fiber", unit: "g" },
  sodium_mg: { label: "Sodium", unit: "mg" },
  calcium_mg: { label: "Calcium", unit: "mg" },
  iron_mg: { label: "Iron", unit: "mg" },
  vitamin_c_mg: { label: "Vitamin C", unit: "mg" },
};

// Display order for secondary stats on a card.
export const SECONDARY_ORDER = [
  "calories_kcal",
  "protein_g",
  "fat_g",
  "carbs_g",
  "fiber_g",
  "sodium_mg",
];

const FOCUS_PATTERNS = [
  ["vitamin_c_mg", /vitamin\s*c|ascorbic/i],
  ["protein_g", /protein/i],
  ["calcium_mg", /calcium/i],
  ["iron_mg", /\biron\b/i],
  ["fiber_g", /fib(er|re)/i],
  ["sodium_mg", /sodium|salt/i],
  ["carbs_g", /carb/i],
  ["fat_g", /\bfats?\b/i],
  ["calories_kcal", /calorie|kcal/i],
];

// Returns the nutrient key a question is about, or null (e.g. comparisons).
export function detectFocusNutrient(question) {
  const match = FOCUS_PATTERNS.find(([, pattern]) => pattern.test(question));
  return match ? match[0] : null;
}

export function formatValue(value) {
  return Number(Number(value).toFixed(2)).toString();
}
