# Versus Training site: working notes

## Writing rules

**No em dashes.** Never use `—` (U+2014) anywhere: page copy, headings, alt
text, meta descriptions, JSON-LD, CSS `content`, code comments, or commit
messages. They read as AI-generated. Use a colon, a comma, parentheses, or a
full stop instead, and prefer splitting the sentence where that reads better.

Also avoid the other tells: "delve", "in today's fast-paced world", "unlock
the power of", "it's not just X, it's Y", and paragraphs that open with
"Whether you're...".

Numeric ranges use an en dash (`0–100`, `2–3%`) or the word "to". That is
correct typography, not the thing being banned.

## Units

Body measurements in page copy ship metric and convert for imperial locales
(US, LR, MM) at runtime. Wrap the value so `assets/script.js` can find it:

    <span data-measure="38" data-unit="cm">38 cm</span>

Supported units are `cm` (to inches) and `kg` (to pounds); values round to the
nearest whole unit. Do **not** tag numbers inside screenshot `alt` text: alt
text describes what is on the screen, and the app renders metric.

## Build

Pages are assembled from `src/pages/` + `src/partials/` by
`scripts/build_site.py`. Always run it after editing `src/`, then verify with
`python3 scripts/build_site.py --check` (exits non-zero if the committed HTML
has drifted from source). Never hand-edit the built files at the repo root.

## Invite links

App builds hand out `https://versus24.net/r/{code}`. GitHub Pages has no
wildcard routing, so that path is served by `404.html`, with a 404 status;
`/r/` is a real 200 page. Both render from `assets/referral.js`, which also
accepts `?c=CODE` and `#CODE`. New app builds should use `/r/#CODE`: it
returns 200, so messaging apps will build a link preview for it.

`.well-known/apple-app-site-association` is what makes those links open the
app. Two things about it:

- It is not built from `src/`, and it fails silently: links keep working in a
  browser and simply stop opening the app. `build_site.py` asserts it is
  present, parses, and covers `/r`, `/r/` and `/r/*`. Bare `/r` needs its own
  entry because link shorteners strip trailing slashes and iOS matches the URL
  as sent, before any redirect.
- Editing it is slow to take effect: Apple's CDN takes up to a day to reach new
  installs and about a week for existing ones, with no way to purge. Diagnose
  first, then make one change. `curl -s -D- https://app-site-association.cdn-apple.com/a/v1/versus24.net`
  shows what Apple actually ingested.

Deleting `.nojekyll`, or switching Pages from branch deploys to the Actions
flow, drops the whole `.well-known` directory. The build guard catches the
first; nothing catches the second, so do not switch without checking.

Ignore advice that the file must be served as `application/json`. Apple's
current docs and TN3155 do not require it, and since iOS 14 the device reads a
normalised copy from Apple's CDN, which sniffs the body. GitHub Pages serves it
as `application/octet-stream` and that is fine.

## Design

The art direction is "the training log": type carries the page, colour is a
signal rather than decoration. Gold marks structure; the five modality colours
only ever encode a modality. No gradient-filled text, no glow, no film grain,
no uniform hover-lift on cards. See the header comment in `assets/style.css`.

## Facts

Product claims must match the app. Currently: 17 martial arts in the skill
tree (beginner level on Free, all belts on Core/Elite), 14 sports, 8 Vanity
Vault check-ins on Free, 12 body measurements. AI Meal Scan and the Physique
Report Card are Elite. Prices are per App Store storefront; US and India are
both defined in `assets/script.js`.

### ACWR, and what the rings mean

The app's three rings were rebuilt for v1.2. The inner ring stopped being an
acute:chronic workload ratio gauge and became Balance: full when every system
you train sits near your own baseline, draining only on a spike, unaffected by
rest days. Readiness became a pure recovery measure (subjective, HRV, sleep);
training volume left the score entirely.

The site is written for the **shipped** build, so it still describes readiness
as including recent load. Everything else has already moved to own-baseline
workload language, which is true of both builds, and ACWR is down to a single
mention on `features.html` (kept for credibility and search, framed as a
research metric rather than an injury predictor). Do not reintroduce it as a
headline feature: the ratio is the part the 2020–2021 methodology papers took
apart, and own-baseline deviation is the part that survived.

**Flip these on the day v1.2 ships**, once new screenshots exist:

- `src/pages/index.html`: readiness composition bullet in "What readiness and
  workload are"; the `readiness.webp` alt and the figcaption quoting
  "Load 1797, ACWR 1.04".
- `src/pages/fighters.html`: readiness composition bullet.
- `src/pages/features.html`: the "reads HRV, sleep, RHR, training load" and
  "four signals your watch measured" sentences; the `screen-readiness.webp`
  alt naming the Score/Load/ACWR rings.
- `src/pages/sports.html`: the `readiness.webp` alt.
- `src/pages/changelog.html`: move v1.2 from Planned to Shipped, and bump
  `softwareVersion` in the JSON-LD.

The v1.0 changelog entry naming ACWR is a historical record. Leave it.
