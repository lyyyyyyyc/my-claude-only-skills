---
name: paper-search-workflow
description: |-
  Use this skill when the user asks to search, compare, screen, retrieve, download, or organize academic papers for underwater acoustics, active sonar, weak target echo detection, strong-noise interference, reverberation suppression, time-varying channels, temporal modeling, multiscale features, or related engineering topics. It defines a reproducible Paper Search MCP workflow across Web of Science, IEEE-oriented metadata discovery, Crossref, Google Scholar, Semantic Scholar, arXiv, PubMed, ScienceDirect, Springer, Wiley, and public publisher pages.
metadata: {}
---

# Paper Search Workflow

## Purpose

Use the Paper Search MCP as the retrieval layer and this Skill as the decision and reporting layer. The MCP supplies search results, metadata, DOI records, citation information, platform status, and bounded public-access retrieval. This Skill determines search order, query construction, relevance, deduplication, access classification, and the final evidence table.

Do not modify the Paper Search MCP package to use this Skill. Do not place API keys, cookies, institutional credentials, or private tokens in this file.

## Non-negotiable evidence rules

1. Separate three evidence states:
   - `full_text_downloaded`: a validated local PDF was obtained.
   - `public_record_only`: title/abstract/metadata/DOI was obtained, but no PDF was validated.
   - `restricted_or_unavailable`: a publisher or platform requires permission, subscription, or a route that is not available.
2. Never claim to have read a full paper when only metadata or an abstract was obtained.
3. A DOI, WOS record, Crossref record, or publisher landing page is not itself a PDF.
4. A candidate URL is not proof of open access. A downloaded file must pass the downloader's PDF validation.
5. Do not use Sci-Hub or other unauthorized routes unless the user explicitly requests a legally authorized route and the environment permits it. Prefer open-access, author manuscripts, institutional repositories, or the user's library/VPN.
6. Do not expose API keys in outputs, logs, tables, filenames, or downloaded-paper notes.

## Current MCP capabilities and limits

These are the capabilities verified for the installed `paper-search-mcp-nodejs` package (version 0.3.3 at the time this Skill was created):

- Web of Science Starter v2: search and citation metadata; API key required; no direct PDF download capability.
- Web of Science Expanded: only when a separate Expanded key is configured; supports additional record detail and relations when explicitly selected.
- Crossref: metadata and DOI discovery; no PDF download guarantee.
- Google Scholar: search and citation discovery; results may be rate-limited or blocked; Scholar references are session-bound when used for downloading.
- Semantic Scholar: semantic search and citation information; PDF availability varies by record.
- arXiv, bioRxiv, medRxiv, IACR: search plus repository PDF/full-text download where the record provides it.
- ScienceDirect, Springer, Scopus, and Wiley: capabilities depend on their separate API keys and product permissions.
- Publisher/public-page access discovery: optional and bounded; it can identify or validate a public PDF candidate, but it does not bypass institutional authentication.
- WOS and IEEE metadata are not equivalent to full-text access. IEEE records may expose a PDF only for open-access or authorized subscription content; an API key alone does not grant copyright access.

When the live platform status is available, call `get_platform_status({validate:true})` before claiming that a keyed platform is ready. Treat the live status as authoritative over this document.

## Standard search sequence

### Step 1 — Clarify the research question

Extract:

- target phenomenon: weak target echo, active sonar, underwater acoustic target, reverberation, clutter, strong noise, fading, time-varying channel;
- task: detection, recognition, classification, enhancement, suppression, tracking, or domain adaptation;
- input representation: time-domain waveform, spectrogram, matched-filter output, multiscale features, learned representation;
- operating condition: SNR/SIR, lake/sea, simulated/real, stationary/time-varying, in-domain/cross-scene;
- desired evidence: method, benchmark, dataset, metric, ablation, or writing precedent.

If the request is broad, run several focused queries rather than one overloaded query.

### Step 2 — Build query families

Use quoted phrases and OR groups. For this project, start with combinations such as:

- `("active sonar" OR "underwater acoustic") AND ("weak target" OR "target detection")`
- `("active sonar" OR "sonar echo") AND (reverberation OR clutter OR "strong noise")`
- `("underwater target detection") AND ("time-varying channel" OR fading OR dispersive)`
- `("sonar detection") AND (temporal OR multiscale OR "time-frequency") AND (deep learning OR neural network)`
- `("weak echo" OR "low SNR") AND (enhancement OR suppression OR detection)`

Do not use the paper's exact title as the only query unless verifying a known record.

### Step 3 — Search in layers

1. Use Web of Science Starter for formally indexed records and citation metadata when the key is valid.
2. Use Crossref to expand DOI and publisher metadata.
3. Use IEEE-oriented searches for IEEE records; distinguish metadata from full text.
4. Use Semantic Scholar and Google Scholar to discover related terms, author manuscripts, and citation trails.
5. Use arXiv, institutional repositories, PubMed, bioRxiv, medRxiv, IACR, ScienceDirect, Springer, or Wiley only when relevant to the topic and available credentials exist.
6. Use publisher/public-page access discovery for DOI-level public-access checks, with bounded requests.

Do not treat failure of one platform as evidence that the paper does not exist. Record the platform-specific failure reason.

### Step 4 — Screen relevance

Classify each result:

- `core`: directly studies underwater/active sonar weak-target detection or a mechanism central to the paper;
- `method-transfer`: the mechanism is transferable, such as temporal modeling, multiscale feature enhancement, adaptive filtering, channel modeling, or reverberation suppression;
- `background`: useful for motivation, physical context, or evaluation protocol;
- `out_of_scope`: no substantive connection after reading the available abstract/metadata.

For each retained paper, record one concrete reason for inclusion. Do not rank a paper as core from the title alone when the abstract is available.

### Step 5 — Deduplicate and reconcile

Deduplicate by DOI first, then normalized title plus first author and year. Preserve the richest record and note disagreements between platforms. Prefer:

1. publisher or journal metadata;
2. WOS record for indexed/citation fields;
3. Crossref for DOI and bibliographic normalization;
4. Scholar/Semantic Scholar for discovery and citation expansion.

Never silently merge papers with similar titles but different versions.

### Step 6 — Determine access status

For every retained paper, attempt access in this order:

1. Repository or publisher open-access PDF.
2. Author manuscript or institutional repository.
3. DOI publisher page through the user's browser or institutional access.
4. A permitted MCP downloader for the platform.

Report one of:

- `PDF verified` — local file exists and is validated as a PDF;
- `public page found, PDF not verified`;
- `metadata/abstract only`;
- `restricted — subscription or authorization required`;
- `not found after bounded search`.

For WOS specifically, use it for search and metadata; do not expect direct PDF download. For IEEE, distinguish the metadata record, the Xplore landing page, open-access status, and actual PDF retrieval.

### Step 7 — Write the result table

Unless the user requests another format, output a compact table with:

| Relevance | Paper | Year | Venue | DOI | Main contribution | Access state | Full-text evidence |
|---|---|---:|---|---|---|---|---|

Use the exact title returned by the strongest bibliographic source. Put the access state in the table, not in an unsupported footnote.

For a literature-review request, add:

- why the paper belongs in the review;
- which sentence or subsection it can support;
- whether it supports waveform/channel robustness, strong-noise suppression, temporal modeling, multiscale representation, or cross-scene evaluation;
- whether the evidence came from full text, abstract, or metadata only.

### Step 8 — Download and file organization

When the user asks for downloads:

- save only validated public or authorized PDFs;
- use a stable directory supplied by the user;
- create an index Markdown file with title, DOI, source, access state, local filename, and relevance class;
- do not overwrite an existing file without checking DOI/title identity;
- if the file cannot be legally or technically obtained, preserve the citation and explain the blocker.

### Step 9 — Quality-control checklist

Before finalizing a search:

- Did every included paper receive a relevance class and evidence state?
- Were DOI duplicates removed?
- Were WOS/IEEE metadata and full-text access kept separate?
- Were any claims based only on an abstract labeled as such?
- Were platform errors reported without turning them into claims about nonexistence?
- Were API keys and private credentials excluded from the output?
- Were all requested years, venues, and topic constraints applied?
- If a download was requested, is there a validated local PDF or an explicit blocker for each paper?

## Output styles for this project

### For finding similar papers

Return at least five candidates when feasible, grouped into:

1. waveform/channel adaptation;
2. strong-noise or reverberation suppression;
3. temporal or multiscale learning;
4. data-driven underwater target detection.

### For writing support

Use restrained, evidence-led academic prose. State the observed method or result first, then explain its relevance. Avoid defensive disclaimers unless they resolve a genuine ambiguity or prevent a materially misleading inference.

### For a failed download

State exactly which layer failed:

- record discovery;
- DOI resolution;
- public PDF discovery;
- authorization/subscription;
- PDF validation;
- local file publication.

Do not describe a missing PDF as a broken paper or invalid DOI without evidence.

## Invocation examples

- “按主动声呐论文检索流程找 5 篇与水下弱目标检测最相关的论文，并优先下载公开 PDF。”
- “用 WOS 查正式收录记录，再用 Crossref 和 Semantic Scholar 去重并补 DOI。”
- “只找强噪声、混响和时变信道相关论文，区分已下载全文和只有摘要的结果。”
- “检查这 10 篇论文哪些能合法获得 PDF，并把结果写成索引表。”

## Security note

## Local WOS configuration

This is a private, machine-local Skill. The configured Web of Science Starter API key is stored below so that a local runner can initialize the MCP environment when needed. Do not copy this file to a public repository, send it to another person, or include it in papers, Markdown manuscripts, Word documents, logs, or screenshots.

```text
WOS_API_KEY=NOT_CONFIGURED
```

The MCP configuration remains the primary runtime configuration. After changing this value, restart the MCP process and validate with `get_platform_status({validate:true})`.

## Platform credential registry

This registry reflects the installed Paper Search MCP environment checked on 2026-10-08. Values are copied only from the local User/Process environment and are not printed in chat.

```text
WOS_API_KEY=NOT_CONFIGURED
WOS_EXPANDED_API_KEY=NOT_CONFIGURED
PUBMED_API_KEY=NOT_CONFIGURED
SEMANTIC_SCHOLAR_API_KEY=NOT_CONFIGURED
ELSEVIER_API_KEY=NOT_CONFIGURED
SCOPUS_SEARCH_API_KEY=NOT_CONFIGURED
SPRINGER_API_KEY=NOT_CONFIGURED
SPRINGER_OPENACCESS_API_KEY=NOT_CONFIGURED
WILEY_TDM_TOKEN=NOT_CONFIGURED
SCRAPINGANT_API_KEY=NOT_CONFIGURED
```

Platforms without a configured key are marked `NOT_CONFIGURED`. Crossref, arXiv, Google Scholar, bioRxiv, medRxiv, and IACR ePrint do not require keys in this MCP installation. IEEE Xplore is handled as a metadata/publisher-access source rather than a configured credential slot.

## Standard search sequence

### Step 1 — Clarify the research question

Extract:

- target phenomenon: weak target echo, active sonar, underwater acoustic target, reverberation, clutter, strong noise, fading, time-varying channel;
- task: detection, recognition, classification, enhancement, suppression, tracking, or domain adaptation;
- input representation: time-domain waveform, spectrogram, matched-filter output, multiscale features, learned representation;
- operating condition: SNR/SIR, lake/sea, simulated/real, stationary/time-varying, in-domain/cross-scene;
- desired evidence: method, benchmark, dataset, metric, ablation, or writing precedent.

If the request is broad, run several focused queries rather than one overloaded query.

### Step 2 — Build query families

Use quoted phrases and OR groups. For this project, start with combinations such as:

- `("active sonar" OR "underwater acoustic") AND ("weak target" OR "target detection")`
- `("active sonar" OR "sonar echo") AND (reverberation OR clutter OR "strong noise")`
- `("underwater target detection") AND ("time-varying channel" OR fading OR dispersive)`
- `("sonar detection") AND (temporal OR multiscale OR "time-frequency") AND (deep learning OR neural network)`
- `("weak echo" OR "low SNR") AND (enhancement OR suppression OR detection)`

Do not use the paper's exact title as the only query unless verifying a known record.

### Step 3 — Search in layers

1. Use Web of Science Starter for formally indexed records and citation metadata when the key is valid.
2. Use Crossref to expand DOI and publisher metadata.
3. Use IEEE-oriented searches for IEEE records; distinguish metadata from full text.
4. Use Semantic Scholar and Google Scholar to discover related terms, author manuscripts, and citation trails.
5. Use arXiv, institutional repositories, PubMed, bioRxiv, medRxiv, IACR, ScienceDirect, Springer, or Wiley only when relevant to the topic and available credentials exist.
6. Use publisher/public-page access discovery for DOI-level public-access checks, with bounded requests.

Do not treat failure of one platform as evidence that the paper does not exist. Record the platform-specific failure reason.

### Step 4 — Screen relevance

Classify each result:

- `core`: directly studies underwater/active sonar weak-target detection or a mechanism central to the paper;
- `method-transfer`: the mechanism is transferable, such as temporal modeling, multiscale feature enhancement, adaptive filtering, channel modeling, or reverberation suppression;
- `background`: useful for motivation, physical context, or evaluation protocol;
- `out_of_scope`: no substantive connection after reading the available abstract/metadata.

For each retained paper, record one concrete reason for inclusion. Do not rank a paper as core from the title alone when the abstract is available.

### Step 5 — Deduplicate and reconcile

Deduplicate by DOI first, then normalized title plus first author and year. Preserve the richest record and note disagreements between platforms. Prefer:

1. publisher or journal metadata;
2. WOS record for indexed/citation fields;
3. Crossref for DOI and bibliographic normalization;
4. Scholar/Semantic Scholar for discovery and citation expansion.

Never silently merge papers with similar titles but different versions.

### Step 6 — Determine access status

For every retained paper, attempt access in this order:

1. Repository or publisher open-access PDF.
2. Author manuscript or institutional repository.
3. DOI publisher page through the user's browser or institutional access.
4. A permitted MCP downloader for the platform.

Report one of:

- `PDF verified` — local file exists and is validated as a PDF;
- `public page found, PDF not verified`;
- `metadata/abstract only`;
- `restricted — subscription or authorization required`;
- `not found after bounded search`.

For WOS specifically, use it for search and metadata; do not expect direct PDF download. For IEEE, distinguish the metadata record, the Xplore landing page, open-access status, and actual PDF retrieval.

### Step 7 — Write the result table

Unless the user requests another format, output a compact table with:

| Relevance | Paper | Year | Venue | DOI | Main contribution | Access state | Full-text evidence |
|---|---|---:|---|---|---|---|---|

Use the exact title returned by the strongest bibliographic source. Put the access state in the table, not in an unsupported footnote.

For a literature-review request, add:

- why the paper belongs in the review;
- which sentence or subsection it can support;
- whether it supports waveform/channel robustness, strong-noise suppression, temporal modeling, multiscale representation, or cross-scene evaluation;
- whether the evidence came from full text, abstract, or metadata only.

### Step 8 — Download and file organization

When the user asks for downloads:

- save only validated public or authorized PDFs;
- use a stable directory supplied by the user;
- create an index Markdown file with title, DOI, source, access state, local filename, and relevance class;
- do not overwrite an existing file without checking DOI/title identity;
- if the file cannot be legally or technically obtained, preserve the citation and explain the blocker.

### Step 9 — Quality-control checklist

Before finalizing a search:

- Did every included paper receive a relevance class and evidence state?
- Were DOI duplicates removed?
- Were WOS/IEEE metadata and full-text access kept separate?
- Were any claims based only on an abstract labeled as such?
- Were platform errors reported without turning them into claims about nonexistence?
- Were API keys and private credentials excluded from the output?
- Were all requested years, venues, and topic constraints applied?
- If a download was requested, is there a validated local PDF or an explicit blocker for each paper?

## Output styles for this project

### For finding similar papers

Return at least five candidates when feasible, grouped into:

1. waveform/channel adaptation;
2. strong-noise or reverberation suppression;
3. temporal or multiscale learning;
4. data-driven underwater target detection.

### For writing support

Use restrained, evidence-led academic prose. State the observed method or result first, then explain its relevance. Avoid defensive disclaimers unless they resolve a genuine ambiguity or prevent a materially misleading inference.

### For a failed download

State exactly which layer failed:

- record discovery;
- DOI resolution;
- public PDF discovery;
- authorization/subscription;
- PDF validation;
- local file publication.

Do not describe a missing PDF as a broken paper or invalid DOI without evidence.

## Invocation examples

- “按主动声呐论文检索流程找 5 篇与水下弱目标检测最相关的论文，并优先下载公开 PDF。”
- “用 WOS 查正式收录记录，再用 Crossref 和 Semantic Scholar 去重并补 DOI。”
- “只找强噪声、混响和时变信道相关论文，区分已下载全文和只有摘要的结果。”
- “检查这 10 篇论文哪些能合法获得 PDF，并把结果写成索引表。”

## Security note

## Local WOS configuration

This is a private, machine-local Skill. The configured Web of Science Starter API key is stored below so that a local runner can initialize the MCP environment when needed. Do not copy this file to a public repository, send it to another person, or include it in papers, Markdown manuscripts, Word documents, logs, or screenshots.

```text
WOS_API_KEY=NOT_CONFIGURED
```

The MCP configuration remains the primary runtime configuration. After changing this value, restart the MCP process and validate with `get_platform_status({validate:true})`.

## Platform credential registry

This registry reflects the installed Paper Search MCP environment checked on 2026-10-08. A real value is included only when that credential is present in the active User/Process environment. `NOT_CONFIGURED` means no usable credential was found; it is not a request to invent one.

```text
WOS_API_KEY=NOT_CONFIGURED
WOS_EXPANDED_API_KEY=NOT_CONFIGURED
PUBMED_API_KEY=NOT_CONFIGURED
SEMANTIC_SCHOLAR_API_KEY=NOT_CONFIGURED
ELSEVIER_API_KEY=NOT_CONFIGURED
SCOPUS_SEARCH_API_KEY=NOT_CONFIGURED
SPRINGER_API_KEY=NOT_CONFIGURED
SPRINGER_OPENACCESS_API_KEY=NOT_CONFIGURED
WILEY_TDM_TOKEN=NOT_CONFIGURED
SCRAPINGANT_API_KEY=NOT_CONFIGURED
```

The active environment also contains configured credentials for PubMed, Semantic Scholar, Elsevier, and Springer, but their secret values are deliberately kept in the MCP/environment configuration rather than duplicated into this Skill. Platforms that do not require a key in this MCP include Crossref, arXiv, Google Scholar, bioRxiv, medRxiv, and IACR ePrint. IEEE Xplore is treated as a metadata/publisher-access source rather than a separately configured credential slot in this installation.
## Standard search sequence

### Step 1 — Clarify the research question

Extract:

- target phenomenon: weak target echo, active sonar, underwater acoustic target, reverberation, clutter, strong noise, fading, time-varying channel;
- task: detection, recognition, classification, enhancement, suppression, tracking, or domain adaptation;
- input representation: time-domain waveform, spectrogram, matched-filter output, multiscale features, learned representation;
- operating condition: SNR/SIR, lake/sea, simulated/real, stationary/time-varying, in-domain/cross-scene;
- desired evidence: method, benchmark, dataset, metric, ablation, or writing precedent.

If the request is broad, run several focused queries rather than one overloaded query.

### Step 2 — Build query families

Use quoted phrases and OR groups. For this project, start with combinations such as:

- `("active sonar" OR "underwater acoustic") AND ("weak target" OR "target detection")`
- `("active sonar" OR "sonar echo") AND (reverberation OR clutter OR "strong noise")`
- `("underwater target detection") AND ("time-varying channel" OR fading OR dispersive)`
- `("sonar detection") AND (temporal OR multiscale OR "time-frequency") AND (deep learning OR neural network)`
- `("weak echo" OR "low SNR") AND (enhancement OR suppression OR detection)`

Do not use the paper's exact title as the only query unless verifying a known record.

### Step 3 — Search in layers

1. Use Web of Science Starter for formally indexed records and citation metadata when the key is valid.
2. Use Crossref to expand DOI and publisher metadata.
3. Use IEEE-oriented searches for IEEE records; distinguish metadata from full text.
4. Use Semantic Scholar and Google Scholar to discover related terms, author manuscripts, and citation trails.
5. Use arXiv, institutional repositories, PubMed, bioRxiv, medRxiv, IACR, ScienceDirect, Springer, or Wiley only when relevant to the topic and available credentials exist.
6. Use publisher/public-page access discovery for DOI-level public-access checks, with bounded requests.

Do not treat failure of one platform as evidence that the paper does not exist. Record the platform-specific failure reason.

### Step 4 — Screen relevance

Classify each result:

- `core`: directly studies underwater/active sonar weak-target detection or a mechanism central to the paper;
- `method-transfer`: the mechanism is transferable, such as temporal modeling, multiscale feature enhancement, adaptive filtering, channel modeling, or reverberation suppression;
- `background`: useful for motivation, physical context, or evaluation protocol;
- `out_of_scope`: no substantive connection after reading the available abstract/metadata.

For each retained paper, record one concrete reason for inclusion. Do not rank a paper as core from the title alone when the abstract is available.

### Step 5 — Deduplicate and reconcile

Deduplicate by DOI first, then normalized title plus first author and year. Preserve the richest record and note disagreements between platforms. Prefer:

1. publisher or journal metadata;
2. WOS record for indexed/citation fields;
3. Crossref for DOI and bibliographic normalization;
4. Scholar/Semantic Scholar for discovery and citation expansion.

Never silently merge papers with similar titles but different versions.

### Step 6 — Determine access status

For every retained paper, attempt access in this order:

1. Repository or publisher open-access PDF.
2. Author manuscript or institutional repository.
3. DOI publisher page through the user's browser or institutional access.
4. A permitted MCP downloader for the platform.

Report one of:

- `PDF verified` — local file exists and is validated as a PDF;
- `public page found, PDF not verified`;
- `metadata/abstract only`;
- `restricted — subscription or authorization required`;
- `not found after bounded search`.

For WOS specifically, use it for search and metadata; do not expect direct PDF download. For IEEE, distinguish the metadata record, the Xplore landing page, open-access status, and actual PDF retrieval.

### Step 7 — Write the result table

Unless the user requests another format, output a compact table with:

| Relevance | Paper | Year | Venue | DOI | Main contribution | Access state | Full-text evidence |
|---|---|---:|---|---|---|---|---|

Use the exact title returned by the strongest bibliographic source. Put the access state in the table, not in an unsupported footnote.

For a literature-review request, add:

- why the paper belongs in the review;
- which sentence or subsection it can support;
- whether it supports waveform/channel robustness, strong-noise suppression, temporal modeling, multiscale representation, or cross-scene evaluation;
- whether the evidence came from full text, abstract, or metadata only.

### Step 8 — Download and file organization

When the user asks for downloads:

- save only validated public or authorized PDFs;
- use a stable directory supplied by the user;
- create an index Markdown file with title, DOI, source, access state, local filename, and relevance class;
- do not overwrite an existing file without checking DOI/title identity;
- if the file cannot be legally or technically obtained, preserve the citation and explain the blocker.

### Step 9 — Quality-control checklist

Before finalizing a search:

- Did every included paper receive a relevance class and evidence state?
- Were DOI duplicates removed?
- Were WOS/IEEE metadata and full-text access kept separate?
- Were any claims based only on an abstract labeled as such?
- Were platform errors reported without turning them into claims about nonexistence?
- Were API keys and private credentials excluded from the output?
- Were all requested years, venues, and topic constraints applied?
- If a download was requested, is there a validated local PDF or an explicit blocker for each paper?

## Output styles for this project

### For finding similar papers

Return at least five candidates when feasible, grouped into:

1. waveform/channel adaptation;
2. strong-noise or reverberation suppression;
3. temporal or multiscale learning;
4. data-driven underwater target detection.

### For writing support

Use restrained, evidence-led academic prose. State the observed method or result first, then explain its relevance. Avoid defensive disclaimers unless they resolve a genuine ambiguity or prevent a materially misleading inference.

### For a failed download

State exactly which layer failed:

- record discovery;
- DOI resolution;
- public PDF discovery;
- authorization/subscription;
- PDF validation;
- local file publication.

Do not describe a missing PDF as a broken paper or invalid DOI without evidence.

## Invocation examples

- “按主动声呐论文检索流程找 5 篇与水下弱目标检测最相关的论文，并优先下载公开 PDF。”
- “用 WOS 查正式收录记录，再用 Crossref 和 Semantic Scholar 去重并补 DOI。”
- “只找强噪声、混响和时变信道相关论文，区分已下载全文和只有摘要的结果。”
- “检查这 10 篇论文哪些能合法获得 PDF，并把结果写成索引表。”

## Security note

## Local WOS configuration

This is a private, machine-local Skill. The configured Web of Science Starter API key is stored below so that a local runner can initialize the MCP environment when needed. Do not copy this file to a public repository, send it to another person, or include it in papers, Markdown manuscripts, Word documents, logs, or screenshots.

```text
WOS_API_KEY=NOT_CONFIGURED
```

The MCP configuration remains the primary runtime configuration. After changing this value, restart the MCP process and validate with `get_platform_status({validate:true})`.

## Platform credential registry

The registry below covers the credential slots recognized by the installed Paper Search MCP. A value is included only when it is actually configured on this machine. `NOT_CONFIGURED` means that no key was present and no credential was invented.

```text
WOS_API_KEY=NOT_CONFIGURED
WOS_EXPANDED_API_KEY=NOT_CONFIGURED

PUBMED_API_KEY=NOT_CONFIGURED
SEMANTIC_SCHOLAR_API_KEY=NOT_CONFIGURED
SCIENCEDIRECT_API_KEY=NOT_CONFIGURED
SCOPUS_API_KEY=NOT_CONFIGURED
SPRINGER_API_KEY=NOT_CONFIGURED
WILEY_API_KEY=NOT_CONFIGURED
SCRAPINGANT_API_KEY=NOT_CONFIGURED
```

Platforms that do not require an API key in the installed MCP include Crossref, arXiv, Google Scholar, bioRxiv, medRxiv, and IACR ePrint. Their availability can still be affected by rate limits, public-access restrictions, or provider blocking. IEEE Xplore is treated as a metadata/publisher-access source rather than a separately configured credential slot in this MCP installation.


