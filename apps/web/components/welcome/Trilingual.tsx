import type { Copy } from "@/lib/ui-copy";

/** Dutch, English and Persian together: the first screen, before the learner has chosen a support language. */
export function Trilingual({ text, className = "" }: { text: Copy; className?: string }) {
  return (
    <span className={`trilingual ${className}`.trim()}>
      <span lang="nl" className="trilingual-nl">
        {text.nl}
      </span>
      <span lang="en" className="trilingual-support">
        {text.en}
      </span>
      <span lang="fa" dir="rtl" className="trilingual-support fa">
        {text.fa}
      </span>
    </span>
  );
}
