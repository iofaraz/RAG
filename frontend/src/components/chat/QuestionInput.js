import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";

export default function QuestionInput({ value, onChange, onSubmit, disabled }) {
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      onSubmit();
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="overflow-hidden rounded-xl border border-line bg-white shadow-sm transition-all focus-within:border-brand/80 focus-within:ring-2 focus-within:ring-accent/25"
    >
      <label htmlFor="question" className="sr-only">
        Your nutrition question
      </label>
      <textarea
        id="question"
        rows={4}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about foods, nutrients, or nutrition..."
        className="block min-h-[96px] w-full resize-none bg-transparent px-4 py-3 text-base leading-6 text-ink placeholder:text-slate-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
      />
      <div className="flex items-center justify-between gap-3 border-t border-line bg-slate-50/70 px-3 py-3">
        <p className="hidden text-[11px] font-medium uppercase tracking-[0.12em] text-muted sm:block">
          Enter to ask · Shift+Enter for a new line
        </p>
        <Button
          type="submit"
          disabled={disabled || !value.trim()}
          className="ml-auto min-w-[110px]"
        >
          {disabled ? (
            <>
              <Spinner />
              <span>Thinking...</span>
            </>
          ) : (
            "Ask"
          )}
        </Button>
      </div>
    </form>
  );
}
