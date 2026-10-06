export default function EmptyState() {
  return (
    <section className="mb-8 text-center">
      <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        Nutrivault
      </h1>
      <p className="mt-1 text-base font-medium text-brand">AI Nutrition Knowledge</p>
      <p className="mx-auto mt-4 max-w-xl text-[15px] leading-7 text-muted">
        Ask about foods and nutrients. Every answer is generated from retrieved USDA
        nutrition records, shown alongside it so you can check the evidence.
      </p>
    </section>
  );
}
