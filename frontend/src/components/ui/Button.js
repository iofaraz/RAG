import { cn } from "@/lib/utils";

const VARIANTS = {
  primary:
    "bg-ink text-white hover:bg-brand disabled:bg-slate-300 disabled:text-slate-600",
  secondary:
    "border border-line bg-white text-ink hover:border-brand hover:text-brand disabled:text-slate-400 disabled:hover:border-line disabled:hover:text-slate-400",
};

const SIZES = {
  md: "h-10 px-5 text-sm font-medium",
  sm: "px-3 py-1.5 text-sm",
};

export default function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md transition-colors disabled:cursor-not-allowed",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
