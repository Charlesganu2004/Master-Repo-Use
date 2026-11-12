---
name: master-architect
description: Decide the shape of a system before writing it: the boundaries, where state lives, what each piece owns, and which decisions are expensive to reverse. Use before a new component, a change that crosses more than one module, an integration, a data model, or any work where the second version would be a rewrite rather than an edit. Distinct from planning, which sequences work that has already been shaped.
---

# Architect

Planning answers "in what order". Architecture answers "in what shape". They are
different questions and the second one is the one that gets skipped, because a
plan feels like a decision and reads like progress.

The test for whether this skill applies: if you got the shape wrong, would the
fix be an edit or a rewrite? An edit means proceed. A rewrite means stop and
decide the shape first.

## Name the boundaries before the pieces

A boundary is a line across which two sides can change without telling each
other. Every one you draw is a promise you have to keep, so draw few and draw
them where the change actually happens.

For each piece, write one line answering three things:

    owns          the state or decision nothing else may touch
    depends on    what it needs, and in which direction
    changes when  the reason it would ever be edited

If two pieces have the same "changes when", they are one piece wearing two
names. If a piece has three, it is three pieces. That question separates
components far better than what they are called or which folder they sit in.

## Direction of dependency is the design

Dependencies point one way. When they point both ways you have one component
with a line drawn through it, and the line will not hold: every change will
cross it, and the two halves will be edited together forever.

When a cycle appears, the fix is almost never an interface. It is that a third
thing exists which both sides depend on and neither owns yet. Find it and name
it.

## Say where state lives, exactly once

Most defects that survive review are two copies of the same fact disagreeing.
Every piece of state gets one owner and one home. Anything else holding it holds
a cache, which is spelled out as a cache with a stated staleness, not left as a
second source that looks authoritative.

This repository has paid for that lesson repeatedly: a page that restated the
pipeline rules said ten while the hook injected eleven, a store that counted 49
recipes while the payload shipped 50, and a note typed as "1126 components" while
the catalog held 1291. In each case the fix was the same: one source, read by
everyone who needs it.

## Sort decisions by what they cost to undo

    cheap to reverse    make it now, do not hold a meeting, do not write a doc
    costly to reverse   write down the alternatives and why this one, then decide
    one way only        data formats others will store, public interfaces, wire
                        protocols, anything a user or another system persists

Only the third kind deserves real deliberation. Treating a cheap decision as
expensive is how a change takes a week; treating an expensive one as cheap is how
a format survives for years because migrating it is now unaffordable.

## Write the decision down where the code is

A decision with no record gets re-litigated by the next person, or quietly
reversed by someone who did not know it was a decision. Two or three sentences at
the top of the file it governs: what was chosen, what else was considered, and
what would make this wrong. That last sentence is the valuable one, because it
tells a future reader when to revisit rather than leaving them to guess whether
the constraint still holds.

## The shapes worth reaching for, and when they are wrong

    one module            until a second reason to change appears. Splitting
                          before that produces two files edited together.
    a pipeline            stages that only pass data forward. Wrong the moment a
                          later stage needs to talk back to an earlier one.
    an event stream       when producers must not know their consumers. Costs you
                          the ability to answer "what happens next" by reading.
    a shared store        when several pieces need the same fact. Becomes the
                          coupling it was meant to remove once everyone writes.
    a plugin registry     when the set of implementations is open. Overkill when
                          you have two and will always have two.

Reaching for the last three before you need them is the common failure. Each one
buys flexibility with a permanent cost in traceability, and the flexibility is
frequently never used.

## What this does not license

It does not license a redesign of code that works because a nicer shape exists.
Structure that is ugly and stable is cheaper than structure that is elegant and
new. Change shape when a specific change is hard, and name the change that is
hard.

It does not license abstraction ahead of evidence. Two call sites is a
coincidence; three is a pattern. Extracting on the first coincidence produces an
interface fitted to one case that both later cases have to fight.

Related: `master-plan` sequences the work once its shape is decided,
`master-refactor` changes structure without changing behaviour, and
`master-review` checks the result against the shape that was chosen.
