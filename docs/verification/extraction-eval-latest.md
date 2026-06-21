# Extraction accuracy report

## hendrickson_2023_tax_return

SKIPPED: missing fixture `test_documents/hendrickson_2023_tax_return.pdf`

## hendrickson_2024_tax_return

SKIPPED: missing fixture `test_documents/hendrickson_2024_tax_return.pdf`

## w2_fake_clean

| field | expected | got | status |
|---|---:|---:|---|
| `w2_wages` | 85000 | 85000.0 | PASS |
| `w2_federal_tax_withheld` | 12000 | 12000.0 | PASS |
| `tax_year` | null | null | PASS |
| `w2_social_security_wages` | null | null | PASS |
| `w2_medicare_wages` | null | null | PASS |
| `w2_employer_name` | null | null | PASS |
| `w2_employee_name` | null | null | PASS |

Validation high-review flag: expected False, got False (PASS)
Issues: none

## w2_fake_filled

| field | expected | got | status |
|---|---:|---:|---|
| `tax_year` | 2023 | 2023.0 | PASS |
| `w2_wages` | 85000 | 85000.0 | PASS |
| `w2_federal_tax_withheld` | 12500 | 12500.0 | PASS |
| `w2_social_security_wages` | 85000 | 85000.0 | PASS |
| `w2_medicare_wages` | 85000 | 85000.0 | PASS |
| `w2_employer_name` | Acme Corp | null | MISSING |
| `w2_employee_name` | null | null | PASS |

Validation high-review flag: expected False, got False (PASS)
Issues: none

## Aggregate accuracy

| field | correct |
|---|---:|
| `tax_year` | 2/2 |
| `w2_employee_name` | 2/2 |
| `w2_employer_name` | 1/2 |
| `w2_federal_tax_withheld` | 2/2 |
| `w2_medicare_wages` | 2/2 |
| `w2_social_security_wages` | 2/2 |
| `w2_wages` | 2/2 |

## Variance
No variance checked or no changed values.