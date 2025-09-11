# IMAGENES-API

IMAGENES-API is a FastAPI-based web service that allows authenticated users to classify medical images (e.g., mammograms or MRI scans) for cancer detection using a trained CNN model. This microservice is part of the **Carealytica** ecosystem and is designed for deployment in secure healthcare environments.

---

## 🏗️ Project Structure

```
IMAGENES-API/
├── auth/                 # Authentication (JWT, user roles)
├── core/                 # Config, database, environment management
├── entity/               # Pydantic models and business schemas
├── logs/                 # Logging configuration and log storage
├── model/                # ML model loading and prediction
├── postman/              # Postman collection for testing
├── routers/              # API endpoints (e.g., /classify)
├── utils/                # Utility/helper functions
├── .env.example          # Template for environment variables
├── .gitignore
├── .dockerignore
├── app.py                # FastAPI entrypoint
├── Dockerfile            # Docker setup for deployment
├── requirements.txt      # Python dependencies
└── README.md             # You are here
```

---

## 🚀 Features

- 🔐 **JWT Authentication**: Secure endpoints with token-based access
- 🖼️ **Image Classification**: CNN model for binary classification (`cancer` / `not_cancer`)
- 📦 **MongoDB Integration**: Store prediction logs and metadata
- 📃 **Logging**: Structured logs for debugging and monitoring
- 🧪 **Postman Support**: Collection included for easy API testing
- 🐳 **Dockerized**: Easily deployable using Docker

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/romanstephenson/imagenes-api.git
cd imagenes-api
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create and Configure `.env`

Copy from example:

```bash
cp .env.example .env
```

Edit `.env` and update:
- `JWT_SECRET_KEY`
- `MONGO_URI`
- `MODEL_PATH`

---

## ▶️ Run the API

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8002
```

---

## 🧪 Postman

Use the Postman collection in the `/postman` directory to test:
- `POST /imagenes/classify` (protected)
- `POST /imagenes/auth/login`
- `POST /imagenes/auth/logout`

---

## 📦 Docker (Optional)

Build and run with Docker:

```bash
docker build -t imagenes-api .
docker run -p 8002:8002 --env-file .env imagenes-api
```

---

## ✅ Example Request

```http
POST /imagenes/classify
Authorization: Bearer <JWT>
Content-Type: multipart/form-data
Body:
  file: <image_file.png>
```

**Response:**

```json
{
  "prediction": "cancer",
  "confidence": 0.94
}
```

---

## 📁 Environment Variables

See `.env.example` for a full list.

---

## 📄 License
MIT License (c) 2025 Carealytica