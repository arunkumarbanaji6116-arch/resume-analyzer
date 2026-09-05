# Resume Analyzer & CareerForge AI 🚀

An AI-powered career platform designed to accelerate technical and professional job search success. Powered by **Google Gemini LLM** and high-accuracy in-memory OCR.

---

## ✨ Features

- **📄 Resume Review (Image OCR)**:
  - Upload resume screenshots or images (PNG, JPG, WEBP).
  - Secure in-memory OCR extraction using Tesseract / RapidOCR ONNX.
  - Comprehensive review of content, action verbs, quantified outcomes, and ATS readiness with Google Gemini.

- **🎯 Job Analyzer**:
  - Semantic job description vs. resume matching.
  - Accurate ATS match scoring (0–100%) and fit classification (*Strong Match*, *Competitive Match*, *Growth Opportunity*).
  - Identification of matched competencies and missing required keywords.
  - Actionable resume tailoring recommendations for target roles.
  - Supports both direct text input and screenshot OCR uploads.

- **🧭 Career Coach**:
  - Dynamic 4-phase milestone execution roadmaps tailored to experience level and timeline.
  - Weekly action sprint checklists.
  - Top recognized industry certifications and credentials.
  - High-converting LinkedIn networking & informational interview outreach scripts.
  - Print/Save execution plans for offline tracking.

- **🎙️ Interview Lab**:
  - Interactive mock interview simulator across 7 technical and professional tracks.
  - STAR methodology rubric assessment (Situation, Task, Action, Result).
  - Real-time word counter and live running score tracking across multi-question drills.
  - Actionable feedback highlighting strengths and concrete improvement areas.
  - Post-drill performance scorecard.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask, SQLite
- **AI / LLM**: Google Gemini SDK (google-genai), gemini-flash-lite-latest
- **OCR**: apidocr-onnxruntime, pytesseract, Pillow
- **Frontend**: HTML5, CSS3 Modern Glassmorphism UI, Responsive JavaScript

---

## 🚀 Quick Start

### 1. Clone Repository
`ash
git clone https://github.com/arunkumarbanaji6116-arch/resume-analyzer.git
cd resume-analyzer
`

### 2. Install Dependencies
`ash
pip install -r requirements.txt
`

### 3. Configure Environment Variables
Copy .env.example to .env:
`ash
cp .env.example .env
`
Edit .env to add your Google Gemini API key:
`env
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=true
GEMINI_API_KEY=your-actual-gemini-api-key
`

### 4. Run the Application
`ash
python app.py
`
Open **http://127.0.0.1:5000** in your browser.
