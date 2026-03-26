# Skill-Build Platform MVP

This document describes the industrial skill-build MVP implemented for:

1. Quality root cause copilot (8D/QRQC)
2. Equipment anomaly diagnosis + work-order assistant
3. Operations daily/weekly report agent

## Architecture

- Backend: FastAPI (`mini_agent/platform/api.py`)
- Workflow engine: LangGraph (`mini_agent/platform/workflows.py`)
- Persistence: SQLite metadata + Redis chat memory (`mini_agent/platform/repository.py`)
- LangChain chat runtime: `mini_agent/platform/llm_chat.py`
- Redis:
  - LangChain Redis chat history for real multi-turn memory
  - LangGraph Redis checkpointer for workflow state (with in-memory fallback)
- Frontend: Separate React app (JSX + Vite) under `frontend/`

## API Scope

- `GET /api/task-categories`
- `POST /api/task-categories`
- `PUT /api/task-categories/{category_id}`
- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/{task_id}/messages`
- `POST /api/tasks/{task_id}/messages`
- `GET /api/skills`
- `PUT /api/skills/{skill_id}`
- `POST /api/skill-lab/analyze`
- `POST /api/skill-lab/apply`

## Run

Backend:

```bash
uv run mini-agent-platform --host 0.0.0.0 --port 8001 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

Environment variables:

- `SKILL_BUILD_REDIS_URL`: Redis URL for LangChain chat memory and LangGraph checkpoint
- `SKILL_BUILD_SKILLS_DIR`: Local skills directory to host built-in skills (default: `./mini_agent/skills`)

## Mock Assets

- Mock task logs: `examples/skill_build_mock_logs.json`
- New built-in industrial skills:
  - `mini_agent/skills/geely-quality-rootcause-copilot/SKILL.md`
  - `mini_agent/skills/geely-equipment-anomaly-assistant/SKILL.md`
  - `mini_agent/skills/geely-ops-report-agent/SKILL.md`

## Notes

- Built-in skills can be enhanced online (stored as platform-enhanced overlays).
- Skill editing supports category bindings.
- Task category editor supports default selected skill bindings.
- New task form includes name, description, category, optional document, and multi-select skills.

