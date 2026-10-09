import Button from "@/components/ui/Button";

export default function ErrorState({ onRetry, message }) {
  return (
    <div role="alert" className="rounded-2xl border border-[#efd8cb] bg-[#fff7f1] p-5 sm:p-6">
      <p className="text-sm font-semibold text-[#723f2b]">We couldn&apos;t complete that question.</p>
      <p className="mt-1 text-sm leading-6 text-[#855a48]">
        {message || "The nutrition service is temporarily unavailable. Please try again."}
      </p>
      <Button variant="secondary" size="sm" onClick={onRetry} className="mt-4 rounded-lg border-[#e7cabc] bg-white text-[#723f2b] hover:border-[#d4aa96] hover:bg-[#fffaf7]">
        Try again
      </Button>
    </div>
  );
}
