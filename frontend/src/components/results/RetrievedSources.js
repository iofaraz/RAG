import SectionLabel from "@/components/ui/SectionLabel";
import SourceCard from "./SourceCard";

export default function RetrievedSources({ sources, focusNutrient }) {
  return (
    <section aria-labelledby="supporting-data-heading" className="rounded-2xl border border-line bg-[#fbfcf9] p-4 sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <SectionLabel>
            <span id="supporting-data-heading">Retrieved nutrition records</span>
          </SectionLabel>
          <p className="mt-1 text-sm text-muted">
            Source details returned for this question. They may not support every statement in the AI answer.
          </p>
        </div>
        <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-muted ring-1 ring-line">
          {sources.length} record{sources.length === 1 ? "" : "s"}
        </span>
      </div>

      {sources.length > 0 ? (
        <ol className="mt-4 grid gap-3 sm:grid-cols-2">
          {sources.map((source, index) => (
            <SourceCard
              key={source.food_id ?? `${source.food_name ?? source.name}-${index}`}
              source={source}
              rank={index + 1}
              focusNutrient={focusNutrient}
            />
          ))}
        </ol>
      ) : (
        <p className="mt-4 rounded-xl border border-dashed border-line bg-white px-4 py-5 text-sm leading-6 text-muted">
          No supporting nutrition records were returned for this answer.
        </p>
      )}
    </section>
  );
}
