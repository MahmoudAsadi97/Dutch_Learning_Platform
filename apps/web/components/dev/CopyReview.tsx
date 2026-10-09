"use client";

import { COPY_BATCHES } from "@/lib/client/persian-review";
import { PERSIAN_REVIEWED } from "@/lib/copy/review";

/**
 * Every batch of interface copy side by side, for the fluent reader who checks the Persian (O2). A batch
 * marked "nog niet nagekeken" keeps its Persian hidden from learners until lib/copy/review.ts says true.
 */
export function CopyReview() {
  const names = Object.keys(COPY_BATCHES).sort();
  return (
    <div className="copy-review" data-testid="copy-review">
      <header className="page-heading">
        <div>
          <p className="eyebrow">ONTWIKKELING</p>
          <h1>Interfaceteksten nakijken</h1>
          <p>
            Lees per groep het Perzisch na. Zet daarna de groep op <code>true</code> in{" "}
            <code>lib/copy/review.ts</code>; tot dan zien leerders het Perzisch van die groep niet.
          </p>
        </div>
      </header>
      <nav aria-label="Groepen" className="copy-review-index">
        {names.map((name) => (
          <a key={name} href={`#copy-${name}`}>
            {name} {PERSIAN_REVIEWED[name] ? "✓" : ""}
          </a>
        ))}
      </nav>
      {names.map((name) => {
        const entries = Object.entries(COPY_BATCHES[name]);
        return (
          <section key={name} id={`copy-${name}`} className="card" aria-labelledby={`copy-${name}-title`}>
            <h2 id={`copy-${name}-title`}>
              {name} · {entries.length} teksten ·{" "}
              {PERSIAN_REVIEWED[name] ? "Perzisch nagekeken" : "Perzisch nog niet nagekeken"}
            </h2>
            <div className="copy-review-table">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Sleutel</th>
                    <th scope="col">Nederlands</th>
                    <th scope="col">English</th>
                    <th scope="col">فارسی</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map(([key, copy]) => (
                    <tr key={key}>
                      <th scope="row">
                        <code>{key}</code>
                      </th>
                      <td lang="nl">{copy.nl}</td>
                      <td lang="en">{copy.en}</td>
                      <td lang="fa" dir="rtl">
                        {copy.fa}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}
    </div>
  );
}
