.PHONY: all run-fe run-launcher stopfe

all: run-fe run-launcher

run-fe:
	cd cogs/pokemonduel && nohup ./FE > fe.log 2>&1 &

run-launcher:
	python3 launcher.py

stopfe:
	pkill FE 
