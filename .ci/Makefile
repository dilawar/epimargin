DOCKER:=$(shell which docker)

all : Dockerfile.ubuntu
	# Must run from top-directory else ADD won't work.
	cd .. && $(DOCKER) build -t epimargin/ubuntu .ci -f .ci/$<
