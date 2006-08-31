# Makefile for CodeCollaborator for UCM
# Miki Tebeka <mtebeka@qualcomm.com>

# Copyright (c) 2006 by QUALCOMM INCORPORATED  All Rights Reserved.

PYTHON = $(shell pyexe.py)
INNO = $(shell innoexe.py)
SRC = ucmcc.py \
	  ucmcc_baseline.py \
	  ucmcc.ico \
	  common.py \
	  setup.py
UTIL = README.txt \
	   Makefile \
	   ChangeLog \
	   version.iss.in \
	   LICENSE.txt \
	   VERSION \
	   publish \
	   pyexe.py \
	   innoexe.py \
	   style.css \
	   setup.iss

TEST = $(wildcard test/*.py)
VERSION = $(shell cat VERSION)
ZIP_DIR = ucmcc_$(VERSION)

all: dist

dist: $(SRC) README.html ChangeLog version.py
	$(PYTHON) setup.py py2exe
	cp -f ucmcc.ico $@
	cp -f README.html dist
	cp -f ChangeLog dist
	cp -f LICENSE.txt dist
	cp -f default.css dist

version.py: VERSION
	echo 'VERSION = "$(VERSION)"' > $@

installer: dist setup.iss
	$(INNO) setup.iss

setup.iss: version.iss

version.iss: version.iss.in VERSION
	sed -e "s/_VERSION_/$(VERSION)/" $< > $@

# FIXME: Find a solution for windows
README.html: README.txt style.css VERSION
	sed -e "s/_VERSION_/$(VERSION)/" $< | rst2html.py --stylesheet=style.css \
   		- $@

zip:
	rm -fr $(ZIP_DIR)
	mkdir $(ZIP_DIR)
	cp -r $(SRC) $(ZIP_DIR)
	cp -r $(UTIL) $(ZIP_DIR)
	cp -r $(TEST) $(ZIP_DIR)
	zip -r9 ucmcc_src_$(VERSION).zip $(ZIP_DIR)
	rm -fr $(ZIP_DIR)

clean:
	rm -fr dist build
	rm -f *.pyc
	rm -f *.exe *.zip
	rm -f version.iss version.py
	rm -f README.html

fresh: clean all

.PHONY: all clean fresh
