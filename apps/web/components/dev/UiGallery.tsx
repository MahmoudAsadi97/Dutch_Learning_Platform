import { Icon, ICON_NAMES } from "@/components/Icon";
import {
  Badge,
  Button,
  ButtonLink,
  Card,
  EmptyState,
  Field,
  IconTile,
  Input,
  Notice,
  Select,
  Skeleton,
  SkeletonPanel,
  Textarea,
} from "@/components/ui";
import { ACCENTS } from "@/lib/design/identity";

/** Every primitive in every state. Served outside production only (app/dev/ui/page.tsx). */
export function UiGallery() {
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
        <h2 id="gallery-notices">Meldingen</h2>
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
