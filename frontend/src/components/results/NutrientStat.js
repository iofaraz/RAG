import { NUTRIENTS, formatValue } from "@/lib/utils";

export default function NutrientStat({ nutrientKey, value }) {
  const { label, unit } = NUTRIENTS[nutrientKey] ?? { label: nutrientKey, unit: "" };
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="text-sm font-medium tabular-nums text-ink">
        {formatValue(value)} <span className="text-xs font-normal text-muted">{unit}</span>
      </dd>
    </div>
  );
}
