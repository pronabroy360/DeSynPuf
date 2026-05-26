# LLM Claims Explanation Examples

These examples are generated from synthetic CMS DE-SynPUF-style beneficiary-year features.
They are safe, non-diagnostic explanations for portfolio demonstration only.

Guardrails:

- Use only structured synthetic or aggregate fields.
- Do not infer real patient facts.
- Do not diagnose or recommend treatment.
- State that the explanation is not clinical advice.

## Example 1: `B010E908FD8DED6A` in 2008

| Field | Value |
| --- | ---: |
| `age` | 80 |
| `chronic_condition_count` | 5 |
| `inpatient_claims_count` | 6 |
| `outpatient_claims_count` | 5 |
| `carrier_claims_count` | 35 |
| `prescription_events_count` | 23 |
| `total_synthetic_cost` | $171,540 |
| `risk_percentile` | 100 |

**Explanation**

For B010E908FD8DED6A in 2008, total synthetic cost is $171,540. The risk percentile is approximately 100. The main cost/utilization drivers are repeated inpatient utilization, frequent professional/carrier claims, multiple prescription drug events, multiple chronic-condition indicators. Flagged chronic-condition indicators include: heart failure, kidney disease, diabetes, ischemic heart, rheumatoid arthritis. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 2: `3A9D94388C426924` in 2008

| Field | Value |
| --- | ---: |
| `age` | 84 |
| `chronic_condition_count` | 8 |
| `inpatient_claims_count` | 8 |
| `outpatient_claims_count` | 4 |
| `carrier_claims_count` | 48 |
| `prescription_events_count` | 58 |
| `total_synthetic_cost` | $170,280 |
| `risk_percentile` | 100 |

**Explanation**

For 3A9D94388C426924 in 2008, total synthetic cost is $170,280. The risk percentile is approximately 100. The main cost/utilization drivers are repeated inpatient utilization, frequent professional/carrier claims, multiple prescription drug events, multiple chronic-condition indicators. Flagged chronic-condition indicators include: alzheimers, heart failure, kidney disease, copd, depression, diabetes, ischemic heart, stroke tia. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 3: `F8F72B475A3381DC` in 2008

| Field | Value |
| --- | ---: |
| `age` | 69 |
| `chronic_condition_count` | 11 |
| `inpatient_claims_count` | 7 |
| `outpatient_claims_count` | 11 |
| `carrier_claims_count` | 146 |
| `prescription_events_count` | 17 |
| `total_synthetic_cost` | $161,990 |
| `risk_percentile` | 100 |

**Explanation**

For F8F72B475A3381DC in 2008, total synthetic cost is $161,990. The risk percentile is approximately 100. The main cost/utilization drivers are repeated inpatient utilization, frequent professional/carrier claims, frequent outpatient facility claims, multiple prescription drug events, multiple chronic-condition indicators. Flagged chronic-condition indicators include: alzheimers, heart failure, kidney disease, cancer, copd, depression, diabetes, ischemic heart, osteoporosis, rheumatoid arthritis, stroke tia. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 4: `11B3642EFC2521EB` in 2009

| Field | Value |
| --- | ---: |
| `age` | 38 |
| `chronic_condition_count` | 7 |
| `inpatient_claims_count` | 6 |
| `outpatient_claims_count` | 11 |
| `carrier_claims_count` | 64 |
| `prescription_events_count` | 44 |
| `total_synthetic_cost` | $153,060 |
| `risk_percentile` | 100 |

**Explanation**

For 11B3642EFC2521EB in 2009, total synthetic cost is $153,060. The risk percentile is approximately 100. The main cost/utilization drivers are repeated inpatient utilization, frequent professional/carrier claims, frequent outpatient facility claims, multiple prescription drug events, multiple chronic-condition indicators. Flagged chronic-condition indicators include: alzheimers, heart failure, kidney disease, copd, diabetes, ischemic heart, rheumatoid arthritis. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 5: `8F43AE15B6CD7F39` in 2008

| Field | Value |
| --- | ---: |
| `age` | 40 |
| `chronic_condition_count` | 9 |
| `inpatient_claims_count` | 7 |
| `outpatient_claims_count` | 11 |
| `carrier_claims_count` | 118 |
| `prescription_events_count` | 0 |
| `total_synthetic_cost` | $150,800 |
| `risk_percentile` | 100 |

**Explanation**

For 8F43AE15B6CD7F39 in 2008, total synthetic cost is $150,800. The risk percentile is approximately 100. The main cost/utilization drivers are repeated inpatient utilization, frequent professional/carrier claims, frequent outpatient facility claims, multiple chronic-condition indicators. Flagged chronic-condition indicators include: alzheimers, heart failure, kidney disease, copd, depression, diabetes, ischemic heart, osteoporosis, rheumatoid arthritis. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.
