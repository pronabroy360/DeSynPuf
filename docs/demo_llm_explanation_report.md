# LLM Claims Explanation Examples

These examples are generated from synthetic CMS DE-SynPUF-style beneficiary-year features.
They are safe, non-diagnostic explanations for portfolio demonstration only.

Guardrails:

- Use only structured synthetic or aggregate fields.
- Do not infer real patient facts.
- Do not diagnose or recommend treatment.
- State that the explanation is not clinical advice.

## Example 1: `DEMO_BENE_001` in 2009

| Field | Value |
| --- | ---: |
| `age` | 74 |
| `chronic_condition_count` | 4 |
| `inpatient_claims_count` | 1 |
| `outpatient_claims_count` | 1 |
| `carrier_claims_count` | 0 |
| `prescription_events_count` | 1 |
| `total_synthetic_cost` | $7,620 |
| `risk_percentile` | 100 |

**Explanation**

For DEMO_BENE_001 in 2009, total synthetic cost is $7,620. The risk percentile is approximately 100. The main cost/utilization drivers are at least one inpatient claim, multiple chronic-condition indicators. Flagged chronic-condition indicators include: heart failure, copd, diabetes, ischemic heart. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 2: `DEMO_BENE_001` in 2008

| Field | Value |
| --- | ---: |
| `age` | 73 |
| `chronic_condition_count` | 4 |
| `inpatient_claims_count` | 1 |
| `outpatient_claims_count` | 0 |
| `carrier_claims_count` | 1 |
| `prescription_events_count` | 1 |
| `total_synthetic_cost` | $2,780 |
| `risk_percentile` | 100 |

**Explanation**

For DEMO_BENE_001 in 2008, total synthetic cost is $2,780. The risk percentile is approximately 100. The main cost/utilization drivers are at least one inpatient claim, multiple chronic-condition indicators. Flagged chronic-condition indicators include: heart failure, copd, diabetes, ischemic heart. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 3: `DEMO_BENE_002` in 2008

| Field | Value |
| --- | ---: |
| `age` | 66 |
| `chronic_condition_count` | 1 |
| `inpatient_claims_count` | 0 |
| `outpatient_claims_count` | 1 |
| `carrier_claims_count` | 0 |
| `prescription_events_count` | 0 |
| `total_synthetic_cost` | $300 |
| `risk_percentile` | 67 |

**Explanation**

For DEMO_BENE_002 in 2008, total synthetic cost is $300. The risk percentile is approximately 67. The main cost/utilization drivers are the combined synthetic cost and utilization profile. Flagged chronic-condition indicators include: depression. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 4: `DEMO_BENE_002` in 2009

| Field | Value |
| --- | ---: |
| `age` | 67 |
| `chronic_condition_count` | 1 |
| `inpatient_claims_count` | 0 |
| `outpatient_claims_count` | 0 |
| `carrier_claims_count` | 1 |
| `prescription_events_count` | 1 |
| `total_synthetic_cost` | $210 |
| `risk_percentile` | 67 |

**Explanation**

For DEMO_BENE_002 in 2009, total synthetic cost is $210. The risk percentile is approximately 67. The main cost/utilization drivers are the combined synthetic cost and utilization profile. Flagged chronic-condition indicators include: depression. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.

## Example 5: `DEMO_BENE_003` in 2008

| Field | Value |
| --- | ---: |
| `age` | 58 |
| `chronic_condition_count` | 0 |
| `inpatient_claims_count` | 0 |
| `outpatient_claims_count` | 0 |
| `carrier_claims_count` | 1 |
| `prescription_events_count` | 0 |
| `total_synthetic_cost` | $75 |
| `risk_percentile` | 33 |

**Explanation**

For DEMO_BENE_003 in 2008, total synthetic cost is $75. The risk percentile is approximately 33. The main cost/utilization drivers are the combined synthetic cost and utilization profile. Flagged chronic-condition indicators include: none flagged. This explanation is based only on synthetic CMS DE-SynPUF data and is not clinical advice.
