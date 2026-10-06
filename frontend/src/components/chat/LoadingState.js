import Spinner from "@/components/ui/Spinner";

export default function LoadingState() {
  return (
    <div
      role="status"
      className="flex items-center gap-3 rounded-xl border border-line bg-slate-50 px-4 py-3 text-sm text-muted"
    >
      <Spinner />
      <span>Analyzing nutrition data...</span>
    </div>
  );
}
