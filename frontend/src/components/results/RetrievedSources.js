import SectionLabel from "@/components/ui/SectionLabel";
import SourceCard from "./SourceCard";

export default function RetrievedSources({ sources, focusNutrient }) {
  if (sources.length === 0) return null;

  return (
    <section>
      <SectionLabel>Supporting nutrition data</SectionLabel>
      <p className="mt-1 text-sm text-muted">
        Based on retrieved nutrition sources · {sources.length} record
        {sources.length === 1 ? "" : "s"}
      </p>
      <ol className="mt-4 grid gap-3 sm:grid-cols-2">
        {sources.map((source, index) => (
          <SourceCard
            key={source.food_id}
            source={source}
            rank={index + 1}
            focusNutrient={focusNutrient}
          />
        ))}
      </ol>
    </section>
  );
}
