install:
	@echo ">>> Installing dependencies"
	pip install --upgrade pip && pip install -r requirements.txt

format:
	@echo ">>> Formatting files using isort and Black"
	isort .
	black .

lint:
	@echo ">>> Linting Python files"
	ruff check .

lint-container:
	@echo ">>> Linting Dockerfile(s)"
	docker run --rm -i hadolint/hadolint < Dockerfile

refactor:
	format lint lint-container

coverage:
	@echo ">>> Displaying pytest coverage report"
	pytest --cov=./ tests/

test:
	@echo ">>> Running unit tests within existing environment"
	python -m pytest -vv

scrape:
	@echo ">>> Scraping data from LZV Cup"
	python ./scraper/main.py

push:
	@echo ">>> Stage, commit, and pushing to GitHub"
	git add .
	git commit -m "$(message)" --no-verify
	git push

debug:
	@echo ">>> Debugging Python script"
	python -m pdb -c continue $(script)

app:
	@echo ">>> Running Streamlit app"
	streamlit run ./webapp/01_Home.py