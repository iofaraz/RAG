import Button from "@/components/ui/Button";

export default function ErrorState({ onRetry }) {
  return (
    <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-5">
      <p className="text-sm font-semibold text-red-900">Error</p>
      <p className="mt-1 text-[15px] text-red-900">
        Something went wrong while processing your question.
      </p>
      <Button variant="secondary" size="sm" onClick={onRetry} className="mt-4">
        Try again
      </Button>
    </div>
  );
}
