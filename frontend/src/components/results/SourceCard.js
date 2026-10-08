import Badge from "@/components/ui/Badge";
import NutrientStat from "./NutrientStat";
import { NUTRIENTS, SECONDARY_ORDER, formatValue } from "@/lib/utils";

export default function SourceCard({ source, rank, focusNutrient }) {
  const { food_name, food_id, food_type, nutrition, detail, score } = source;

  const primaryKey =
    focusNutrient && nutrition[focusNutrient] != null ? focusNutrient : null;
  const secondaryKeys = SECONDARY_ORDER.filter(
    (key) => key !== primaryKey && nutrition[key] != null,
  ).slice(0, primaryKey ? 3 : 4);
  const primary = primaryKey ? NUTRIENTS[primaryKey] : null;

  return (
    <li className="flex flex-col rounded-xl border border-line bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold leading-snug text-ink">{food_name}</h3>
        <span className="text-xs tabular-nums text-muted">#{rank}</span>
      </div>

      {food_type && (
        <p className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
          <Badge>{food_type}</Badge>
          {food_id && <span>ID {food_id}</span>}
        </p>
      )}

      {detail && <p className="mt-2 text-sm leading-6 text-muted">{detail}</p>}
      {score != null && (
        <p className="mt-2 text-xs text-muted">Relevance: {Number(score).toFixed(2)}</p>
      )}

      {primary && (
        <div className="mt-4 border-l-2 border-accent pl-3">
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-muted">
            {primary.label}
          </p>
          <p className="text-2xl font-semibold tabular-nums text-ink">
            {formatValue(nutrition[primaryKey])}
            <span className="ml-1 text-sm font-normal text-muted">{primary.unit}</span>
          </p>
        </div>
      )}

      {secondaryKeys.length > 0 && (
        <dl className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(4.5rem,1fr))] gap-3 border-t border-line pt-3">
          {secondaryKeys.map((key) => (
            <NutrientStat key={key} nutrientKey={key} value={nutrition[key]} />
          ))}
        </dl>
      )}
    </li>
  );
}
