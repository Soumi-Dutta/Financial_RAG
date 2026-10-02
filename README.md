# Financial RAG Assistant

A basic Financial RAG proof-of-concept for an appliance and service-centre business.

The project uses a synthetic three-year financial and service dataset to answer questions about revenue, direct cost, gross profit, customer performance, repair profitability, warranty impact, appliance performance, business segments, regions, and basic financial risk signals.

All financial answers are based on the synthetic POC dataset.

---

## 1. Project Objective

The objective of this project is to build a basic Retrieval-Augmented Generation (RAG) chatbot that can answer natural-language financial questions using structured appliance and service-centre data.

The system combines:

- Excel-based financial data
- Pandas-based deterministic calculations
- Local vector search using FAISS
- Sentence-transformer embeddings
- An LLM for natural-language answer generation
- Streamlit for the user interface
- Source and evidence display for answers

The project is a proof-of-concept and is not intended for production financial reporting.

---

## 2. Dataset
The project uses a synthetic Excel dataset:

```text
data/financial_rag_poc_dataset.xlsx