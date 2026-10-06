import SectionLabel from "@/components/ui/SectionLabel";

export default function UserQuestion({ question }) {
  return (
    <section>
      <SectionLabel>Question</SectionLabel>
      <p className="mt-2 text-xl font-semibold leading-snug text-ink">{question}</p>
    </section>
  );
}
