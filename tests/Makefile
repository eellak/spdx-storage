# Makefile (for GNU make) to run tests for spdx-storage
# 
# Copyright (C) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

VERSION := $(shell $(MAKE) --version)
ifneq ($(firstword $(VERSION)),GNU)
$(error This Makefile might not work without GNU Make)
endif
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
empty :=

IMPORT_CMD = spdx-storage import
IMPORT_CMD = echo Importing file

EX = spdx-examples
VIZ = spdx-viz

# Example SBOMs from the SPDX examples repo.  These are rather small.
EXFILES = \
	$(EX)/ai/example01/spdx3.0/simplehtr-example.spdx3.json \
	$(EX)/ai/example02/spdx3.0/sbom.spdx3.json \
	$(EX)/dataset/example01/spdx3.0/example01.spdx3.json \
	$(EX)/software/example10/spdx3.0/hello-source.spdx3.json \
	$(EX)/software/example11/spdx3.0/sbom.spdx3.json \
	$(EX)/software/example12/spdx3.0/hello-dist.spdx3.json \
	$(EX)/software/example12/spdx3.0/hello-src.spdx3.json \
	$(EX)/software/example13/spdx3.0/example13.spdx3.json \
	$(EX)/software/example14/content/examplemaven-0.0.1.spdx3.json \
	$(EX)/software/example14/spdx3.0/examplemaven-0.0.1-enriched.spdx3.json \
	$(EX)/software/example1/spdx3.0/example1.spdx3.json \
	$(EX)/software/example3/spdx3.0/example3-bin.spdx3.json \
	$(EX)/software/example3/spdx3.0/example3-src.spdx3.json \
	$(EX)/software/example4/spdx3.0/example4-bin.spdx3.json \
	$(EX)/software/example4/spdx3.0/example4-src.spdx3.json \
	$(EX)/software/example5/spdx3.0/example5-bin.spdx3.json \
	$(EX)/software/example5/spdx3.0/example5-src.spdx3.json \
	$(EX)/software/example6/spdx3.0/example6-bin.spdx3.json \
	$(EX)/software/example6/spdx3.0/example6-lib.spdx3.json \
	$(EX)/software/example6/spdx3.0/example6-src.spdx3.json \
	$(EX)/software/example7/spdx3.0/example7-bin.spdx3.json \
	$(EX)/software/example7/spdx3.0/example7-golang.spdx3.json \
	$(EX)/software/example7/spdx3.0/example7-go-module.spdx3.json \
	$(EX)/software/example7/spdx3.0/example7-third-party-modules.spdx3.json \
	$(EX)/software/example8/spdx3.0/examplemaven-0.0.1.spdx3.json \
	$(EX)/software/example9/spdx3.0/appbomination.spdx3.json \
	$(empty)

# Large SBOMs from the SPDX visualizer repo.  These are mostly large, real-world examples.
LGFILES = \
	$(VIZ)/public/samples/ai/simplehtr-example.spdx3.json \
	$(VIZ)/public/samples/android/aosp-android-latest-release.jsonld \
	$(VIZ)/public/samples/ansible/ansible-automation-platform-2.6.spdx3.jsonld \
	$(VIZ)/public/samples/ansible/ansible-automation-platform-2.6-vex.spdx3.jsonld \
	$(VIZ)/public/samples/basil/spdx.jsonld \
	$(VIZ)/public/samples/docker/ubuntu-24.04-linux-amd64.spdx3.jsonld \
	$(VIZ)/public/samples/functional-safety/aeb-safety-case.spdx3.jsonld \
	$(VIZ)/public/samples/jenkins/org.jenkins-ci.main_jenkins-parent-2.572-SNAPSHOT.spdx3.json-ld.json \
	$(VIZ)/public/samples/kubernetes/kubernetes_1_35_3_spdx.jsonld \
	$(VIZ)/public/samples/linux/sbom-build.spdx.json \
	$(VIZ)/public/samples/linux/sbom-output.spdx.json \
	$(VIZ)/public/samples/linux/sbom-source.spdx.json \
	$(VIZ)/public/samples/paper-plane/paper-plane-supply-chain.spdx3.jsonld \
	$(VIZ)/public/samples/samples.json \
	$(VIZ)/public/samples/supply-chain/arborlink-sg1-supply-chain.spdx3.jsonld \
	$(VIZ)/public/samples/trivy/trivy-ubuntu-26-bom.spdx3.json \
	$(VIZ)/public/samples/vuejs/vuej-demo-sbom.spdx3.jsonld \
	$(VIZ)/public/samples/windows/windows-11.spdx3.json \
	$(VIZ)/public/samples/yocto6/core-image-minimal-qemux86-64.rootfs-20260713122608.spdx.json \
	$(VIZ)/public/samples/yocto/core-image-minimal-1-0-0-0-20260321-1540.spdx.json \
	$(VIZ)/public/samples/zephyr/app.jsonld \
	$(VIZ)/public/samples/zephyr/build.jsonld \
	$(VIZ)/public/samples/zephyr-experimental/app.jsonld \
	$(VIZ)/public/samples/zephyr-experimental/build.jsonld \
	$(VIZ)/public/samples/zephyr-experimental/modules-deps.jsonld \
	$(VIZ)/public/samples/zephyr-experimental/safety.jsonld \
	$(VIZ)/public/samples/zephyr-experimental/sdk.jsonld \
	$(VIZ)/public/samples/zephyr-experimental/zephyr.jsonld \
	$(VIZ)/public/samples/zephyr/modules-deps.jsonld \
	$(VIZ)/public/samples/zephyr/zephyr.jsonld \
	$(empty)

# external programs
GIT := git

all: input-files

# tests to run

import-all: import-ex import-lg

import-ex: $(EXFILES)
	for f in $^; do $(IMPORT_CMD) $$f; done

import-lg: $(LGFILES)
	for f in $^; do $(IMPORT_CMD) $$f; done

import-one-small: $(EXFILES)
	@RANDOM_FILE=$$(echo "$^" | tr ' ' '\n' | shuf -n 1); \
	echo "Importing at random small SBOM $$RANDOM_FILE";
	$(IMPORT_CMD) $$RANDOM_FILE

import-one-large: $(LGFILES)
	@RANDOM_FILE=$$(echo "$^" | tr ' ' '\n' | shuf -n 1); \
	echo "Importing at random large SBOM $$RANDOM_FILE"; \
	$(IMPORT_CMD) $$RANDOM_FILE

# cleaning up

clean:
	$(RM) -r $(EX)

clobber: clean
	$(RM) $(WORDFILE)


# the input data (SPDX SBOM files)

input-files: $(EX) $(VIZ)

$(EX):
	$(GIT) clone --depth 1 https://github.com/spdx/spdx-examples.git $(EX)

$(VIZ):
	$(GIT) clone --depth 1 https://github.com/kartben/spdx3_viz.git $(VIZ)

update: $(EX) $(VIZ)
	$(GIT) -C $(EX) pull
	$(GIT) -C $(VIZ) pull


.PHONY: all
.PHONY: clean
.PHONY: clobber
.PHONY: import-all
.PHONY: import-ex
.PHONY: import-lg
.PHONY: input-files
.PHONY: update

