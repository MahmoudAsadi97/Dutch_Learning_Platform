import { SpeechCheck } from "@/components/SpeechCheck";

export default function SpeechCheckPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">EERST EVEN PROBEREN</p>
          <h1>Jouw stem. Jouw Nederlands.</h1>
          <p>
            Test je microfoon, bekijk de transcriptie en luister naar een
            gesproken voorbeeld.
          </p>
        </div>
        <span className="quiet-badge">Microfoontest</span>
      </header>
      <aside className="information-callout">
        <div>
          <h3>Een rustige plek maakt het verschil.</h3>
          <p>
            Geef je browser toegang tot de microfoon. Gebruik bij voorkeur een
            hoofdtelefoon. Deze test geeft geen uitspraakscore en beoordeelt je
            accent niet.
          </p>
        </div>
      </aside>
      <SpeechCheck />
    </>
  );
}
