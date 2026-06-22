# Extraction eval harness

This manual harness measures extraction accuracy and run-to-run variance by provider.
It is separate from `tests/tieout`, which validates the deterministic income engines.

## Local documents

Put hand-verified PDFs in:

```text
eval/extraction/documents/
```

The PDFs are gitignored because they may contain borrower NPI/PII. Commit labels only in
`labels.json`: document id, local path, document type, expected fields, and optional
subtotal target.

Expected local files for the default labels:

```text
eval/extraction/documents/hendrickson_2023_tax_return.pdf
eval/extraction/documents/hendrickson_2024_tax_return.pdf
eval/extraction/documents/saunders_schedule_e.pdf
eval/extraction/documents/w2_fake_filled.pdf
```

## Run

Claude vision:

```powershell
python -m eval.extraction.run --provider anthropic --runs 5
```

Ollama text model:

```powershell
python -m eval.extraction.run --provider ollama --model llama3.2:latest --num-gpu 0 --runs 5
```

The command prints a Markdown summary and writes a JSON result under
`eval/extraction/results/`. Results are gitignored because they can contain real
borrower-derived values.

## Reading the report

The report shows exact field accuracy, whether any field varied across runs, and whether
the resulting income subtotal ties out within the configured tolerance. A miss is not
authoritative income; it is a review item for the broker/underwriter.
