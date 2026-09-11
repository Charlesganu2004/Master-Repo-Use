---
name: master-refactor-ui
description: Fix an interface that already exists, in the order that makes each fix visible. Use when a page looks wrong and nobody can say why, when spacing and type are inconsistent, when a design reads as a default rather than a decision, or before adding a component to a surface that cannot hold it. Grayscale first, colour last.
---

# Refactor UI

The code refactor rule has a direct equivalent here: change how the surface
looks, not what it does. A button that moved is a redesign of the layout. A
button that now submits a different form is a bug wearing a redesign.

The other half is the order. Most interfaces that look wrong are not wrong in
their colour, they are wrong in their spacing and their hierarchy, and colour
was added on top of that and is now hiding it. So the fixes go in an order
where each one is visible before the next one lands.

The approach draws on jaywilburn/refactoring-ui-skill (MIT), itself based on the
Refactoring UI book; this is our own condensed statement of it.
`repo-lists/skill-upstreams.json` records the version checked against.

## Grayscale first

Strip the colour and look at it. Not metaphorically: set every colour to a gray
of the same lightness and reload.

What survives that is real hierarchy. What disappears was being carried by a
hue, which fails for the reader who is colour-blind, the one on a bad monitor,
and the one who printed it. If the primary action is indistinguishable from the
secondary one in gray, the fix is size, weight or position, not a stronger
blue.

Fix the layout, spacing and type in gray until it reads correctly. Only then
put the colour back.

## The audit, in order

1. **Spacing.** Pick one scale and use only it: 4, 8, 12, 16, 24, 32, 48, 64.
   Every arbitrary 13px and 27px is replaced by the nearest step. Inconsistent
   spacing is the single most common reason a page reads as unfinished, and it
   is the cheapest thing on this list to fix.
2. **Hierarchy.** Size, weight and colour, in that order of strength. If
   everything is bold, nothing is. Emphasis is usually better achieved by
   making the surrounding text lighter than by making the target heavier.
3. **Type.** One family, or one plus a mono for numbers and code. A modular
   scale rather than arbitrary sizes. Body text capped near 65 characters a
   line. Negative letter-spacing on large display text, never on body.
4. **Colour, last.** One accent, held across the whole surface. Backgrounds off
   the pure ends: not `#000000`, not `#ffffff`. Greys tinted from one family,
   warm or cool, not both on one page.
5. **Depth.** Shadows tinted toward the background hue rather than black at low
   opacity, and one consistent light direction. A shadow exists to say an
   element is above another one; if nothing is above anything, remove it.
6. **States.** Hover, active, focus, loading, empty, error. A surface with only
   its success state is not finished, and the empty state is the one a new user
   sees first.
7. **Accessibility as a gate, not a polish step.** Contrast at least 4.5:1 for
   body text and 3:1 for large text, a visible focus ring on everything
   reachable by keyboard, and `prefers-reduced-motion` honoured. These are
   pass or fail, not opinions, so check them with a measurement.

## Defaults to reach past

These are the shapes a model produces when it has not made a decision, which is
exactly why they read as machine-made:

- Purple or blue-violet gradients as the accent.
- A centred hero over a dark mesh background.
- Three equal cards in a row as the feature section.
- Glassmorphism applied to every container rather than to the one that floats.
- Inter at 400 and 700 only, on slate-900.
- A pill badge saying "New" next to everything.
- Lorem ipsum, "Acme Corp", "John Doe", and round fake numbers like 99.99%.

Reaching past a default means naming the family you chose instead and why it
fits the audience. "Editorial, because the page is mostly long-form text and
the client is a publisher" is a decision. "Modern and clean" is not.

## Change one thing, then look

Same reason as the code refactor. Swap the font and reload before touching the
palette. Fix the spacing scale and reload before restyling the cards. Six
simultaneous changes produce a surface that is different and nobody can say
which change was the improvement, so the next round has nothing to build on.

Highest impact first, which is usually: type family, then spacing scale, then
interactive states, then layout, then components, then the palette.

## Verify what is painted, not what exists

Counting elements in the DOM cannot tell a working page from one hidden behind
an opaque fixed layer. Both have the same node count. Load the surface in a real
browser, take the screenshot, and hit-test the specific coordinates of the
controls that are supposed to be clickable.

That failure mode is not hypothetical in this repository: a collapsed scene once
painted over the whole atlas, every element was present, every count passed, and
nothing on the page could be clicked.

Related: `master-design-taste` for choosing the aesthetic before there is
anything to audit, `master-refactor` for the same discipline applied to code,
and `verify-before-complete` for why the screenshot is the evidence and the
element count is not.
