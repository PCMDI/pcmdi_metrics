.PHONY: conda-info conda-list setup-build setup-tests conda-rerender \
	conda-build conda-upload conda-dump-env \
	run-tests run-coveralls

SHELL = /bin/bash

os = $(shell uname)
pkg_name = pcmdi_metrics
organization = pcmdi

#
# user and label for upload
#
user = pcmdi
label ?= nightly
build_script = conda-recipes/build_tools/conda_build.py

test_pkgs = testsrunner scipy cia coverage coveralls
ifeq ($(os),Linux)
pkgs = "mesalib=18.3.1"
else
pkgs = "mesalib=17.3.9"
endif

last_stable ?= 1.2

conda_build_env=build-$(pkg_name)
conda_test_env=test-$(pkg_name)

branch ?= $(shell git rev-parse --abbrev-ref HEAD)
extra_channels ?= pcmdi/label/nightly pcmdi cdat/label/nightly conda-forge
conda ?= $(or $(CONDA_EXE),$(shell find /opt/*conda*/bin $(HOME)/*conda*/bin -type f -iname conda))
conda_env_filename ?= spec-file

ifeq ($(workdir),)
ifeq ($(wildcard $(PWD)/.tempdir),)
workdir = $(shell mktemp -d -t "build_$(pkg_name).XXXXXXXX")
$(shell echo $(workdir) > $(PWD)/.tempdir)
endif

workdir := $(shell cat $(PWD)/.tempdir)
endif

$(info $(workdir))

artifact_dir ?= $(PWD)/artifacts

ifeq ($(coverage),1)
coverage_opt = -c tests/coverage.json --coverage-from-egg
endif

conda_recipes_branch ?= master

conda_base = $(patsubst %/bin/conda,%,$(conda))
conda_activate = $(conda_base)/bin/activate

conda_build_extra = --copy_conda_package $(artifact_dir)/

ifndef $(local_repo)
local_repo = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
endif

conda-info:
	source $(conda_activate) $(conda_test_env); conda info

conda-list:
	source $(conda_activate) $(conda_test_env); conda list

setup-build:
ifeq ($(wildcard $(workdir)/conda-recipes),)
	git clone -b $(conda_recipes_branch) https://github.com/CDAT/conda-recipes $(workdir)/conda-recipes
else
	cd $(workdir)/conda-recipes; git pull
endif

clean:
	rm -rf $(shell cat .tempdir)

	rm -f .tempdir

setup-tests:
	source $(conda_activate) base; conda create -y -n $(conda_test_env)  \
		$(or $(if $(findstring $(conda_build_env),base),—use-local,),-c file://$(conda_base)/envs/$(conda_build_env)/conda-bld) \
		$(foreach x,$(extra_channels),-c $(x)) $(pkg_name) $(foreach x,$(test_pkgs),"$(x)") \
		$(foreach x,$(extra_pkgs),"$(x)") $(foreach x,$(pkgs),"$(x)")

conda-rerender: setup-build 
	python $(workdir)/$(build_script) -w $(workdir) -l $(last_stable) -B 0 -p $(pkg_name) \
		-b $(branch) --do_rerender --conda_env $(conda_build_env) --ignore_conda_missmatch \
		--conda_activate $(conda_activate) --organization $(organization)

conda-local-rerender: setup-build 
	python $(workdir)/$(build_script) -w $(workdir) -l $(last_stable) -B 0 -p $(pkg_name) \
		-b $(branch) --do_rerender --conda_env $(conda_build_env) --ignore_conda_missmatch \
		--conda_activate $(conda_activate) --organization $(organization) --local_repo=$(local_repo)

conda-build:
	mkdir -p $(artifact_dir)

	python $(workdir)/$(build_script) -w $(workdir) -p $(pkg_name) --build_version noarch \
		--do_build --conda_env $(conda_build_env) --extra_channels $(extra_channels) \
		--conda_activate $(conda_activate) $(conda_build_extra)

conda-local-build:
	mkdir -p $(artifact_dir)

	python $(workdir)/$(build_script) -w $(workdir) -p $(pkg_name) --build_version noarch \
		--do_build --conda_env $(conda_build_env) --extra_channels $(extra_channels) \
		--conda_activate $(conda_activate) $(conda_build_extra) --local_repo=$(local_repo)

conda-upload:
	source $(conda_activate) $(conda_build_env); \
		anaconda -t $(conda_upload_token) upload -u $(user) -l $(label) --force $(artifact_dir)/*.tar.bz2

conda-dump-env:
	mkdir -p $(artifact_dir)

	source $(conda_activate) $(conda_test_env); conda list --explicit > $(artifact_dir)/$(conda_env_filename).txt

run-tests:
	source $(conda_activate) $(conda_test_env); python run_tests.py -H -v2 $(coverage_opt)

run-coveralls:
	source $(conda_activate) $(conda_test_env); coveralls;
