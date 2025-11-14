VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
GUNICORN := $(VENV)/bin/gunicorn

.PHONY: help install run serve clean

help:
	@echo "Comandos disponibles:"
	@echo "  make install  - crea el entorno virtual e instala dependencias"
	@echo "  make run      - ejecuta la app en modo desarrollo (python app.py)"
	@echo "  make serve    - despliega con gunicorn (app:app.server)"
	@echo "  make clean    - elimina el entorno virtual .venv"

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run: install
	$(PYTHON) app.py

serve: install
	$(GUNICORN) app:server

clean:
	rm -rf $(VENV)
