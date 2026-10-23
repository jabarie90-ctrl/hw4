# Campus Customs (MGT 409 Homework 4)

React + Vite front end and FastAPI / PydanticAI back end for the Campus Customs shop.

## Data pack (required locally — not in git)

Download `data.zip` from the course site and unzip so you have:

```
hw4/data/campus_customs.db
hw4/data/products/
```

### Seeded test user

- Email: `test@campuscustoms.yale.edu`
- Password: `password`

## Setup

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (or `PORTKEY_API_KEY`). Model defaults to `gpt-5.6-luna`.

```bash
# backend
cd backend
python3 -m pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000

# frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Without an API key the chat still answers stock/search from SQLite via a local fallback so you can exercise the UI.

## Layout

```
hw4/
├── AI_prompts.md
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── frontend/
├── backend/
│   ├── main.py
│   ├── agent.py
│   ├── models.py
│   ├── tools.py
│   └── prompts/prompt.md
└── output/
    ├── harness.md
    ├── design.md
    ├── usability.md
    ├── app_check.html
    ├── app_check_images/
    └── audit_trail.json
```
