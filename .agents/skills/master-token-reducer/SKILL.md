---
name: master-token-reducer
description: Build compact retrieval packets for large repositories, documents, transcripts, catalogs, and logs before loading details into model context.
---

# Master Token Reducer

Start with a narrow question and targeted paths. When the local Token Reducer is
installed, use its hash backend with a small top-k and word budget, then open
only the cited chunks. If it cannot parse the input, fall back to focused text
searches and bounded sections instead of dumping the source.

Measure the reduction. Preserve code, commands, URLs, file paths, versions,
dates, headings and exact errors byte for byte. Never send capability definitions,
catalog entries or protected `NO-COMPRESS` content through a compression pass.
