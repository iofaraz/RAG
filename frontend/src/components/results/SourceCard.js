import Badge from "@/components/ui/Badge";
import NutrientStat from "./NutrientStat";
import { NUTRIENTS, SECONDARY_ORDER, formatValue } from "@/lib/utils";

export default function SourceCard({ source, rank, focusNutrient }) {
  const {
    food_name,
    name,
    food_id,
    food_type,
    nutrition = {},
    detail,
    score,
  } = source;
  const displayName = food_name ?? name ?? "Nutrition source";

  const primaryKey =
    focusNutrient && nutrition[focusNutrient] != null ? focusNutrient : null;
  const secondaryKeys = SECONDARY_ORDER.filter(
    (key) => key !== primaryKey && nutrition[key] != null,
  ).slice(0, primaryKey ? 3 : 4);
  const primary = primaryKey ? NUTRIENTS[primaryKey] : null;

  return (
    <li className="flex min-w-0 flex-col rounded-2xl border border-line bg-white p-4 shadow-[0_8px_26px_-24px_rgba(25,59,50,0.45)] sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="min-w-0 break-words text-sm font-semibold leading-6 text-ink">{displayName}</h3>
        <span className="shrink-0 rounded-full bg-mint px-2 py-1 text-[11px] font-semibold tabular-nums text-brand">{rank}</span>
      </div>

      {food_type && (
        <p className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
          <Badge>{food_type}</Badge>
          {food_id && <span>ID {food_id}</span>}
        </p>
      )}

      {detail && <p className="mt-3 rounded-xl bg-[#f7f8f4] px-3 py-2.5 text-sm leading-6 text-[#52685c]">{detail}</p>}
      {score != null && (
        <p className="mt-2 text-xs text-muted">Relevance: {Number(score).toFixed(2)}</p>
      )}

      {primary && (
        <div className="mt-4 rounded-xl border border-[#dce8dd] bg-mint/50 px-3.5 py-3">
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
