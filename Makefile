
PACKAGE_NAME := litprog

# This is the python version that is used for:
# - `make fmt`
# - `make ipy`
# - `make lint`
# - `make devtest`
DEVELOPMENT_PYTHON_VERSION := python=3.9

# These must be valid (space separated) conda package names.
# A separate conda environment will be created for each of these.
#
# Some valid options are:
# - python=2.7
# - python=3.5
# - python=3.6
# - python=3.7
# - python=3.8
# - pypy2.7
# - pypy3.5
# - pypy3.6
SUPPORTED_PYTHON_VERSIONS := python=3.9

include Makefile.bootstrapit.make

## -- Extra/Custom/Project Specific Tasks --

# TODO (mb 2018-11-15): Ammend installation to include
#	system deps (related to weasyprint) and to
#	download fonts and link them so weasyprint
#	can find them.


## Generate template.pdf from template.html
template.pdf: template.html
	 sed 's/&shy;//g' template.html > template_noshy.html;
	 $(DEV_ENV)/bin/weasyprint template_noshy.html template_tmp.pdf;
	 mv template_tmp.pdf template.pdf


##
../pycalver/README.html: ../pycalver/README.md *.css src/litprog/pdf_gen_scratch.py
	$(DEV_ENV)/bin/python src/litprog/pdf_gen_scratch.py html ../pycalver/README.md


##
../pycalver/README.pdf: ../pycalver/README.md *.css src/litprog/pdf_gen_scratch.py
	$(DEV_ENV)/bin/python src/litprog/pdf_gen_scratch.py pdf ../pycalver/README.md


##
../pycalver/README_booklet.pdf: ../pycalver/README.pdf
	$(DEV_ENV)/bin/python src/litprog/pdf_booklet_scratch.py ../pycalver/README.pdf
	# touch ../pycalver/README_booklet.pdf


## Regenerate file:///home/mbarkhau/workspace/pycalver/README.html
pycalver_docs: ../pycalver/README.html ../pycalver/README_booklet.pdf
	echo "noop"



## Generate Litprog Documentation
.PHONY: doc
doc:
	PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(DEV_ENV)/bin/lit \
			build -v lit_v3/*.md --html doc/
#	cp doc/*.html /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/
# 	rsync -r fonts/woff* /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/fonts/
#	cp src/litprog/static/*.css /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/
#	cp src/litprog/static/*.js /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/


svg2png := inkscape --without-gui --export-area-page --file


## Create favicon
logo/favicon.ico: logo/*.svg
	# $(svg2png) logo/favicon.svg --export-png logo/favicon_16.png -w 16 -h 16
	# $(svg2png) logo/favicon.svg --export-png logo/favicon_24.png -w 24 -h 24
	# $(svg2png) logo/favicon.svg --export-png logo/favicon_48.png -w 48 -h 48
	# $(svg2png) logo/favicon.svg --export-png logo/icon.png -w 128 -h 128
	# convert logo/favicon_16.png logo/favicon_24.png logo/favicon_48.png logo/favicon_old.ico

	$(svg2png) logo/logotype.svg --export-png logo/logotype_16.png -w 16 -h 16
	$(svg2png) logo/logotype.svg --export-png logo/logotype_24.png -w 24 -h 24
	$(svg2png) logo/logotype.svg --export-png logo/logotype_48.png -w 48 -h 48
	$(svg2png) logo/logotype.svg --export-png logo/logotype.png -w 256 -h 256
	convert logo/logotype_16.png logo/logotype_24.png logo/logotype_48.png logo/favicon.ico


KATEX_CDN_BASE_URL=https://cdn.jsdelivr.net/npm/katex@0.10.2/dist


## Download css and fonts so font files are not from google
.PHONY: download_fonts_static
download_fonts_static:
	# TODO:
	# download stylesheets
	# download fonts from urls in stylesheets
	# ua IE: Mozilla/5.0 (compatible; MSIE 9.0; InfoChannel RNSafeBrowser/v.1.1.0G)


## Download css and fonts so pdf generation doesn't have to
## repeatedly request from the CDN.
.PHONY: download_katex_static
download_katex_static:
	curl $(KATEX_CDN_BASE_URL)/katex.css \
		-s -o fonts/katex.css;
	grep -Po "(?<=url\().*?\.(woff2|woff|ttf)" fonts/katex.css \
		| sort | uniq > fonts/katex_fontfile_urls.txt
	mkdir -p katex_static/fonts/;
	for path in $$(cat fonts/katex_fontfile_urls.txt); do \
		curl "$(KATEX_CDN_BASE_URL)/$${path}" -s -o katex_static/$${path}; \
		echo "downloaded katex_static/$${path}"; \
	done

## Copy sketch files to kbfs to test on mobile
.PHONY: deploy_sketch
deploy_sketch:
	cp sketch.html /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/;
	cp src/litprog/static/*.js /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/src/litprog/static/;
	cp src/litprog/static/*.css /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/src/litprog/static/;
	cp src/litprog/static/*.svg /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/src/litprog/static/;


## build ../sbk/READMEv2.md -> doc/
.PHONY: sbk
sbk:
	$(DEV_ENV)/bin/lit build -v ../sbk/READMEv2.md --html doc
	$(DEV_ENV)/bin/lit build -v ../sbk/READMEv2.md --pdf doc


## upload static doc/ to keybase
.PHONY: sync
sync:
	rsync -rtpov --exclude='*.woff' --exclude='*.woff2' --exclude='*.ttf' \
		--exclude='*.pdf' --exclude='print*.html' \
		doc/ /run/user/1000/keybase/kbfs/public/mbarkhau/sbk/
