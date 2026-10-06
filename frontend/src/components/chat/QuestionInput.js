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
      className="rounded-lg border border-slate-300 bg-white shadow-sm transition focus-within:border-brand focus-within:ring-2 focus-within:ring-accent/40"
    >
      <label htmlFor="question" className="sr-only">
        Your nutrition question
      </label>
      <textarea
        id="question"
        rows={3}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything about foods, nutrients, or nutrition..."
        className="block w-full resize-none rounded-t-lg bg-transparent px-4 pt-4 text-base leading-6 text-ink placeholder:text-slate-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
      />
      <div className="flex items-center justify-between gap-3 px-3 pb-3 pt-1">
        <p className="hidden text-xs text-muted sm:block">
          Enter to ask · Shift+Enter for a new line
        </p>
        <Button type="submit" disabled={disabled || !value.trim()} className="ml-auto">
          {disabled && <Spinner />}
          Ask
        </Button>
      </div>
    </form>
  );
}
