APP_NAME := `sed -n 's/^ *name.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`
APP_VERSION := `sed -n 's/^ *version.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`

# Makefile help

.PHONY: help
help: header usage options ## Print help

.PHONY: header
header:
	@printf "\033[34mEnvironment\033[0m\n"
	@printf "\033[34m---------------------------------------------------------------\033[0m\n"
	@printf "\033[33mAPP_NAME: \033[0m"
	@printf "\033[35m$(APP_NAME)\033[0m"
	@printf "\n"
	@printf "\033[33mAPP_VERSION: \033[0m"
	@printf "\033[35m$(APP_VERSION)\033[0m\n"
	@printf "\n"

.PHONY: usage
usage:
	@printf "\033[034mUsage\033[0m"
	@printf "\n"
	@printf "\033[34m---------------------------------------------------------------\033[0m"
	@printf "\n"
	@printf "\033[37mmake [options] \033[0m"
	@printf "\n\n"

.PHONY: options
options:
	@printf "\033[34mOptions\033[0m"
	@printf "\n"
	@printf "\033[34m---------------------------------------------------------------\033[0m"
	@printf "\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' | sort


### Development

.PHONY: start
start: ## Start the server
	FASTAPI_ENV=development uv run python -m aisync_api.main


### Code quality

.PHONY: fix-lint
lint-fix: ## Auto-fix linting issues where possible
	uv run ruff check --fix .

.PHONE: format
format: ## Format the code
	uv run ruff format .

.PHONY: lint
lint: ## Check code for style and error issues
	uv run ruff check .


### Database

.PHONY: migrate
migrate: ## Run the migrations
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	uv run alembic upgrade head

.PHONY: rollback
rollback: ## Rollback the migrations
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	uv run alembic downgrade -1

.PHONY: generate-migration
generate-migration: ## Generate a new migration
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	@echo -ne "\033[33mEnter migration message: \033[0m"
	@read -r message; \
	uv run alembic revision --autogenerate -m "$$message"
