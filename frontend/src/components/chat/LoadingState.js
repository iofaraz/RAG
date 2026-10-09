import Spinner from "@/components/ui/Spinner";

export default function LoadingState() {
  return (
    <div
      role="status"
      className="flex items-center gap-3 rounded-2xl border border-[#dce6dc] bg-mint/60 px-4 py-4 text-sm text-brand"
    >
      <Spinner />
      <span className="font-medium">Searching nutrition records and preparing your answer...</span>
    </div>
  );
}
