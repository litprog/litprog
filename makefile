
PACKAGE_NAME := litprog

# This is the python version that is used for:
# - `make fmt`
# - `make ipy`
# - `make lint`
# - `make devtest`
DEVELOPMENT_PYTHON_VERSION := python=3.8

# These must be valid (space separated) conda package names.
# A separate conda environment will be created for each of these.
#
# Some valid options are:
# - python=2.7
# - python=3.5
# - python=3.6
# - python=3.7
# - pypy2.7
# - pypy3.5
SUPPORTED_PYTHON_VERSIONS := python=3.8 python=2.7


include makefile.bootstrapit.make

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


## MVP
.PHONY: src/litprog/tmp__main__.py
src/litprog/tmp__main__.py: lit/000_mvp.md src/litprog/__main__.py
	touch src/litprog/tmp__main__.py
	$(DEV_ENV)/bin/litprog build lit/000_mvp.md
	$(DEV_ENV)/bin/sjfmt src/litprog/tmp*.py


lit_out/out.html.tmp.html: lit/*.md
	$(DEV_ENV)/bin/litprog build lit/000_mvp.md lit/005c_html_postproc_v2.md
	$(DEV_ENV)/bin/python src/litprog/html_postproc_v2.py lit_out/out.html


src/litprog/__main__.py: lit/*.md
	ENABLE_BACKTRACE=0 $(DEV_ENV)/bin/litprog build -v lit/*.md


## Generate Litprog Documentation
.PHONY: it
it:
	$(DEV_ENV)/bin/litprog build -v lit_v3/11_overview.md --html doc/
#	cp doc/*.html /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/
# 	rsync -r fonts/woff* /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/fonts/
	cp src/litprog/static/*.css /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/
	cp src/litprog/static/*.js /run/user/1000/keybase/kbfs/public/mbarkhau/litprog/


## Create favicon
favicon.ico: *.png
	inkscape -z -e favicon_16.png -w 16 -h 16 favicon.svg
	inkscape -z -e favicon_24.png -w 24 -h 24 favicon.svg
	inkscape -z -e favicon_48.png -w 48 -h 48 favicon.svg
	inkscape -z -e icon.png -w 128 -h 128 favicon.svg
	inkscape -z -e icon.png -w 128 -h 128 logotype.svg
	convert favicon_16.png favicon_24.png favicon_48.png favicon_old.ico
	convert logotype_16.png logotype_24.png logotype_48.png favicon.ico


KATEX_CDN_BASE_URL=https://cdn.jsdelivr.net/npm/katex@0.10.2/dist


## Download css and fonts so pdf generation doesn't have to
## repeatedly request from the CDN.
.PHONY: katex_static
katex_static:
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


.PHONY: sbk
sbk:
	$(DEV_ENV)/bin/litprog build -v ../sbk/READMEv2.md --html doc
# 	$(DEV_ENV)/bin/litprog build -v ../sbk/READMEv2.md --pdf doc

.PHONY: sync
sync:
	rsync -rtpov --exclude='*.woff' --exclude='*.woff2' --exclude='*.ttf' \
		--exclude='*.pdf' --exclude='print*.html' \
		doc/ /run/user/1000/keybase/kbfs/public/mbarkhau/sbk/