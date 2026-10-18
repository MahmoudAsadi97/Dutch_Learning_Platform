import { fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { MatchPairsItem } from "@/components/exercise/MatchPairsItem";
import { OrderItem } from "@/components/exercise/OrderItem";
import { SortBinsItem } from "@/components/exercise/SortBinsItem";
import { TilesItem } from "@/components/exercise/TilesItem";
import type { Answer } from "@/lib/client/exercises";

/** The boards are answered whole: each reports its answer only once every part is in place. */

const left = [
  { id: "l1", nl: "de deur" },
  { id: "l2", nl: "het raam" },
];
const right = [
  { id: "r1", en: "the window" },
  { id: "r2", en: "the door" },
];

describe("MatchPairsItem", () => {
  it("pairs a word with a meaning, changes a pair, and answers once every word has one", () => {
    const onDraft = vi.fn();
    render(
      <MatchPairsItem prompt={{ kind: "match_pairs", left, right }} feedback={null} onDraft={onDraft} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /de deur/ }));
    expect(screen.getByRole("button", { name: /de deur/ })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: /the window/ }));
    expect(onDraft).toHaveBeenLastCalledWith(null);
    // the name says what it goes with once, without a gloss of the template repeating it
    expect(screen.getByRole("button", { name: /^the window, hoort bij de deur$/ })).toBeInTheDocument();
    // the door goes with de deur after all: the window is free again
    fireEvent.click(screen.getByRole("button", { name: /^de deur/ }));
    fireEvent.click(screen.getByRole("button", { name: /the door/ }));
    expect(screen.getByRole("button", { name: /^the window$/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /het raam/ }));
    fireEvent.click(screen.getByRole("button", { name: /the window/ }));
    expect(onDraft).toHaveBeenLastCalledWith({ pairs: { l1: "r2", l2: "r1" } });
  });

  it("shows each word's meaning after a skip", () => {
    const card = (en: string) => ({ library_id: "x", term: "", meaning: { en }, example: {} });
    render(
      <MatchPairsItem
        prompt={{ kind: "match_pairs", left, right }}
        feedback={{ outcome: "skipped", cards: { l1: card("the door"), l2: card("the window") } }}
        onDraft={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: /^de deur/ }).closest("li")).toHaveTextContent(
      /Het juiste antwoord.*the door/,
    );
    expect(screen.getByRole("button", { name: /^het raam/ }).closest("li")).toHaveTextContent(/the window/);
  });

  it("shows each pair's result and the right meaning of a wrong one", () => {
    render(
      <MatchPairsItem
        prompt={{ kind: "match_pairs", left, right }}
        feedback={{
          outcome: "incorrect",
          pairs: {
            l1: { given: "r1", correct: "r2", ok: false },
            l2: { given: "r2", correct: "r1", ok: false },
          },
        }}
        onDraft={() => {}}
      />,
    );
    const deur = screen.getByRole("button", { name: /^de deur/ });
    expect(deur).toBeDisabled();
    expect(deur).toHaveAttribute("data-state", "incorrect");
    expect(deur.closest("li")).toHaveTextContent(/Het juiste antwoord.*the door/);
  });
});

describe("SortBinsItem", () => {
  const prompt = {
    kind: "de_het",
    bins: ["de", "het"],
    options: [
      { id: "n1", nl: "huis" },
      { id: "n2", nl: "tafel" },
    ],
  } as const;

  it("answers once every noun has an article", () => {
    const onDraft = vi.fn();
    render(
      <SortBinsItem
        prompt={{ ...prompt, bins: [...prompt.bins], options: [...prompt.options] }}
        feedback={null}
        onDraft={onDraft}
      />,
    );
    fireEvent.click(within(screen.getByRole("group", { name: "huis" })).getByRole("radio", { name: "het" }));
    expect(onDraft).toHaveBeenLastCalledWith(null);
    fireEvent.click(within(screen.getByRole("group", { name: "tafel" })).getByRole("radio", { name: "de" }));
    expect(onDraft).toHaveBeenLastCalledWith({ bins: { n1: "het", n2: "de" } });
  });

  it("names the right article of a noun sorted wrongly", () => {
    render(
      <SortBinsItem
        prompt={{ ...prompt, bins: [...prompt.bins], options: [...prompt.options] }}
        feedback={{
          outcome: "incorrect",
          bins: {
            n1: { given: "de", correct: "het", ok: false },
            n2: { given: "de", correct: "de", ok: true },
          },
        }}
        onDraft={() => {}}
      />,
    );
    expect(
      within(screen.getByRole("group", { name: "huis" })).getByRole("radio", { name: "de" }),
    ).toBeChecked();
    expect(screen.getByText("het huis").closest(".sort-result")).toHaveTextContent(/Het juiste antwoord/);
  });

  it("shows every article after a skip, read-only", () => {
    const card = (term: string) => ({ library_id: "x", term, meaning: {}, example: {} });
    render(
      <SortBinsItem
        prompt={{ ...prompt, bins: [...prompt.bins], options: [...prompt.options] }}
        feedback={{ outcome: "skipped", cards: { n1: card("het huis"), n2: card("de tafel") } }}
        onDraft={() => {}}
      />,
    );
    for (const radio of screen.getAllByRole("radio")) expect(radio).toBeDisabled();
    expect(screen.getByText("het huis")).toBeInTheDocument();
    expect(screen.getByText("de tafel")).toBeInTheDocument();
  });
});

describe("TilesItem", () => {
  const prompt = {
    kind: "sentence_builder",
    tiles: [
      { id: "t2", nl: "woon" },
      { id: "t1", nl: "ik" },
      { id: "t3", nl: "in Gent" },
    ],
    end: ".",
    cue: { en: "I live in Ghent." },
  } as const;

  it("builds the sentence tile by tile, puts a tile back, and keeps the focus on the tiles", () => {
    const onDraft = vi.fn();
    render(<TilesItem prompt={{ ...prompt, tiles: [...prompt.tiles] }} feedback={null} onDraft={onDraft} />);
    const pieces = screen.getByRole("group", { name: "Stukjes" });
    fireEvent.click(within(pieces).getByRole("button", { name: "ik" }));
    // "ik" left the pieces: the piece now in its place has the focus
    expect(within(pieces).getByRole("button", { name: "in Gent" })).toHaveFocus();
    fireEvent.click(within(pieces).getByRole("button", { name: "woon" }));
    const line = screen.getByRole("group", { name: "Jouw zin" });
    fireEvent.click(within(line).getByRole("button", { name: "Leg woon terug" }));
    expect(onDraft).toHaveBeenLastCalledWith(null);
    fireEvent.click(within(pieces).getByRole("button", { name: "in Gent" }));
    fireEvent.click(within(pieces).getByRole("button", { name: "woon" }));
    expect(onDraft).toHaveBeenLastCalledWith({ order: ["t1", "t3", "t2"] });
  });

  it("shows the right sentence when the order went another way", () => {
    render(
      <TilesItem
        prompt={{ ...prompt, tiles: [...prompt.tiles] }}
        feedback={{
          outcome: "incorrect",
          given_order: ["t1", "t3", "t2"],
          order: ["t1", "t2", "t3"],
          first_difference: 1,
          sentence: "Ik woon in Gent.",
        }}
        onDraft={() => {}}
      />,
    );
    expect(screen.getByText("Ik woon in Gent.")).toBeInTheDocument();
    const built = within(screen.getByRole("group", { name: "Jouw zin" })).getAllByRole("button");
    expect(built.map((tile) => tile.getAttribute("data-state"))).toEqual([
      "correct",
      "incorrect",
      "incorrect",
    ]);
  });
});

describe("TilesItem after a skip", () => {
  it("shows only the right sentence", () => {
    render(
      <TilesItem
        prompt={{
          kind: "sentence_builder",
          tiles: [
            { id: "t1", nl: "ik" },
            { id: "t2", nl: "woon" },
          ],
          end: ".",
          cue: null,
        }}
        feedback={{ outcome: "skipped", sentence: "Ik woon." }}
        onDraft={() => {}}
      />,
    );
    expect(screen.queryByRole("group", { name: "Jouw zin" })).not.toBeInTheDocument();
    expect(screen.getByText("Ik woon.")).toBeInTheDocument();
  });
});

describe("OrderItem", () => {
  const prompt = {
    kind: "sentence_order",
    sentences: [
      { id: "s2", nl: "Dan eet ik." },
      { id: "s1", nl: "Ik sta op." },
    ],
  } as const;

  it("is an answer as it stands, and a sentence moves with its own buttons while focus stays", () => {
    const onDraft = vi.fn();
    render(
      <OrderItem
        prompt={{ ...prompt, sentences: [...prompt.sentences] }}
        feedback={null}
        onDraft={onDraft}
      />,
    );
    expect(onDraft).toHaveBeenLastCalledWith({ order: ["s2", "s1"] });
    expect(screen.getByRole("button", { name: "Zet zin 1 hoger" })).toBeDisabled();
    const down = screen.getByRole("button", { name: "Zet zin 1 lager" });
    down.focus();
    fireEvent.click(down);
    expect(onDraft).toHaveBeenLastCalledWith({ order: ["s1", "s2"] });
    // "Dan eet ik." is last now: its down button is off, so focus is on its up button
    expect(screen.getByRole("button", { name: "Zet zin 2 hoger" })).toHaveFocus();
  });

  it("publishes the visible order before focus transfers to the moved sentence", () => {
    const draftAtFocus = vi.fn();
    function Harness() {
      const [draft, setDraft] = useState<Answer | null>(null);
      return (
        <div
          onFocusCapture={(event) => {
            if (event.target instanceof HTMLButtonElement && event.target.dataset.move === "s2:-1")
              draftAtFocus(draft);
          }}
        >
          <OrderItem
            prompt={{ ...prompt, sentences: [...prompt.sentences] }}
            feedback={null}
            onDraft={setDraft}
          />
        </div>
      );
    }
    render(<Harness />);
    const down = screen.getByRole("button", { name: "Zet zin 1 lager" });
    down.focus();
    fireEvent.click(down);
    expect(screen.getAllByRole("listitem")[0]).toHaveTextContent("Ik sta op.");
    expect(screen.getAllByRole("listitem")[1]).toHaveTextContent("Dan eet ik.");
    expect(screen.getByRole("button", { name: "Zet zin 2 hoger" })).toHaveFocus();
    expect(draftAtFocus).toHaveBeenCalledWith({ order: ["s1", "s2"] });
  });

  it("shows the right order with its translation, says where each sentence stood, and keeps a swap neutral", () => {
    render(
      <OrderItem
        prompt={{ ...prompt, sentences: [...prompt.sentences] }}
        feedback={{
          outcome: "almost",
          order: ["s1", "s2"],
          given_order: ["s2", "s1"],
          translation: { en: ["I get up.", "Then I eat."] },
        }}
        onDraft={() => {}}
      />,
    );
    const rows = screen.getAllByRole("listitem");
    expect(rows[0]).toHaveTextContent(/Ik sta op\..*I get up\..*Stond op plaats 2/);
    expect(rows[1]).toHaveTextContent(/Dan eet ik\..*Then I eat\..*Stond op plaats 1/);
    expect(rows.map((row) => row.getAttribute("data-state"))).toEqual(["almost", "almost"]);
  });

  it("shows a skipped ordering's right order without marks for an order never sent", () => {
    render(
      <OrderItem
        prompt={{ ...prompt, sentences: [...prompt.sentences] }}
        feedback={{ outcome: "skipped", order: ["s1", "s2"] }}
        onDraft={() => {}}
      />,
    );
    const rows = screen.getAllByRole("listitem");
    expect(rows.map((row) => row.getAttribute("data-state"))).toEqual(["shown", "shown"]);
    expect(screen.queryByText(/Stond op plaats/)).not.toBeInTheDocument();
  });
});
