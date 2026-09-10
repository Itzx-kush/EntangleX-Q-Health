PYTHON ?= python3
.PHONY: test backend frontend
backend:
	cd backend && uvicorn app.main:app --reload --port 8000
frontend:
	cd frontend && npm run dev
test:
	cd backend && PYTHONPATH=. $(PYTHON) -m unittest discover -s tests -v
	cd frontend && npm test
