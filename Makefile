.PHONY: up down services infrastructure uvicorn taskiq react react-install logs stop

# Source .env inline for each Django command (avoids xargs parsing issues)
DOTENV := set -a && . ./.env && set +a

# Start everything with one command
up: infrastructure services

# Stop everything
down:
	@echo "Stopping application services..."
	-@pkill -f "uvicorn config.asgi:application" 2>/dev/null || true
	-@pkill -f "taskiq worker" 2>/dev/null || true
	-@pkill -f "vite.*ai-meditation-starter-kit-react" 2>/dev/null || true
	@echo "Stopping Docker infrastructure..."
	cd web && docker compose down

# Infrastructure (Redis, Postgres, Nginx)
infrastructure:
	@echo "Starting Docker infrastructure (Redis, Postgres, Nginx)..."
	cd web && docker compose up -d

# All application services in background
services: uvicorn taskiq react
	@echo ""
	@echo "All services started:"
	@echo "  Django (Uvicorn):  http://localhost:8001"
	@echo "  TaskIQ worker:    running"
	@echo "  React (Vite):     http://localhost:5173"
	@echo "  Nginx proxy:      http://localhost:80"
	@echo ""
	@echo "Logs: make logs"
	@echo "Stop: make down"

# Django Uvicorn server
uvicorn:
	@echo "Starting Django Uvicorn..."
	@mkdir -p .logs
	cd web && $(DOTENV) && ./venv/bin/python -m uvicorn config.asgi:application --host 0.0.0.0 --port 8001 --reload > ../.logs/uvicorn.log 2>&1 &

# TaskIQ worker
taskiq:
	@echo "Starting TaskIQ worker..."
	@mkdir -p .logs
	cd web && $(DOTENV) && ./venv/bin/python -m taskiq worker --log-level=INFO --reload config.taskiq_config:broker config.taskiq_tasks > ../.logs/taskiq.log 2>&1 &

# React dev server (install deps if needed)
react: react-install
	@echo "Starting React dev server..."
	@mkdir -p .logs
	cd ai-meditation-starter-kit-react && npx vite --host > ../.logs/react.log 2>&1 &

react-install:
	@if [ ! -d ai-meditation-starter-kit-react/node_modules ]; then \
		echo "Installing React dependencies..."; \
		cd ai-meditation-starter-kit-react && npm install; \
	fi

# Tail all logs
logs:
	tail -f .logs/uvicorn.log .logs/taskiq.log .logs/react.log

# Django management shortcuts
migrate:
	cd web && $(DOTENV) && ./venv/bin/python manage.py migrate

makemigrations:
	cd web && $(DOTENV) && ./venv/bin/python manage.py makemigrations

shell:
	cd web && $(DOTENV) && ./venv/bin/python manage.py shell

dbshell:
	cd web && $(DOTENV) && ./venv/bin/python manage.py dbshell

collectstatic:
	cd web && $(DOTENV) && ./venv/bin/python manage.py collectstatic --noinput
