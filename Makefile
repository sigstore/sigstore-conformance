ALL_PY_SRCS := action.py \
	sigstore-python-conformance \
	$(shell find test/ -name '*.py') \
	$(shell find tools/ -name '*.py') \
	$(shell find .github/scripts/ -name '*.py')

.PHONY: all
all:
	@echo "Run my targets individually!"

env/bootstrap: dev-requirements.txt
	setup/create-venv.sh env
	. ./env/bin/activate && uv pip install --requirement dev-requirements.txt

selftest-env/pyvenv.cfg: selftest-requirements.txt
	setup/create-venv.sh selftest-env
	. ./selftest-env/bin/activate && uv pip install --requirement selftest-requirements.txt

env/pyvenv.cfg: env/bootstrap requirements.txt
	. ./env/bin/activate && uv pip install --requirement requirements.txt

.PHONY: dev
dev: env/pyvenv.cfg selftest-env/pyvenv.cfg

.PHONY: lint
lint: env/pyvenv.cfg $(ALL_PY_SRCS)
	./env/bin/python -m ruff format $(ALL_PY_SRCS)
	./env/bin/python -m ruff check --fix $(ALL_PY_SRCS)
	./env/bin/python -m mypy action.py test/

requirements.txt: requirements.in env/bootstrap
	. ./env/bin/activate && uv pip compile --custom-compile-command "make requirements.txt" --prerelease=allow --generate-hashes --output-file=$@ $<
