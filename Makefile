makemigrations: ## Create alembic migration
	$(PYTHON) -m alembic revision --autogenerate -m "$(msg)"

migrate:  ## Apply latest alembic migrations
	$(PYTHON) -m alembic upgrade head

unmigrate:  ## Discard latest alembic migration
	$(PYTHON) -m alembic downgrade -1
