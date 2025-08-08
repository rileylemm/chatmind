SHELL := /bin/bash

.PHONY: up down clean pipeline sample api frontend docs lint fmt test

up:
	docker compose up -d
	sleep 5

down:
	docker compose down

clean:
	rm -rf data/processed/*

pipeline:
	python3 chatmind/pipeline/run_pipeline.py --local

sample:
	python3 scripts/generate_sample_data.py

api:
	cd chatmind/api && python run.py

frontend:
	cd chatmind/frontend && npm install && npm run dev

lint:
	ruff check chatmind || true
	npx --yes eslint chatmind/frontend || true

fmt:
	ruff format chatmind || true
	npx --yes prettier -w chatmind/frontend || true

docs:
	mkdocs serve

e2e:
	python3 scripts/test_api_endpoints.py
	python3 scripts/test_db_query.py 