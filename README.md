# 3GPP Spec Assistant

A small retrieval-augmented generation (RAG) assistant that answers questions about 5G standards
and cites the exact 3GPP specification section it used.

## Problem

Answers to technical 5G questions are spread across large 3GPP specifications. General-purpose LLMs
answer such questions poorly from memory: in the TSpec-LLM study, models answered only 44–51% of
technical questions correctly without retrieval, and 71–75% with a simple RAG pipeline.
Ericsson researchers have explored the same approach for 3GPP standards (TelcoGenAI).

## What this project does

This project is a small reproduction of that idea on one specification, **TS 38.300**
(NR; Overall description). It splits the specification into sections, finds the sections most
relevant to a question, and asks an LLM to answer **only from those sections**, citing them
(for example, "TS 38.300 §4.1"). If the answer is not in the retrieved text, it says so.

The main goal is to **measure** the effect of retrieval:

- **hit@3** on hand-written questions with known answer sections;
- **accuracy without vs. with retrieval** on a sample of TeleQnA multiple-choice questions.

## Status

Work in progress.

- [x] Project setup
- [ ] Ingest and chunk TS 38.300
- [ ] Embeddings and retrieval
- [ ] Cited answers
- [ ] Evaluation
- [ ] Optional: abbreviation expansion with TR 21.905, Streamlit UI, Docker

## References

- A. Karapantelakis et al. (Ericsson), *Using Large Language Models to Understand Telecom Standards*, arXiv:2404.02929
- R. Nikbakht et al., *TSpec-LLM: An Open-source Dataset for LLM Understanding of 3GPP Specifications*, arXiv:2406.01768
- *TeleQnA: A Benchmark Dataset to Assess Large Language Models Telecommunications Knowledge*, arXiv:2310.15051