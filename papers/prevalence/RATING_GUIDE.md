# Rating guide

Written before any rating (PROTOCOL.md §6). Raters work from the item
alone: they don't see other raters' answers, the package's rank or its
dependent counts. Each rating records the rater's identifier, the time,
the answer and one line of evidence (a quotation or a URL).

## Task A: archived repositories

**Item:** one archived GitHub repository from the *Top* stratum, with its
README, description and the package's registry page.

**Question:** what does the repository or the registry say about the code's
future?

| Answer | Use when | Example evidence |
|---|---|---|
| `moved` | It names a successor location for the same code: another repository, a monorepo path, a fork it endorses | "This package now lives in https://github.com/org/monorepo/packages/x" |
| `deprecated` | It says the code is no longer maintained or should not be used, and names no successor location | "This project is no longer maintained." |
| `replaced` | It recommends a *different* project instead | "Use the built-in `fetch` instead." |
| `unstated` | It says nothing about the future, or the README is missing | — |

Rules:
- Rate what the text says, not what you know from elsewhere.
- If both `moved` and `deprecated` apply ("deprecated; v2 lives at …"),
  choose `moved`.
- `replaced` needs a recommendation, not just a mention of another project.

## Task B: advisory and lifecycle signals

**Item:** one package and one matched record: an OSV advisory (its summary
and details) or an endoflife.date product page. Unmatched items show the
package's OSV records, if any, and the endoflife.date search result.

**Question:** does this record tell a consumer that *this package's* code
is unmaintained, archived, relocated or past end of life?

| Answer | Use when |
|---|---|
| `yes` | The record states it about this package (or the product this package is) |
| `no-other` | The matched term concerns something else: a deprecated API, a dependency, another product |
| `no` | Nothing in the record concerns maintenance or location |

For unmatched items, `yes` means the lexical match missed a real signal.

## Agreement

Two raters per item. Disagreements go to a third rater, who sees both
answers and evidence lines. The paper reports Cohen's κ before
adjudication and the adjudicated answer. At least one of the two first
raters is not the author; a rating by a language model is not an
independent rating, and is labelled as such if used at all.
