# Submission status

**Live generation is incomplete.** The latest user-reported Colab run failed sentence-coverage validation. The provided preview PDF and sample book show a labelled offline fixture, not a successful live-generated book. See `submission/Live_Run_Status.txt`.

# Multi-Agent Book Writer with Free Colab Mode

A small Python system that plans, researches, writes, edits and fact-checks a three-chapter book for first-time small-business owners in India. Each role makes a separate model call and passes a structured JSON result through a central orchestrator. The book uses numbered citations, chapter-specific references, and a final Takeaway line.

**Current verification:** all 32 deterministic tests pass, including local-backend preprocessing and fact-check batching. The Colab notebook's code cells pass syntax checks. A real GPU/model generation run has NOT been performed in the preparation environment because it has no GPU or model weights. Live API mode has not been tested either. The example chapters remain explicitly labelled prewritten fixtures.

## Free Colab run without an API key

Open `Free_Colab_Book_Writer.ipynb` in Google Colab using **File → Upload notebook**. Choose **Runtime → Change runtime type → GPU** (T4 if available). Run cells in order and upload `UPI_Book_Writer_Free_Colab.zip` when the notebook asks for the updated project.

The notebook installs `requirements-colab.txt`, verifies a CUDA GPU, tests readable public sources, loads **Qwen/Qwen2.5-7B-Instruct** in 4-bit precision, and runs all five roles using that local model. No OpenAI key or inference API billing is involved. Model files are downloaded from Hugging Face; the public model does not require a token. The download is several GB, and generation may take a substantial part of a Colab session. GPU/session resources are not guaranteed on the free tier.

The local Writer generates plain-prose paragraphs separately and adds paragraphs until it reaches at least 630 prose words, with a maximum of 16 paragraphs. Individual paragraphs may be 35–115 words, while the final 600–900-word chapter gate remains mandatory. It produces numerical citations in the prose, and the existing validator and Fact-checker check the cited sources and factual support. Writer output is not parsed as JSON. It allows two attempts per paragraph. The local Fact-checker selects evidence IDs, and code copies the original excerpt. Semantic support and all final checks remain required. The local model uses the same orchestrator, revision gate, sentence coverage checks and publication rules. The Researcher selects numbered evidence candidates; code copies their original text, so the model cannot paraphrase a quotation into the research packet. Source windows sent to the model are verbatim extracts from fetched pages; claims and quotes are still validated against the full original source. Fact-checking runs in batches of six sentences, preserving original indices. The Editor sees prior prose without the earlier full source pages. No prompt is silently truncated; exceeding the 6,000-input-token local limit fails with an explicit diagnostic. Smaller source windows can miss evidence; the model must omit unsupported claims. A local model may fail quality or JSON checks. Failures are not automatically accepted.

For a supported local GPU environment outside Colab:

```bash
python -m pip install -r requirements-colab.txt
python -m bookwriter --mode local --out runs/local-1 --max-revisions 2
```

The local backend requires a CUDA-enabled PyTorch environment. `bookwriter/local.py` uses separate role prompts on one shared model, not separate copies of the model. This saves memory. Successful actual generation has status `accepted` and mode `local`; the fixture replay still has `demo_complete`.

The notebook provides visible progress, a status/error cell that makes no model calls, book previews, and a download cell that packages repository files plus the accepted output. It excludes model weights, credentials and complete scraped pages. Add your actual screenshots before submitting.

Official implementation references:

- Model card: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- Quantization: https://huggingface.co/docs/transformers/quantization/bitsandbytes
- Colab resource limits: https://research.google.com/colaboratory/faq.html


## Quick start

Python 3.10 or later. No external Python packages are required. Run commands from the extracted `upi-book-writer` directory.

```bash
python -m unittest discover -s tests -v
python -m bookwriter --mode demo --out runs/demo-1
```

Open `runs/demo-1/book.html` and `runs/demo-1/run.html` in a browser. Each output directory must be new; the application never overwrites an earlier run. Demo mode deliberately introduces a bullet in the first draft so that you can observe rejection and revision. It uses editorial source summaries and fixture reviews, and makes no LLM or network calls. The included `examples/demo-run` is an actual execution of that replay.

## Live run

Obtain an API key from your chosen OpenAI-compatible provider. Use a model available to your account that supports the Chat Completions endpoint and can reliably return JSON. `OPENAI_MODEL` is deliberately not hard-coded. API usage may incur charges.

macOS / Linux:

```bash
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='your-model-id'
# Optional, defaults to https://api.openai.com/v1
export OPENAI_BASE_URL='https://api.openai.com/v1'
python -m bookwriter --mode live --out runs/live-1 --max-revisions 2
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = 'your-key'
$env:OPENAI_MODEL = 'your-model-id'
$env:OPENAI_BASE_URL = 'https://api.openai.com/v1'
python -m bookwriter --mode live --out runs/live-1 --max-revisions 2
```

Never commit your key. `.env.example` is a reference only: this program does not automatically load `.env` files. Normal API calls send the book brief, drafts and fetched public source text to the configured provider.

A successful local or API live run writes `status.json` with `status: accepted`. A demo writes `demo_complete`, so the two cannot be mistaken for each other. A rejected or failed run writes its diagnostics but never publishes a final book. Existing output directories cause a clear failure; choose a new directory name.

## Agent responsibilities

| Role | Input | Output |
|---|---|---|
| Planner | Book brief | Exactly three chapter plans, goals and research questions |
| Researcher | Plan and approved source URLs | Downloaded text plus exact evidence excerpts and suggested uses |
| Writer | Plan, evidence and revision feedback | Chapter title, prose paragraphs and Takeaway line |
| Editor | Current draft and accepted earlier chapters | Grammar, readability, voice and flow issues |
| Fact-checker | Every draft sentence and original source text | Classification and supporting excerpts for each factual sentence |

The roles share JSON objects, not unrestricted chats. The orchestrator owns state, iteration limits, rendering and publication. Editor and Fact-checker review the same draft; their feedback goes back to Writer. Reviews run sequentially to keep the implementation easy to inspect. See `docs/architecture.svg` or `docs/architecture.png`.

## Source handling and citation checks

The Researcher fetches a small curated corpus from government, NPCI BHIM and a bank's own safety guidance. This deliberately avoids asking a model to invent links. Add or replace sources in `examples/source_cards.json` and, for new hosts, update the explicit allowlist in `bookwriter/core.py`. Live mode ignores the cards' editorial summaries and fetches the original pages. This version is tailored to the supplied UPI brief; it is not a general-purpose search engine.

Live fetching requires readable HTML or plain text, HTTPS and an approved host. Redirects must remain on approved hosts. JavaScript-only shells, unsupported formats, unavailable pages and very large responses are rejected. Source records include retrieval time, final URL and SHA-256 text hashes. Research evidence excerpts must occur verbatim in downloaded text. The Fact-checker reads original source text rather than trusting the Researcher's interpretation.

Mechanical checks enforce 600–900 words, no chapter bullets, one final Takeaway line, known citation IDs and citations on sentences containing numerals. Semantic review covers **every sentence**, including the takeaway, to identify facts without numerals. It must return exactly one check per sentence. Every cited source needs an exact excerpt; unsupported claims, missing sentence checks, fabricated excerpts and unknown references block release. A link that exists is not enough: the model is asked to judge whether the evidence supports the claim. The renderer creates each chapter's reference list from its actual citations.

The final gate refetches all used sources. Changed or inaccessible sources block release. A changed page may include harmless navigation changes; the conservative response is to fail and rerun. This avoids quietly publishing against evidence different from what was reviewed.

**Limits:** a model can misclassify a factual sentence as advice or misjudge entailment. Exact text matching detects fabricated quotations, not semantic truth. HTML extraction may include navigation or miss content. Sentence segmentation is deliberately simple and can be confused by abbreviations. An official page can contain stale or conflicting guidance. Human review is still needed, especially for fees, limits, refund timing and claims of guaranteed outcomes. The included fixture does not contain current fee/limit claims; BHIM's FAQ showed inconsistent refund timings during preparation.

## Revision, retries and audit trail

`--max-revisions 2` means one initial draft and at most two revisions per chapter. Reaching the limit fails the run without a final book. Malformed schema responses fail closed; invalid JSON gets bounded repair attempts. Transient HTTP errors and invalid JSON get at most three attempts per model call. Non-transient API errors stop immediately. There is a maximum of 90 total HTTP model attempts per run. A source download times out after 20 seconds; a model call after 120 seconds. These are operational bounds, not a monetary budget.

A run saves its outline, research packet, every draft, every review, source snapshots, event log, final status and reported token usage. These files make the agent interactions inspectable in an interview. `run.html` displays the event log. Source snapshots and drafts may be large, so `runs/` is ignored by Git; selectively include your final submission evidence.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover the successful demo, revision-limit rejection, uncited numerals, unknown references, word length, takeaway shape, missing/duplicate sentence reviews, fabricated evidence, unsupported claims, cited advice bypasses, malformed plans, network source failures, disallowed URLs, source changes and output overwrite protection. These are deterministic unit/integration tests. They do not measure real-model quality or certify external links.

## Submission steps

1. Run local mode in Colab, or API live mode with your own key and model. Inspect `status.json`, all chapter reviews and the final book. Manually confirm that every empirical claim has a relevant citation and that the links work.
2. Open `run.html` and `book.html` from that live run. Take actual browser screenshots of the running output and the book. The supplied PNG previews are labelled offline examples and should not be presented as live evidence.
3. Create a GitHub repository and upload the project. Include the final live book, architecture diagram and your live screenshots. Keep credentials and irrelevant source snapshots out of the repository. The assignment leaves the private-access GitHub username as a placeholder, so a public repository avoids that unresolved detail if you are comfortable sharing it.
4. Submit your repository link, architecture diagram and screenshots using the form in the assignment. The brief also mentions email but supplies a form; confirm the intended route with the recruiter if needed. Deadline in the supplied brief: Monday 5 October 2026, 12 PM IST.

## Interview walkthrough

Start with `Pipeline.run` in `bookwriter/core.py`. Explain why the orchestrator controls transitions, why Researcher and Fact-checker have different responsibilities, and how rejection returns feedback to Writer. Demonstrate the deliberate first-draft failure in demo mode, then show one draft and its review JSON side by side. Explain that model review is probabilistic and that mechanical validation is only one layer. Discuss the small curated corpus and the absence of silent source-cache fallback as deliberate scope decisions.

AI coding assistance was used to prepare this project and its fixture examples. Review the code and run it yourself before presenting it; the assignment says shortlisted candidates will walk through their implementation.

## Files

- `bookwriter/core.py`: roles, LLM client, source fetcher, validators, orchestrator and renderer.
- `bookwriter/demo.py`: explicitly labelled offline fixture implementation.
- `bookwriter/__main__.py`: command-line entry point.
- `bookwriter/local.py`: optional 4-bit GPU model backend, excerpt selection and batched fact review.
- `Free_Colab_Book_Writer.ipynb`: ordered cells for a no-key Colab run.
- `examples/chapters.json`: prewritten demo chapters.
- `examples/source_cards.json`: public source metadata and editorial demo summaries.
- `examples/create_fixtures.py`: reproducible construction of the example chapters.
- `examples/demo-run/`: saved offline run with book and audit trail.
- `docs/`: architecture, rendered offline previews and notes.
- `tests/test_pipeline.py`: automated failure and success tests.

API interface reference: https://developers.openai.com/api/reference/resources/chat
