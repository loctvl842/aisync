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
	@printf "\033[35m$(APP_NAME)\033[0m\n"
	@printf "\033[33mAPP_VERSION: \033[0m"
	@printf "\033[35m$(APP_VERSION)\033[0m\n"
	@printf "\n"

.PHONY: usage
usage:
	@printf "\033[034mUsage\033[0m\n"
	@printf "\033[34m---------------------------------------------------------------\033[0m\n"
	@printf "\033[37mmake [options] \033[0m\n\n"

.PHONY: options
options:
	@printf "\033[34mOptions\033[0m\n"
	@printf "\033[34m---------------------------------------------------------------\033[0m\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' | sort


### API

.PHONY: api
api:  ## Run a command in packages/api/Makefile (Usage: make api <command>)
	@$(MAKE) --no-print-directory -C packages/api $(filter-out $@, $(MAKECMDGOALS))

.PHONY: core
core:  ## Run a command in packages/core/Makefile (Usage: make core <command>)
	@$(MAKE) --no-print-directory -C packages/core $(filter-out $@, $(MAKECMDGOALS))

%:
	@:
