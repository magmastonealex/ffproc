## Automate local deployment from a checkout


# OS-specific support
PYTHON_BIN_DIR = bin
ifeq ($(OS),Windows_NT)
PYTHON_BIN_DIR = Scripts
PYTHON_EXT = .exe
endif


## Top-level targets

.PHONY: default
default: .venv
	.venv/$(PYTHON_BIN_DIR)/python$(PYTHON_EXT) ffproc.py -h


## Real targets

.venv:
	virtualenv "$(@)"
