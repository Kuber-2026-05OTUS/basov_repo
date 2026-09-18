.PHONY: install lint typecheck test security yamllint helm-lint validate

install:
	pip install -r requirements-dev.txt

lint:
	ruff check .

typecheck:
	mypy src streamlit_app

test:
	pytest tests/unit tests/integration -v

security:
	bandit -r src streamlit_app dags
	pip-audit -r requirements.txt

yamllint:
	yamllint -c .yamllint.yaml k8s airflow monitoring

helm-lint:
	helm repo add apache-airflow https://airflow.apache.org
	helm lint apache-airflow/airflow -f airflow/values.yaml -f airflow/values-dev.yaml

validate: lint typecheck test security yamllint
	@echo "All local validations passed."
