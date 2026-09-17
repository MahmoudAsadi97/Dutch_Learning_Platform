import { SpeechCheck } from "@/components/SpeechCheck";

export default function SpeechCheckPage() {
  return (
    <>
      <h1>Microfoontest</h1>
      <p className="muted">
        Controleert de volledige spraakketen op deze computer: microfoon → upload → ffmpeg → lokale transcriptie, en synthetische
        weergave.
      </p>
      <SpeechCheck />
    </>
  );
}
