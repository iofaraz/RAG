import Spinner from "@/components/ui/Spinner";

export default function LoadingState() {
  return (
    <div role="status" className="flex items-center gap-3 text-sm text-muted">
      <Spinner />
      Analyzing nutrition data…
    </div>
  );
}
