export default function Badge({ children }) {
  return (
    <span className="rounded border border-line bg-surface px-1.5 py-0.5 text-xs font-medium text-brand">
      {children}
    </span>
  );
}
