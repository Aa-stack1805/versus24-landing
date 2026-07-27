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
