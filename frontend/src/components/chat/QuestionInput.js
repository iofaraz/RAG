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
      className="overflow-hidden rounded-2xl border border-[#d8e0d6] bg-white shadow-[0_18px_50px_-36px_rgba(25,59,50,0.55)] transition-all focus-within:border-accent focus-within:ring-4 focus-within:ring-accent/10"
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
        placeholder="Ask a nutrition question, for example: Which foods are high in calcium?"
        className="block min-h-[88px] w-full resize-y bg-transparent px-5 py-4 text-base leading-7 text-ink placeholder:text-[#89958d] focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 sm:px-6"
      />
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line bg-[#fbfcf9] px-4 py-3 sm:px-5">
        <p className="text-xs text-muted">
          Enter to ask <span aria-hidden="true">·</span> Shift+Enter for a new line
        </p>
        <Button
          type="submit"
          disabled={disabled || !value.trim()}
          className="ml-auto min-w-[118px] rounded-xl"
        >
          {disabled ? (
            <>
              <Spinner />
              <span>Thinking...</span>
            </>
          ) : (
            <>
              <span>Ask Nutrix</span>
              <svg viewBox="0 0 20 20" fill="none" className="size-4" aria-hidden="true">
                <path d="M4 10h11m-4-4 4 4-4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
