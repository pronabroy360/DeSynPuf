# Project Summary

This project demonstrates a reproducible Medicare-style claims data pipeline using the CMS 2008-2010 Data Entrepreneurs' Synthetic Public Use File (DE-SynPUF). It ingests raw CMS Sample 1 files, builds a local DuckDB analytical warehouse, engineers longitudinal patient-year features, and supports claims analytics, risk modeling, and safe synthetic explanations.

## Goals

- Build a clean relational claims database from public synthetic Medicare files.
- Create patient-level longitudinal features across 2008, 2009, and 2010.
- Analyze synthetic cost and utilization by claim type and chronic-condition indicators.
- Predict next-year high-cost beneficiaries using previous-year features.
- Provide a Streamlit dashboard and FastAPI service for portfolio demonstrations.
- Add an LLM-ready explanation layer with explicit non-diagnostic guardrails.

## Dataset Scope

Version 1 targets **DE1.0 Sample 1** only. CMS states that each DE-SynPUF sample contains beneficiary summary, inpatient, outpatient, carrier, and prescription drug event files, with carrier split into two files because of file size constraints.

## Responsible Framing

DE-SynPUF is synthetic and should be framed as a data engineering and analytics demonstration. It should not be used to make clinical claims about real Medicare beneficiaries.
