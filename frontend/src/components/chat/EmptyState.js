export default function EmptyState() {
  return (
    <section className="mb-6 text-center sm:mb-8">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-[2.6rem]">
          Ask your nutrition question
        </h1>
        <p className="mt-3 text-base text-muted sm:text-lg">
          Get AI-powered answers grounded in retrieved nutrition data.
        </p>
        <p className="mx-auto mt-5 max-w-xl text-[15px] leading-7 text-muted">
          Ask about foods, nutrients, and nutrition. Answers are grounded in
          retrieved nutrition data and supported by the underlying sources.
        </p>
      </div>
    </section>
  );
}
