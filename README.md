# 🚗 AI-Powered Car Lease & Loan Contract Review & Negotiation Assistant

> Developed as part of the **Infosys Virtual Internship Program**

------------------------------------------------------------------------

## 📌 Overview

The **Car Lease / Loan Contract Review & Negotiation Assistant** is an
AI-powered application that helps users understand, analyze, and
negotiate car lease or loan agreements.

Car financing contracts are often long, complex, and filled with
financial terms that are difficult to interpret. This system uses
**Large Language Models (LLMs)** to automatically extract important
clauses, analyze pricing fairness, verify vehicle details using VIN
data, and assist users in negotiating better terms.

The goal is simple:

> Turn confusing car contracts into clear, structured, and actionable
> insights.

------------------------------------------------------------------------

## 🎯 Problem Statement

Most consumers sign auto lease or loan contracts without fully
understanding:

-   Actual APR (Annual Percentage Rate)
-   Hidden fees and penalties
-   Early termination conditions
-   Mileage overage charges
-   Residual value structure
-   Whether the deal is fair compared to the market

This creates **information asymmetry** between dealers and customers.

This project reduces that gap using AI.

------------------------------------------------------------------------

## 🚀 Key Features

### 1️⃣ AI-Based Contract Analysis

Upload a lease/loan contract (PDF or image), and the system extracts:

-   Interest Rate / APR\
-   Lease Term Duration\
-   Monthly Payment\
-   Down Payment\
-   Residual Value\
-   Mileage Allowance & Overage Charges\
-   Early Termination Clause\
-   Buyout Option\
-   Maintenance Responsibilities\
-   Warranty & Insurance Coverage\
-   Late Fees / Penalties

**Output:** - Structured summary (JSON) - Easy-to-read explanation -
Contract Fairness Score

------------------------------------------------------------------------

### 2️⃣ Vehicle Price Estimation

The system integrates public vehicle pricing sources to estimate:

-   Fair purchase price range
-   Lease benchmark comparison
-   Market positioning of the deal

This helps users understand whether they are overpaying.

------------------------------------------------------------------------

### 3️⃣ VIN-Based Vehicle Information

Using the vehicle's VIN number, the app retrieves:

-   Manufacturer details\
-   Model & year\
-   Recall history\
-   Public registration data\
-   Basic vehicle specifications

APIs Used: - NHTSA Vehicle API\
- Public vehicle datasets

------------------------------------------------------------------------

### 4️⃣ AI Negotiation Assistant

An intelligent chatbot that:

-   Suggests negotiation strategies\
-   Flags unfair clauses\
-   Helps draft negotiation emails/messages\
-   Provides leverage points based on extracted contract data

------------------------------------------------------------------------

### 5️⃣ Mobile-First Interface (Flutter)

The app includes:

-   Contract upload
-   SLA summary viewer
-   Offer comparison dashboard
-   VIN report viewer
-   Negotiation chatbot
-   User authentication

------------------------------------------------------------------------

## 🛠 Tech Stack

### Backend

-   Python / Node.js API
-   Large Language Models (OpenAI / Claude / Llama)
-   OCR (Tesseract / Vision API)
-   REST API integrations

### Frontend

-   Flutter (Cross-platform mobile development)

### Database

-   Structured relational schema
-   Contract storage
-   Extracted SLA fields
-   VIN reports
-   Pricing data
-   Negotiation threads

------------------------------------------------------------------------

## 🧠 How It Works

1.  User uploads contract (PDF/Image)
2.  OCR extracts text
3.  LLM processes document and extracts key clauses
4.  VIN API fetches vehicle information
5.  Pricing engine computes market comparison
6.  System generates structured summary + fairness score
7.  Negotiation assistant provides actionable guidance

------------------------------------------------------------------------

## 📊 Contract Fairness Score

The fairness score is computed based on:

-   APR comparison with market rates
-   Hidden or excessive penalties
-   Residual value structure
-   Lease terms vs market benchmarks
-   Pricing deviation

This provides a simplified indicator of how competitive the deal is.

------------------------------------------------------------------------

## 📅 Project Milestones

### Phase 1

-   Backend setup
-   Document upload API
-   OCR integration

### Phase 2

-   LLM SLA extraction engine
-   VIN API integration

### Phase 3

-   Flutter MVP
-   Negotiation chatbot

### Phase 4

-   Market price integration
-   Fairness score computation
-   End-to-end testing and deployment

------------------------------------------------------------------------

## 📂 Project Structure

    /backend
        /ocr
        /llm_engine
        /vin_service
        /pricing_engine
    /frontend
        /flutter_app
    /docs

------------------------------------------------------------------------

## ▶️ How to Run

### Backend

``` bash
pip install -r requirements.txt
python app.py
```

### Flutter App

``` bash
flutter pub get
flutter run
```

------------------------------------------------------------------------

## 🎓 Internship Acknowledgment

This project was developed as part of the **Infosys Virtual Internship
Program**, where the objective was to design and prototype an AI-driven
solution addressing real-world financial and consumer transparency
challenges.

The internship provided the framework and structured milestones under
which this system was conceptualized and developed.

------------------------------------------------------------------------

## 📌 Expected Impact

-   Increased consumer transparency in automotive financing\
-   Reduced hidden lease penalties\
-   Data-driven negotiation support\
-   Improved financial decision-making

------------------------------------------------------------------------

## ⚠️ Limitations

-   LLM outputs may require validation for legal accuracy\
-   OCR quality affects extraction precision\
-   Some vehicle pricing APIs offer limited free access\
-   Paid vehicle history providers (e.g., Carfax) are not directly
    integrated

------------------------------------------------------------------------

## 🔮 Future Improvements

-   Fine-tuned legal LLM model
-   Dealer-side analytics dashboard
-   Integration with paid vehicle history APIs
-   Web version alongside mobile app
-   Advanced fairness scoring using ML models

------------------------------------------------------------------------

## 📜 License

MIT License

------------------------------------------------------------------------

## ✨ Final Note

Car contracts are complex by design.\
This project transforms them into structured, understandable, and
negotiable financial documents using AI.