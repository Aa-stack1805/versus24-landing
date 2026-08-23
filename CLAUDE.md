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

### AI sport coaching

Shipped in v1.3. The AI stopped refusing to program sport skill work. It is two
per-sport switches ("I have a coach for this", "let Sensei program my skill
work"), both off by default. Coach plus AI gives complement mode: solo homework
only, nothing needing a partner, about 60% of full-mode minutes, and the
athlete's coached sessions counted against the same budget. Generation is
Elite; the drill library, running drills by hand and skill tree credit are free
on every tier. Fourteen sports, 415 drills. **Combat is a later release, so
nothing on the site may promise it**, which is why `fighters.html` is untouched
and both pages say combat follows.

The load model: three separate budgets (jump landings, hard cuts, sprint
metres), built from age, mass, lifting history, recent load and recovery, with
the athlete's own games charged against them. Injuries remove classes of drill
rather than adding a warning. Never describe it as preventing or predicting
injury, for the same reason the rings are not described that way.

**Owed on the sports and features pages: three captures.** The weekly plan card
and the drill runner (`sports.html`), and the two-switch setup
(`features.html`). Those sections shipped as full-width text rather than with
placeholder frames, so nothing looks unfinished; when the captures exist, add a
`hero-visual` phone block back and put `feature-split` on the section's
container to stand it beside the copy, the way the readiness section does.

**Unverified copy.** The "longer arc" section on `sports.html` describes
six-week blocks, field tests and an end-of-block review. Blocks and the review
come from the progression engine's own rules (a focus is dropped after three
weeks without progress and never outstays six). **Field tests were named in an
app audit but never described to whoever wrote this copy**, so the bullet
claims only that a short test is asked for periodically and that the next block
is built on the result. Verify it and rewrite with the real tests if wrong.

### ACWR, and what the rings mean

The app's three rings were rebuilt for v1.2. The inner ring stopped being an
acute:chronic workload ratio gauge and became Balance: full when every system
you train sits near your own baseline, draining only on a spike, unaffected by
rest days. Readiness became a pure recovery measure (subjective, HRV, sleep);
training volume left the score entirely.

The copy is now written for v1.2. Readiness is described as recovery only
(check-in, HRV, sleep), workload as own-baseline and per-system, and ACWR is
down to a single mention on `features.html`, kept for credibility and search
and framed as research context rather than an injury predictor. Do not
reintroduce it as a headline feature: the ratio is the part the 2020–2021
methodology papers took apart, and own-baseline deviation is the part that
survived. Do not put a number of check-in questions or a baseline window in
the copy either, unless you have just checked it against the app.

**Still owed: two screenshots.** These predate v1.2 and show the old ring set.
Alt text describes what is in the image, so it is correct as long as the old
image is there. Replace the image and the alt together:

- `assets/screens/screen-watch-readiness.webp` on `features.html`, alt calling
  the inner ring blue. On the phone, Balance renders blue, so that wording is
  probably right; check it against the new capture rather than assuming.
- `assets/screens/screen-dashboard.webp` on `features.html`, whose alt quotes
  an on-screen callout saying the readiness score adapts to load. It no
  longer does.

Done: `readiness.webp` (900x1045, home/sports/fighters) and
`screen-readiness.webp` (900x1948, features) were rebuilt from a v1.2 capture.
Both come from one 1242x2688 screenshot; `readiness.webp` is the region from
just above the rings to just below the stat bubbles, cropped to the same
aspect the old file used so the framing did not change. That capture has no
check-in behind it, so Balance reads as a dash and a "check in for accurate
scores" prompt sits under the rings. The alt text says so. If a populated
capture turns up later, both files and all three alts want redoing together.

The v1.0 changelog entry naming ACWR is a historical record. Leave it.
