---
name: master-repo-auto
description: Master Repo working rules - token discipline, compression safety, no-pruning policy, and multi-command handling. Load when compressing files, deciding what to load into context, orienting in an unfamiliar repository, or when asked how auto mode behaves.
---

# Master Repo auto mode

These rules were in every client's global instruction file, costing about 616
tokens per session per client. They live here instead: the listing carries only
the name and description above until something actually needs the detail.

## Token discipline

- Route shell commands through `rtk <command>` when rtk is installed. 60-90
  percent reduction on common dev commands at zero model cost.
- Before reading an unfamiliar repository, build a structural skeleton first
  (`rtt`) and retrieve only the files it points at. No speculative scanning.
- Compress repeatedly-loaded natural-language files with the local caveman
  skills. They are deterministic and cost no API calls. Do not reach for an
  API-billed compressor to do work a local skill already does.
- Never paste a whole catalog file into a prompt. Search by lane or name and
  load only matching entries.

## What compression may never touch

Code blocks, backtick spans, URLs, file paths, shell commands, environment
variables, headings, version numbers, dates and exact error strings stay
byte-for-byte.

A pass saving under 15 percent is a failed pass. Restore the original and say
the file was already dense rather than reporting moved words as a win.

## Never prune what the user chose to keep

- Do not remove, disable, uninstall or stop loading a skill, tool, MCP server,
  plugin or catalog entry on your own initiative. These were chosen deliberately.
- Keep them unless Charles explicitly asks for removal in his own words. Looking
  unused, stale, redundant or noisy is not permission to drop something.
- Context pressure is never a reason to silently unload a tool. Say the context
  is tight and ask what to drop.
- Cataloged entries are removed only through an owner-approved pull request,
  never by an automated job acting alone.
- Compaction summarises conversation; it does not retire capabilities. Skills and
  tools available before a compaction are still available after it.

This rule is also enforced deterministically by the no-prune hook, which blocks
deletions of skill, plugin, MCP and catalog paths before they run. The hook does
not depend on a model reading this file.

## Run every command in the prompt

- A single message may carry more than one slash command or skill invocation.
  Execute all of them, in the order written, and report each result.
- Do not silently act on the first and drop the rest. If one cannot run, say
  which and why, then continue with the others.

## Scope

Auto mode changes how work is done, never what is permitted. Vetting, licence,
security and approval gates apply in full. Nothing third-party is installed or
executed on the strength of these rules alone.
