"use client";

import { useState } from "react";

import { Icon, ICON_NAMES } from "@/components/Icon";
import {
  Badge,
  Button,
  ButtonLink,
  Card,
  Cover,
  Dialog,
  EmptyState,
  Field,
  IconTile,
  Input,
  Notice,
  ProgressBar,
  ProgressRing,
  Segmented,
  Select,
  Skeleton,
  SkeletonPanel,
  SkillMeter,
  Stepper,
  Tabs,
  Textarea,
  useToast,
} from "@/components/ui";
import { Illustration } from "@/components/illustrations";
import { ACCENTS } from "@/lib/design/identity";
import { playTone, setTonesEnabled, useTonesEnabled } from "@/lib/client/tones";

type Lens = "lezen" | "luisteren" | "spreken";
type Source = "onderwerpen" | "startles";
type Step = "lezen" | "luisteren" | "spreken" | "schrijven";

/** Every primitive in every state. Served outside production only (app/dev/ui/page.tsx). */
export function UiGallery() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [tab, setTab] = useState<Lens>("lezen");
  const [source, setSource] = useState<Source>("onderwerpen");
  const [step, setStep] = useState<Step>("luisteren");
  const [shakeKey, setShakeKey] = useState(0);
  const { notify } = useToast();
  const tones = useTonesEnabled();

  return (
    <div className="ui-gallery" data-testid="ui-gallery">
      <header className="page-heading">
        <div>
          <p className="eyebrow">Ontwikkeling</p>
          <h1>UI-galerij</h1>
          <p className="muted">Elke primitive in elke staat, in de kleur van de sectie waarin ze staat.</p>
        </div>
      </header>

      <Card aria-labelledby="gallery-accents">
        <h2 id="gallery-accents">Accenten</h2>
        <div className="ui-swatches">
          {ACCENTS.map((accent) => (
            <div className="ui-swatch" data-accent={accent} key={accent}>
              {accent}
              <strong>solid</strong>
            </div>
          ))}
        </div>
      </Card>

      <Card aria-labelledby="gallery-buttons">
        <h2 id="gallery-buttons">Knoppen</h2>
        <div className="ui-row">
          <Button>Primair</Button>
          <Button variant="secondary">Secundair</Button>
          <Button variant="ghost">Stil</Button>
          <Button variant="danger">Verwijderen</Button>
          <Button size="small">Klein</Button>
          <Button icon="arrow" iconEnd>
            Met pictogram
          </Button>
          <Button disabled>Uitgeschakeld</Button>
          <ButtonLink href="/dev/ui" variant="secondary" icon="external">
            Als link
          </ButtonLink>
        </div>
        <div className="ui-row">
          <Button variant="talk" aria-pressed="false">
            Houd ingedrukt en spreek
          </Button>
        </div>
        <div className="ui-row">
          <Button variant="talk" aria-pressed="true">
            Aan het opnemen
          </Button>
        </div>
      </Card>

      <Card aria-labelledby="gallery-overlays">
        <h2 id="gallery-overlays">Dialoog en meldingen</h2>
        <div className="ui-row">
          <Button variant="secondary" data-testid="ui-open-dialog" onClick={() => setDialogOpen(true)}>
            Open een dialoog
          </Button>
          <Button
            variant="secondary"
            data-testid="ui-notify"
            onClick={() => notify("Opgeslagen. Je kunt verder.", { tone: "success" })}
          >
            Toon een melding
          </Button>
          <Button variant="ghost" onClick={() => notify("De verbinding is traag.", { tone: "warning" })}>
            Waarschuwing
          </Button>
        </div>
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          title="Voorbeelddialoog"
          description="Een korte vraag met twee keuzes. Escape sluit, de rest van de pagina is even inert."
          actions={
            <>
              <Button variant="secondary" onClick={() => setDialogOpen(false)}>
                Annuleren
              </Button>
              <Button onClick={() => setDialogOpen(false)}>Ga verder</Button>
            </>
          }
        >
          <p>De tekst van de dialoog. Links erin blijven onder de navigatiebewaking vallen.</p>
        </Dialog>
      </Card>

      <Card aria-labelledby="gallery-navigation">
        <h2 id="gallery-navigation">Tabs, keuzes en stappen</h2>
        <Tabs
          label="Voorbeeldtabs"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "lezen", label: "Lezen", icon: "book", badge: 3 },
            { id: "luisteren", label: "Luisteren", icon: "headphones" },
            { id: "spreken", label: "Spreken", icon: "mic", disabled: true },
          ]}
        />
        <div className="ui-row">
          <Segmented
            label="Oefenmateriaal"
            value={source}
            onChange={setSource}
            options={[
              { value: "onderwerpen", label: "Onderwerpen" },
              { value: "startles", label: "Startles" },
            ]}
          />
        </div>
        <div className="ui-stack">
          <Stepper
            label="Voorbeeldstappen"
            current={step}
            onSelect={setStep}
            steps={[
              { key: "lezen", meta: "Lezen", title: "De herinnering", done: true },
              { key: "luisteren", meta: "Luisteren", title: "De voicemail" },
              { key: "spreken", meta: "Spreken", title: "Het telefoongesprek" },
              { key: "schrijven", meta: "Schrijven", title: "Het bericht" },
            ]}
          />
        </div>
      </Card>

      <Card aria-labelledby="gallery-motion">
        <h2 id="gallery-motion">Beweging</h2>
        <div className="ui-row">
          <div className="ui-swatch" data-accent="progress" data-anim="pop">
            pop
          </div>
          <div className="ui-swatch" data-accent="today" data-anim="rise">
            rise
          </div>
          <div className="ui-swatch" data-accent="stories" data-anim="burst">
            burst
          </div>
          <div className="ui-swatch" data-accent="writing" data-anim="shake" key={shakeKey}>
            shake
          </div>
          <Button variant="secondary" size="small" onClick={() => setShakeKey((value) => value + 1)}>
            Schud opnieuw
          </Button>
        </div>
        <div className="ui-row">
          <IconTile name="mic" accent="speaking" data-anim="pulse" aria-label="opname" role="img" />
          <span className="writing-dots" data-anim="dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <Button variant="secondary" size="small" data-press>
            Drukgedrag
          </Button>
          <div className="ui-swatch" data-accent="neutral" data-lift>
            lift
          </div>
        </div>
      </Card>

      <Card aria-labelledby="gallery-sound">
        <h2 id="gallery-sound">Geluid</h2>
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={tones}
            onChange={(event) => setTonesEnabled(event.target.checked)}
          />
          <span>Korte geluidjes bij een antwoord en bij je dagdoel</span>
        </label>
        <div className="ui-row">
          <Button variant="secondary" size="small" onClick={() => playTone("correct")}>
            Juist
          </Button>
          <Button variant="secondary" size="small" onClick={() => playTone("almost")}>
            Bijna
          </Button>
          <Button variant="secondary" size="small" onClick={() => playTone("goal")}>
            Dagdoel
          </Button>
        </div>
      </Card>

      <Card aria-labelledby="gallery-badges">
        <h2 id="gallery-badges">Labels</h2>
        <div className="ui-row">
          <Badge>Neutraal</Badge>
          <Badge tone="ok">Nagekeken</Badge>
          <Badge tone="warn">Wacht op controle</Badge>
          <Badge tone="bad">Mislukt</Badge>
          <Badge tone="info">Nieuw</Badge>
          <Badge tone="accent">Sectie</Badge>
        </div>
      </Card>

      <Card aria-labelledby="gallery-notices">
        <h2 id="gallery-notices">Meldingen in de pagina</h2>
        <div className="ui-stack">
          <Notice title="Zonder toon">Een rustige mededeling zonder pictogram.</Notice>
          <Notice tone="info" title="Goed om te weten">
            De schrijver werkt aan je volgende aflevering.
          </Notice>
          <Notice tone="success" title="Juist">
            <p>Precies. Je antwoord klopt met de tekst.</p>
          </Notice>
          <Notice tone="warning" title="Bijna">
            <p>Let op het lidwoord: het is de sleutel.</p>
          </Notice>
          <Notice tone="danger" title="Niet gelukt">
            <p>De opname kon niet worden bewaard. Probeer opnieuw.</p>
          </Notice>
        </div>
      </Card>

      <Card aria-labelledby="gallery-tiles">
        <h2 id="gallery-tiles">Pictogramtegels</h2>
        <div className="ui-row">
          {ACCENTS.map((accent) => (
            <IconTile key={accent} name="sparkles" accent={accent} aria-label={accent} role="img" />
          ))}
        </div>
        <div className="ui-row">
          <IconTile name="book" size="small" accent="reading" />
          <IconTile name="mic" solid accent="speaking" />
        </div>
      </Card>

      <Card aria-labelledby="gallery-fields">
        <h2 id="gallery-fields">Velden</h2>
        <div className="ui-stack">
          <Field label="Je naam" hint="Zoals je aangesproken wilt worden.">
            {(control) => <Input {...control} placeholder="bv. Sami" />}
          </Field>
          <Field label="Niveau">
            {(control) => (
              <Select {...control} defaultValue="a1">
                <option value="pre-a1">pre-A1</option>
                <option value="a1">A1</option>
                <option value="a2">A2</option>
              </Select>
            )}
          </Field>
          <Field label="Je bericht" error="Schrijf minstens één zin.">
            {(control) => <Textarea {...control} defaultValue="Beste" />}
          </Field>
          <Field label="Niet beschikbaar">
            {(control) => <Input {...control} disabled defaultValue="Later" />}
          </Field>
        </div>
      </Card>

      <Card aria-labelledby="gallery-progress">
        <h2 id="gallery-progress">Voortgang</h2>
        <div className="ui-row">
          <ProgressRing value={0} max={20} label="0 van 20 punten" tone="warm">
            <span className="streak-number">0</span>
            <span className="streak-label">dagen op rij</span>
          </ProgressRing>
          <ProgressRing value={12} max={20} label="12 van 20 punten" tone="warm" size={110}>
            <span className="streak-number">4</span>
            <span className="streak-label">dagen op rij</span>
          </ProgressRing>
          <ProgressRing value={20} max={20} label="20 van 20 punten" tone="success" size={90} progressbar>
            <span className="streak-number">9</span>
          </ProgressRing>
        </div>
        <div className="ui-stack">
          <ProgressBar value={7} max={12} label="Afgeronde niveaus" />
          <ProgressBar value={3} max={5} label="Onderwerpen" size="thin" tone="warm" />
          <SkillMeter done={{ reading: true, listening: true }} />
        </div>
        <div className="ui-row">
          <Cover number={3} caption="De Lindestraat" className="ui-cover" />
          <Cover number={6} className="ui-cover" />
          {(["writer", "stories", "goal", "words", "quiet"] as const).map((name) => (
            <span key={name} data-accent="stories">
              <Illustration name={name} size={64} />
            </span>
          ))}
        </div>
      </Card>

      <Card aria-labelledby="gallery-loading">
        <h2 id="gallery-loading">Laden en leeg</h2>
        <SkeletonPanel>
          <Skeleton lines={3} />
          <div className="ui-row">
            <Skeleton kind="circle" />
            <Skeleton kind="block" width="60%" height={48} />
          </div>
        </SkeletonPanel>
        <EmptyState
          icon="book"
          accent="stories"
          title="Nog geen verhalen"
          description="Je eerste aflevering wordt geschreven zodra je je niveau kiest."
        >
          <Button variant="secondary" size="small">
            Kies een niveau
          </Button>
        </EmptyState>
      </Card>

      <Card tone="tinted" aria-labelledby="gallery-cards" data-accent="progress">
        <h2 id="gallery-cards">Kaart met tint</h2>
        <p>Een getinte kaart volgt het accent van haar sectie.</p>
      </Card>

      <Card aria-labelledby="gallery-icons">
        <h2 id="gallery-icons">Pictogrammen</h2>
        <div className="ui-icons">
          {ICON_NAMES.map((name) => (
            <div key={name}>
              <Icon name={name} size={22} />
              {name}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
