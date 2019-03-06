
# TODO (mb 2018-11-15): Ammend installation to include
#	system deps (related to weasyprint) and to
#	download fonts and link them so weasyprint
#	can find them.

## Generate template.pdf from template.html
template.pdf: template.html
	 sed 's/&shy;//g' template.html > template_noshy.html;
	 $(DEV_ENV)/bin/weasyprint template_noshy.html template_tmp.pdf;
	 mv template_tmp.pdf template.pdf


## Generate pycalver/README.html
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
pycalver_readme: ../pycalver/README.html ../pycalver/README_booklet.pdf
	echo "noop"


## MVP
.PHONY: src/litprog/tmp__main__.py
src/litprog/tmp__main__.py: lit/000_mvp.md src/litprog/__main__.py
	touch src/litprog/tmp__main__.py
	$(DEV_ENV)/bin/litprog build lit/000_mvp.md
	$(DEV_ENV)/bin/sjfmt src/litprog/tmp*.py

