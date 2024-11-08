.PHONY: all run-fe run-launcher

all: run-fe run-launcher

run-fe:
	@echo "running field image gen server..."
	gnome-terminal -- bash -c "cd cogs/pokemonduel && ./FE; exec bash"


run-launcher:
	@echo "running bot..."
	gnome-terminal -- bash -c "python3 launcher.py; exec bash"



