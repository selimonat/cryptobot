setup: setup.pip setup.poetry

setup.pip:
	pip install --upgrade pip
	pip install "poetry==1.1.11"

setup.poetry:
	poetry config virtualenvs.create true
	poetry config virtualenvs.in-project true
	poetry install --no-interaction --no-ansi
