
.PHONY: test
test:
	pytest test/unit


.PHONY: test-smoke
test-smoke:
	pytest test/smoke

.PHONY: test-all
test-all:
	pytest test

.PHONY: lint
lint:
	pycodestyle mplayer

.PHONY: format
format:
	black .
