ALL_PY_SRCS := action.py \
	sigstore-python-conformance \
	$(shell find test/ -name '*.py') \
	$(shell find tools/ -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

env/bootstrap: dev-requirements.txt
	python3 -m venv env
	./env/bin/python -m pip install --upgrade pip
	./env/bin/python -m pip install --requirement dev-requirements.txt
	touch env/bootstrap

selftest-env/pyvenv.cfg: selftest-requirements.txt
	python3 -m venv selftest-env
	./selftest-env/bin/python -m pip install --upgrade pip
	./selftest-env/bin/python -m pip install --requirement selftest-requirements.txt


env/pyvenv.cfg: env/bootstrap requirements.txt
	./env/bin/python -m pip install --requirement requirements.txt

.PHONY: dev
dev: env/pyvenv.cfg selftest-env/pyvenv.cfg

.PHONY: lint
lint: env/pyvenv.cfg $(ALL_PY_SRCS)
	./env/bin/python -m ruff format $(ALL_PY_SRCS)
	./env/bin/python -m ruff check --fix $(ALL_PY_SRCS)
	./env/bin/python -m mypy action.py test/

requirements.txt: requirements.in env/bootstrap
	./env/bin/pip-compile --generate-hashes --output-file=$@ $<
