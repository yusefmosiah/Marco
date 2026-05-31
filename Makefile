PYTHON ?= .venv/bin/python
EMF ?= .venv/bin/emf-macro

.PHONY: setup test web-build ci agent-context serve-agent-api deploy-node-a clean

setup:
	@tools/bootstrap.sh

test:
	@$(PYTHON) -m pytest -q

web-build:
	@cd apps/web && npm run build

ci: test web-build

agent-context:
	@$(EMF) agent-context --root . --run-id latest

serve-agent-api:
	@$(EMF) serve-agent-api --root . --host 127.0.0.1 --port 8765 --public-base-url https://choir-ip.com/marco

deploy-node-a:
	@tools/deploy_node_a_static.sh

clean:
	@rm -rf apps/web/dist .pytest_cache
