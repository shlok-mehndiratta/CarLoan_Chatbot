# Chapter 2: Environment Setup

[← Previous: Introduction](01-introduction.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Architecture →](03-project-architecture.md)

---

## 2.1 Prerequisites Overview

Before writing any code, you need these tools installed:

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend programming language |
| pip | Latest | Python package manager |
| Ollama | Latest | Run AI models locally |
| Flutter | 3.x | Mobile app development |
| Tesseract OCR | 4.x | Read scanned PDFs |
| Git | Any | Version control |
| Docker | Latest | (Optional) Containerized deployment |

---

## 2.2 Step 1: Install Python 3.12

Python is the main language for the entire backend. We use version 3.12 for modern features like improved type hints and performance.

### On Ubuntu/Debian Linux:

```bash
# Update package list
sudo apt update

# Install Python 3.12 and essential tools
sudo apt install python3.12 python3.12-venv python3-pip -y

# Verify installation
python3 --version
# Expected output: Python 3.12.x
```

### On macOS:

```bash
# Using Homebrew (install Homebrew first from https://brew.sh if needed)
brew install python@3.12

# Verify
python3 --version
```

### On Windows:

1. Download from https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Open Command Prompt and verify: `python --version`

### Why Python 3.12?

- **Type hints**: `dict | None` syntax (cleaner than `Optional[dict]`)
- **Performance**: 5% faster than Python 3.11
- **Ecosystem**: All our libraries (FastAPI, LangChain) support it

---

## 2.3 Step 2: Create Project Directory

```bash
# Create the project folder
mkdir -p ~/Desktop/Infosys/CARChatbot
cd ~/Desktop/Infosys/CARChatbot

# Create the backend directory
mkdir -p backend
mkdir -p backend/tests

# Create the Flutter app directory (we'll set this up later)
mkdir -p app
```

---

## 2.4 Step 3: Set Up Python Virtual Environment

A **virtual environment** isolates your project's Python packages from the system Python. This prevents conflicts between different projects.

```bash
# Navigate to project root
cd ~/Desktop/Infosys/CARChatbot

# Create virtual environment
python3 -m venv venv

# Activate it (you'll need to do this every time you open a new terminal)
source venv/bin/activate

# Your prompt should now show (venv) at the beginning
# Example: (venv) user@machine:~/Desktop/Infosys/CARChatbot$
```

**Why virtual environments?**

Without a virtual environment, if Project A needs `fastapi==0.90` and Project B needs `fastapi==0.110`, they would conflict. Virtual environments give each project its own isolated set of packages.

---

## 2.5 Step 4: Install Python Dependencies

Create the `requirements.txt` file with all necessary packages:

```bash
cat > requirements.txt << 'EOF'
# Core
fastapi>=0.95.0
uvicorn>=0.22.0
uvicorn[standard]>=0.22.0
python-dotenv>=1.0.0
python-multipart>=0.0.6
pydantic>=2.0.0

# PDF / OCR
PyPDF2>=3.0.0
pdfplumber>=0.11.8
pdfminer.six>=20221105
pdf2image>=1.16.0
pytesseract>=0.3.10

# LLM
langchain-ollama>=0.1.0
langchain-core>=0.1.0

# HTTP / APIs
requests>=2.28.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
EOF
```

Now install everything:

```bash
pip install -r requirements.txt
```

### What Each Package Does:

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework — creates REST API endpoints |
| `uvicorn` | ASGI web server — runs FastAPI |
| `python-dotenv` | Loads `.env` files for configuration |
| `python-multipart` | Handles file uploads (PDF upload) |
| `pydantic` | Data validation — ensures API inputs/outputs are correct |
| `PyPDF2` | Reads text from digital PDF files |
| `pdfplumber` | Alternative PDF text extractor (better for tables) |
| `pdfminer.six` | Another PDF extractor (best for complex layouts) |
| `pdf2image` | Converts PDF pages to images (for OCR) |
| `pytesseract` | Python wrapper for Tesseract OCR |
| `langchain-ollama` | Connect to Ollama LLM from LangChain |
| `langchain-core` | Core LangChain utilities for messaging |
| `requests` | Make HTTP calls to external APIs (NHTSA) |
| `pytest` | Python testing framework |
| `httpx` | Async HTTP client (used by FastAPI test client) |

---

## 2.6 Step 5: Install Tesseract OCR

Tesseract is needed to read **scanned** or **photographed** PDFs. Many real-world contracts are scanned images, not digital text.

### On Ubuntu/Debian:

```bash
sudo apt install tesseract-ocr poppler-utils -y

# Verify
tesseract --version
# Expected: tesseract 4.x or 5.x

# poppler-utils provides the `pdftoppm` command used by pdf2image
```

### On macOS:

```bash
brew install tesseract poppler
```

### On Windows:

1. Download Tesseract from https://github.com/tesseract-ocr/tesseract
2. Install and note the installation path
3. Add to system PATH

**How OCR works in our project:**
1. First, we try to extract text directly from the PDF (digital PDF)
2. If that fails (scanned PDF), we convert each page to an image
3. Tesseract reads the image and converts it back to text

---

## 2.7 Step 6: Install and Configure Ollama

Ollama lets you run Large Language Models (LLMs) locally on your computer — no cloud API keys or costs required.

### Install Ollama:

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### Download the Language Model:

```bash
# Pull the Llama 3.2 model (about 2-4 GB download)
ollama pull llama3.2

# Verify it's downloaded
ollama list
# Should show: llama3.2
```

### Start the Ollama Server:

```bash
# Start Ollama (runs on http://localhost:11434)
ollama serve
```

> **Note:** Keep this running in a **separate terminal** while working on the project. The backend connects to Ollama on port 11434.

### Verify Ollama is Running:

```bash
# In another terminal, test the API
curl http://localhost:11434/api/tags
# Should return JSON with your downloaded models
```

**Why Ollama instead of OpenAI/ChatGPT?**
- **Free** — no API key costs
- **Private** — your contract data never leaves your computer
- **Fast** — no network latency for each API call
- **Offline** — works without internet after initial model download

---

## 2.8 Step 7: Install Flutter (for Mobile App)

Flutter is Google's UI toolkit for building natively compiled applications for mobile, web, and desktop from a single codebase.

### On Linux:

```bash
# Download Flutter SDK
cd ~
git clone https://github.com/flutter/flutter.git -b stable
echo 'export PATH="$HOME/flutter/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
flutter --version
flutter doctor
```

### On macOS:

```bash
brew install --cask flutter
flutter doctor
```

### On Windows:

1. Download from https://docs.flutter.dev/get-started/install/windows
2. Extract to `C:\flutter`
3. Add `C:\flutter\bin` to your PATH

### Run Flutter Doctor:

```bash
flutter doctor
```

This checks your environment. You need at least:
- ✅ Flutter SDK
- ✅ Android toolchain (for Android development)
- ✅ Chrome (for web debugging)

> **Note:** The Flutter app is optional for backend-first development. You can build and test the entire backend without Flutter.

---

## 2.9 Step 8: Install Docker (Optional — for Deployment)

Docker packages your application into containers that run consistently on any machine.

### On Ubuntu:

```bash
# Install Docker
sudo apt install docker.io docker-compose -y

# Add your user to the docker group (avoids needing sudo)
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker --version
docker-compose --version
```

### On macOS/Windows:

Download Docker Desktop from https://www.docker.com/products/docker-desktop/

---

## 2.10 Verification Checklist

Run these commands to verify everything is set up:

```bash
# Python
python3 --version               # ✅ Python 3.12.x

# Virtual environment
source venv/bin/activate         # ✅ (venv) appears in prompt

# FastAPI
python3 -c "import fastapi; print(fastapi.__version__)"  # ✅ 0.x.x

# Tesseract
tesseract --version              # ✅ tesseract 4.x or 5.x

# Ollama (in separate terminal: ollama serve)
curl -s http://localhost:11434/api/tags | python3 -m json.tool  # ✅ JSON response

# Flutter (optional)
flutter --version                # ✅ Flutter 3.x.x
```

If any of these fail, refer back to the installation steps for that tool.

---

[← Previous: Introduction](01-introduction.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Architecture →](03-project-architecture.md)
