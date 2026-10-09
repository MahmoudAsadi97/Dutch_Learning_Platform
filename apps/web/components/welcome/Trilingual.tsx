import { persianReviewed } from "@/lib/client/persian-review";
import type { Copy } from "@/lib/ui-copy";

/**
 * Dutch, English and Persian together: the first screen, before the learner has chosen a support language.
 * Persian sentences wait until a fluent reader has checked their batch (O2); until then `autonym` (the
 * language's own name, "فارسی") lets a Persian reader find their choice.
 */
export function Trilingual({
  text,
  autonym,
  className = "",
}: {
  text: Copy;
  autonym?: string;
  className?: string;
}) {
  const persian = persianReviewed(text) ? text.fa : autonym;
  return (
    <span className={`trilingual ${className}`.trim()}>
      <span lang="nl" className="trilingual-nl">
        {text.nl}
      </span>
      <span lang="en" className="trilingual-support">
        {text.en}
      </span>
      {persian && (
        <span lang="fa" dir="rtl" className="trilingual-support fa">
          {persian}
        </span>
      )}
    </span>
  );
}
