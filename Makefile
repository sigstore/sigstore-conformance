ALL_PY_SRCS := sigstore-conformance $(shell find test -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

env/pyvenv.cfg: requirements.txt dev-requirements.txt
	python3 -m venv env
	./env/bin/python -m pip install --upgrade pip
	./env/bin/python -m pip install --requirement requirements.txt --requirement dev-requirements.txt

.PHONY: dev
dev: env/pyvenv.cfg

.PHONY: lint
lint: env/pyvenv.cfg $(ALL_PY_SRCS)
	./env/bin/python -m black $(ALL_PY_SRCS)
	./env/bin/python -m isort $(ALL_PY_SRCS)
	./env/bin/python -m flake8 --max-line-length 100 $(ALL_PY_SRCS)
