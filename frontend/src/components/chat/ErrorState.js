import Button from "@/components/ui/Button";

export default function ErrorState({ onRetry }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-5">
      <p className="text-sm font-semibold text-red-900">Unable to process your question.</p>
      <p className="mt-1 text-[15px] text-red-700">Please try again.</p>
      <Button variant="secondary" size="sm" onClick={onRetry} className="mt-4">
        Try again
      </Button>
    </div>
  );
}
