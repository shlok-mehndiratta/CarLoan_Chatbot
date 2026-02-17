# 📖 Complete Project Documentation

## AI-Powered Car Lease & Loan Contract Review and Negotiation Assistant

> **A comprehensive, step-by-step guide to building this project from scratch**
>
> Developed as part of the **Infosys Virtual Internship Program**

---

## Table of Contents

| Chapter | Title | What You'll Learn |
|---------|-------|-------------------|
| [Chapter 1](docs/01-introduction.md) | **Introduction & Problem Statement** | Why this project exists, the problem it solves, and the complete feature set |
| [Chapter 2](docs/02-environment-setup.md) | **Environment Setup** | Installing Python, Flutter, Ollama, and all prerequisites from scratch |
| [Chapter 3](docs/03-project-architecture.md) | **Project Architecture & Database** | System design, folder structure, database schema, and data models |
| [Chapter 4](docs/04-pdf-contract-analysis.md) | **PDF Processing & Contract Analysis** | Reading PDFs, OCR fallback, regex-based financial data extraction |
| [Chapter 5](docs/05-llm-fairness.md) | **LLM Integration & Fairness Scoring** | Connecting Ollama, LLM prompts, merging extractions, and the 6-dimension fairness engine |
| [Chapter 6](docs/06-vin-price.md) | **VIN Lookup & Price Estimation** | NHTSA APIs, vehicle recalls, MSRP database, and depreciation-based pricing |
| [Chapter 7](docs/07-negotiation-chatbot.md) | **Negotiation Chatbot** | Rule-based points, LLM-powered chat, multi-turn conversations, and email generation |
| [Chapter 8](docs/08-fastapi-backend.md) | **FastAPI Backend** | Building the REST API, all 12 endpoints, CORS, middleware, and error handling |
| [Chapter 9](docs/09-flutter-app.md) | **Flutter Mobile App** | Dart models, API service, 6 screens, navigation, and Material Design 3 |
| [Chapter 10](docs/10-testing-deployment.md) | **Testing & Deployment** | pytest suite (79 tests), Docker containerization, and production setup |

---

## Quick Start

If you just want to run the project immediately:

```bash
# Clone and setup
git clone <repository-url>
cd CARChatbot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Ollama (in separate terminal)
ollama pull llama3.2
ollama serve

# Run the backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Open browser
# http://localhost:8000/docs  ← Interactive API documentation
```

For the **full explanation of every line of code**, start with [Chapter 1](docs/01-introduction.md).

---

## Who Is This Documentation For?

This guide is written for:
- **Students** who need to understand every technical decision
- **Beginners** who want to learn by building a real-world AI project
- **Reviewers** who need to evaluate the project's design and implementation
- **Contributors** who want to extend the project with new features

**No prior experience with FastAPI, LLMs, or Flutter is assumed.** Every concept is explained from first principles with code examples.

---

## How to Read This Documentation

1. **Read sequentially** — each chapter builds on the previous one
2. **Copy the code snippets** into the exact file paths shown
3. **Run the verification steps** at the end of each chapter
4. **Don't skip Chapter 2** — environment setup issues cause 90% of problems

> **Estimated time to build from scratch:** 8–12 hours (following all chapters)
