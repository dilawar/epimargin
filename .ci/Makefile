DOCKER:=$(shell which docker)

all : .ci/Dockerfile.debian
	# Must run from top-directory else ADD won't work.
	$(DOCKER) build -t epimargin/ubuntu . -f $<
