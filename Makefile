lint:
	isort downloader/
	.venv/bin/pylint downloader/

typecheck:
	.venv/bin/mypy downloader/

check: lint typecheck
