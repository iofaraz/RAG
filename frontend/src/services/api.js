import { getMockResponse } from "./mockData";

// Flip to false once FastAPI is up and postQuery() is implemented.
const USE_MOCK = true;
// const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Single entry point for the UI. Components never call fetch directly.
 * Resolves to: { question, answer, sources[], graph_context[], retrieval_metadata }
 */
export async function askQuestion(question) {
  const raw = USE_MOCK ? await getMockResponse(question) : await postQuery(question);
  return normalizeResponse(raw, question);
}

async function postQuery(/* question */) {
  // TODO: connect to FastAPI —
  // const res = await fetch(`${API_BASE_URL}/api/query`, {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ question }),
  // });
  // if (!res.ok) throw new Error(`Query failed: ${res.status}`);
  // return res.json();
  throw new Error("Backend not connected");
}

// The only place that knows the backend schema. Adjust here if it changes.
function normalizeResponse(raw, question) {
  return {
    question: raw.question ?? question,
    answer: raw.answer ?? "",
    sources: (raw.sources ?? []).map((source) => ({
      food_id: source.food_id,
      food_name: source.food_name,
      food_type: source.food_type ?? null,
      // Accept nested `nutrition` or flat numeric fields (protein_g, ...).
      nutrition:
        source.nutrition ??
        Object.fromEntries(
          Object.entries(source).filter(([, value]) => typeof value === "number"),
        ),
    })),
    graph_context: raw.graph_context ?? [],
    retrieval_metadata: raw.retrieval_metadata ?? {},
  };
}
