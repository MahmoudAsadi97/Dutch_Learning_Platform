"use client";

import Link from "next/link";
import { LearningText, type LearningCopy } from "@/components/LanguageSupport";

const phrases: { basic: LearningCopy; intermediate: LearningCopy; advanced: LearningCopy }[] = [
  { basic: { nl: "Kunt u dat herhalen?", en: "Could you repeat that?", fa: "می‌توانید آن را تکرار کنید؟" }, intermediate: { nl: "Bedoelt u dat we op een ander moment afspreken?", en: "Do you mean that we should meet at a different time?", fa: "منظورتان این است که در زمان دیگری قرار بگذاریم؟" }, advanced: { nl: "Als ik u goed begrijp, geldt dit voorstel alleen onder bepaalde voorwaarden.", en: "If I understand correctly, this proposal applies only under certain conditions.", fa: "اگر درست متوجه شده باشم، این پیشنهاد فقط تحت شرایط خاصی صدق می‌کند." } },
  { basic: { nl: "Kunt u wat trager spreken?", en: "Could you speak a little more slowly?", fa: "می‌توانید کمی آهسته‌تر صحبت کنید؟" }, intermediate: { nl: "Ik begrijp uw punt, maar ik zie ook een andere mogelijkheid.", en: "I understand your point, but I also see another possibility.", fa: "منظورتان را می‌فهمم، اما امکان دیگری هم می‌بینم." }, advanced: { nl: "Ik onderschrijf het doel, al roept de uitvoering nog vragen op.", en: "I support the aim, although the implementation still raises questions.", fa: "با هدف موافقم، هرچند اجرای آن هنوز پرسش‌هایی ایجاد می‌کند." } },
  { basic: { nl: "Is dat goed voor u?", en: "Does that work for you?", fa: "این برای شما مناسب است؟" }, intermediate: { nl: "Zullen we de belangrijkste afspraken nog even overlopen?", en: "Shall we go over the main agreements once more?", fa: "قرارهای اصلی را یک بار دیگر مرور کنیم؟" }, advanced: { nl: "Waarover zijn we het eens, en welk punt vraagt nog nader overleg?", en: "What do we agree on, and which point needs further discussion?", fa: "در چه مواردی توافق داریم و کدام نکته هنوز به گفت‌وگوی بیشتری نیاز دارد؟" } },
];

export function CommunicationCoach({ stageId }: { stageId: string }) {
  const band = /c[12]/.test(stageId) || stageId === "b2" ? "advanced" : /b[12]/.test(stageId) ? "intermediate" : "basic";
  return <details className="communication-coach">
    <summary><LearningText text={{ nl: "Van een oefenantwoord naar een echt gesprek", en: "From a practice answer to a real conversation", fa: "از پاسخ تمرینی تا گفت‌وگوی واقعی" }}/></summary>
    <ol className="communication-steps">
      <li><LearningText text={{ nl: "Bepaal je doel: wat moet de ander na jouw antwoord weten of kunnen doen? Kies drie kernwoorden, geen volledig uitgeschreven tekst.", en: "Choose your goal: what should the other person know or be able to do afterwards? Pick three key words, not a full script.", fa: "هدفت را مشخص کن: مخاطب پس از پاسخ تو چه چیزی باید بداند یا بتواند انجام دهد؟ سه واژهٔ کلیدی انتخاب کن، نه یک متن کامل." }}/></li>
      <li><LearningText text={{ nl: "Spreek met de opdracht in beeld en het voorbeeld dicht. Geef een concrete uitleg en stel een passende vervolgvraag.", en: "Keep the task visible and the sample closed. Explain something concrete and ask a relevant follow-up question.", fa: "دستور تمرین را ببین و نمونه را ببند. توضیح مشخصی بده و یک پرسش مرتبط برای ادامهٔ گفت‌وگو بپرس." }}/></li>
      <li><LearningText text={{ nl: "Luister naar je opname. Is je bedoeling duidelijk? Probeer opnieuw met één gerichte verbetering. Een transcript kan fouten bevatten; het is geen uitspraakscore.", en: "Listen back. Is your intention clear? Try again with one focused improvement. A transcript can contain errors; it is not a pronunciation score.", fa: "به ضبطت گوش بده. آیا منظورت روشن است؟ با یک بهبود مشخص دوباره تلاش کن. متن پیاده‌شده ممکن است خطا داشته باشد و نمرهٔ تلفظ نیست." }}/></li>
    </ol>
    <h4>Het gesprek op gang houden</h4><ul className="communication-phrases">{phrases.map((item, index) => <li key={index}><LearningText text={item[band]}/></li>)}</ul>
    <p><LearningText text={{ nl: "Probeer daarna dezelfde vaardigheid met andere personen, tijden of redenen. Zo oefen je flexibel antwoorden.", en: "Then try the same skill with different people, times or reasons to practise responding flexibly.", fa: "سپس همان مهارت را با افراد، زمان‌ها یا دلایل متفاوت تمرین کن تا پاسخ دادن انعطاف‌پذیر را تمرین کنی." }}/></p>
    <Link className="button secondary" href="/missions"><LearningText text={{ nl: "Oefen ook een praktisch gesprek", en: "Practise a practical conversation too", fa: "یک گفت‌وگوی کاربردی هم تمرین کن" }}/></Link><p className="course-note"><LearningText text={{ nl: "Extra rollenspellen hebben hun eigen moeilijkheid en openen geen volgend niveau.", en: "Extra role-plays have their own difficulty and do not unlock the next stage.", fa: "گفت‌وگوهای تکمیلی سطح دشواری خودشان را دارند و مرحلهٔ بعد را باز نمی‌کنند." }}/></p>
  </details>;
}
