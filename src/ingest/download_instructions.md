# Download Instructions

Download **DE1.0 Sample 1** from the CMS DE-SynPUF Sample 1 page:

<https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf/de10-sample-1>

Place all eight ZIP or CSV files in:

```text
data/raw/
```

Expected Sample 1 files:

- 2008 Beneficiary Summary
- 2009 Beneficiary Summary
- 2010 Beneficiary Summary
- 2008-2010 Inpatient Claims
- 2008-2010 Outpatient Claims
- 2008-2010 Prescription Drug Events
- 2008-2010 Carrier Claims 1
- 2008-2010 Carrier Claims 2

Do not commit files under `data/raw/`. They are ignored by git.

Then run:

```bash
make ingest
make transform
```
