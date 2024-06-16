
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
	pyright mplayer

.PHONY: format
format:
	black .

.PHONY: wheel
wheel:
	python -m build

.PHONY: clean
clean:
	rm -rf dist
