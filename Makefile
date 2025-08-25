.PHONY: build up down test

# Build Docker image
build:
	docker compose build

# Build and start services
up: build
	docker compose up

# Stop and remove containers
down:
	docker compose down

# Run tests locally
test: requirements
	pytest -q

# Install requirements (dependency for test target)
requirements:
	pip install -r requirements.txt