# 💧 Smart Health Assistant

### AI + Rule-Based Water-Borne Disease Detection System

---

## Overview

**Smart Health Assistant** is an intelligent healthcare web application built using **Streamlit**, combining **Generative AI** and **rule-based logic** to detect potential **water-borne diseases** based on user symptoms.

The system provides:

* AI-powered conversational chatbot
* Structured disease prediction via form
* Admin dashboard for monitoring predictions
* Hybrid detection (AI + rule-based fallback for reliability)

---

## Features

### Disease Prediction (Form-Based)

* Users enter **name + symptoms**
* AI interprets input and predicts possible diseases
* Rule-based fallback ensures prediction even if AI fails
* Provides:

  * Possible disease(s)
  * Precautions
  * Suggested medicines

---

### AI Chatbot

* Interactive health assistant powered by **Google Gemini**
* Maintains short conversational context
* Can handle:

  * Symptoms analysis
  * General queries
  * Date/time responses
  * Basic math queries

---

### Rule-Based Detection

Fallback logic ensures reliability using predefined mappings:

| Disease       | Key Symptoms                 |
| ------------- | ---------------------------- |
| Cholera       | Watery diarrhea, dehydration |
| Typhoid       | Fever, abdominal pain        |
| Dysentery     | Bloody diarrhea, cramps      |
| Hepatitis A/E | Jaundice, fatigue            |

---

### Admin Panel

* View all stored predictions
* Download data as CSV
* Backfill missing disease fields
* Delete records from database

---

## Tech Stack

| Layer    | Technology                    |
| -------- | ----------------------------- |
| Frontend | Streamlit                     |
| Backend  | Python                        |
| AI Model | Google Gemini (Generative AI) |
| Database | Firebase Firestore            |
---

## Project Structure

```
├── main.py              # Frontend (Streamlit UI)
├── backend_code.py      # Backend logic
├── .env                 # API keys & config (NOT uploaded)
├── requirements.txt     # Dependencies
└── README.md            # Documentation
```

---

## Setup Instructions

### Clone Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

---

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Configure Environment Variables

Create a `.env` file:

```env
API_KEY=your_gemini_api_key
FIREBASE_CONFIG=path_to_your_firebase_json
```

**Important:**

* Do NOT upload `.env` or Firebase JSON to GitHub
* Keep credentials secure

---

### Run Application

```bash
streamlit run main.py
```

---

## How It Works

1. User inputs symptoms (chat or form)
2. Input is processed using:

   * AI model (Gemini)
   * Rule-based fallback system
3. Disease is predicted
4. Data is stored in **Firestore**
5. Admin panel allows monitoring

---

## Security Notes

* Sensitive data is stored using environment variables
* Firebase credentials are NOT exposed in code
* Admin panel protected with password

---

## ⚠️ Disclaimer

This application is for **educational purposes only** and **not a substitute for professional medical advice**.
Always consult a qualified healthcare provider.

---

## Future Improvements

* ML-based disease classification
* Multi-language support
* User authentication system
* Deployment with secure secrets management
* Improved symptom NLP processing

---

## Author

Developed by **Akshita Bhardwaj**

---
Give it a ⭐ on GitHub!
