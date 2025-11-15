# E-commerce Chatbot - Rasa 3.6.20

Chatbot hỗ trợ khách hàng cho website e-commerce.

## Quick Start

### 1. Train Model
```bash
.\venv\Scripts\Activate.ps1
rasa train
```

### 2. Run Chatbot

**Terminal 1 - Action Server:**
```bash
.\venv\Scripts\Activate.ps1
rasa run actions
```

**Terminal 2 - Rasa Server:**
```bash
.\venv\Scripts\Activate.ps1
rasa run --enable-api --cors "*"
```

### 3. Test
```bash
rasa shell
```

## API Usage

**Endpoint:** `POST http://localhost:5005/webhooks/rest/webhook`

**Body:**
```json
{
  "sender": "user_id",
  "message": "hello"
}
```

## Environment

- Python 3.10.8
- Rasa 3.6.20
- Backend: http://localhost:3001
- API Key: Xem `.env`

## Project Structure

```
├── actions/          # Custom actions (API calls)
├── data/            # Training data (NLU, stories, rules)
├── models/          # Trained models
├── config.yml       # Rasa pipeline config
├── domain.yml       # Intents, entities, responses
├── endpoints.yml    # Server endpoints
└── .env            # API keys & configs
```
