---
tokens:
  color:
    primary: { paper: "#121314", ink: "#ececec" }
    secondary: { paper: "#393c40", ink: "#c6c8cc" }
    tertiary: { paper: "#5f6368", ink: "#9a9da3" }
    neutral:
      bg: { paper: "#e9eaec", ink: "#1a1b1d" }
      bg-2: { paper: "#dfe1e4", ink: "#222326" }
      bg-3: { paper: "#d3d5d9", ink: "#2b2d31" }
    signal: { paper: "#9a6f22", ink: "#e0b96a" }
    signal-text: { paper: "#7a5a1c", ink: "#e0b96a" }
    line: { paper: "rgba(18,19,20,.26)", ink: "rgba(236,236,236,.26)" }
    line-soft: { paper: "rgba(18,19,20,.12)", ink: "rgba(236,236,236,.12)" }
    mark: { plate: "#0b0f1a", gold: "#d4a858" }
  type:
    sans: "Bahnschrift, -apple-system, 'SF Pro Text', 'Segoe UI', 'Noto Sans', 'DejaVu Sans', system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif"
    mono: "ui-monospace, 'Cascadia Mono', 'SF Mono', Menlo, Consolas, monospace"
    display: { size: "clamp(2.5rem, 5.6vw, 4.25rem)", weight: 600, line: 1.08, tracking: "-0.02em" }
    headline: { size: "clamp(1.6rem, 2.6vw, 2.1rem)", weight: 600, line: 1.2, tracking: "-0.015em" }
    title: { size: "1.2rem", weight: 600, line: 1.3 }
    lede: { size: "clamp(1.1rem, 1.6vw, 1.3rem)", weight: 400, line: 1.5 }
    body: { size: "17px", weight: 400, line: 1.55 }
    table: { size: "16px", weight: 400, line: 1.45 }
    label: { size: "14px", weight: 400 }
    control: { size: "15px", weight: 600 }
    code: { inline: "0.92em", note: "0.95rem", output: "0.9rem", line: 1.5 }
  rounded:
    pill: "999px"
    block: "14px"
    focus: "2px"
    mark: "12px (on a 64 grid)"
  spacing:
    scale: [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40, 48]
    section: "clamp(56px, 8vw, 104px)"
    gutter: "clamp(20px, 5vw, 72px)"
    measure: "62ch"
    max: "1120px"
  motion:
    ease: "cubic-bezier(.16, 1, .3, 1)"
    settle: "700ms"
    hover: "200ms"
---

# DESIGN record · Mem-Forever landing page

Written after the build from what was built, by scanning the custom properties and rules of `docs/index.html`. Paper and ink are the two schemes; every value above comes from the page's CSS or from the iLang site it inherits. Nothing here is a plan; it is an inventory.

## Creative North Star (authored)

A note left on the desk for the next session. The page is a child of the iLang world: paper and ink, hairlines, one gold pointer, and the hand-off note as the only object. It stands on type and space; nothing glows, nothing floats, and the one motion is the note settling where the pointer says "here".

## Colors

Primary is the reading ink on each scheme. Secondary carries running text under headings and inside rows; tertiary carries labels, captions and the footer. Neutral `bg` is the page, `bg-2` the two framed blocks (the note and the review output), `bg-3` is reserved and unused on this page. The signal is the one accent: the second line of the h1, the "here" tick and label, the REJECT verdicts, the focus ring, the selection and the caret. On paper the signal darkens to `#9a6f22` for strokes and `#7a5a1c` for text so that it keeps 5:1 on the page and 4.9:1 on `bg-2`. The two line tokens are the only borders: `line` for the ruler track, ticks, the note and the pills; `line-soft` for every other hairline. The bracket mark keeps its own plate and gold because it is the brand's mark, not a page color.

## Typography

One sans family through the system stack the brand uses, one mono stack for notation. Roles: display (h1), headline (h2), title (h3 and the judge heading), lede, body, table, label (captions, ruler labels, nav at small widths, footer), control (pills, nav), code in three sizes (inline 0.92em, the note 0.95rem, the output block 0.9rem). Headings are weight 600, everything else 400. Headings balance, paragraphs wrap pretty. Numbers in the ruler and the table are tabular.

## Rounded

Pills are the only 999px shape, used for the two actions and the skip link. The two framed blocks use 14px. The focus ring carries a 2px radius. Nothing else is rounded.

## Spacing

The scale above is what the page uses, in px; sections open with the `section` clamp, the gutter is the `gutter` clamp, reading columns stop at 62ch, the frame at 1120px. Rhythm alternates tight inside a group (8 to 14) and loose between groups (26 to 48); space above a heading is always larger than below it.

## Components

- **Pill** (`.pill`, `.pill.solid`): backgroundColor (transparent or primary), textColor (primary or bg), typography control, rounded pill, padding 10px 20px, height 44px minimum; hover darkens the border or the fill in 200ms; focus ring is the signal.
- **Note** (`.note`): backgroundColor bg-2, border line, rounded block, padding 16px 22px, width 720px maximum, typography code; keys in signal-text; settles in 700ms from 60 percent opacity and 14px below, static under reduced motion.
- **Ruler** (`.ruler`): a 1px track in `line`, 1px ticks at both ends, a 2px signal tick at the middle, three labels in label type under their ticks, the middle one in signal-text.
- **Output block** (`.out`): backgroundColor bg-2, border line-soft, rounded block, padding 18px 22px, width 820px maximum, typography code; verdict words in signal-text.
- **Rows** (`.rows`): hairline list, two columns from 721px (title 1fr, text 2fr), one column below; no card, no icon.
- **Steps** (`.steps`): ordered list in secondary with the lead phrase in primary.
- **Table**: row headers at 38 percent above 720px, stacked rows with hairlines below.
- **Bar** (`.bar`, `.top`): full-bleed hairline under a 60px row holding the mark and three links.

## States

Hover on links and pills, visible focus on every focusable element, themed selection, themed caret, themed scrollbar, reduced-motion alternative for the one animation. No loading, error or empty states: the page has no inputs and no data fetches.

## Where it lives

`docs/index.html` is the page, served by GitHub Pages from `docs/`. `docs/assets/banner-light.svg` and `banner-dark.svg` are the README banners in the same tokens; `docs/assets/social-preview.png` is the 1280 by 640 card. `docs/PRODUCT.md` is the product record this page was built from.
