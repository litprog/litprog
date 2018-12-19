
# TODO (mb 2018-11-15): Ammend installation to include
#	system deps (related to weasyprint) and to
#	download fonts and link them so weasyprint
#	can find them.

## Generate template.pdf from template.html
template.pdf: template.html
	 sed 's/&shy;//g' template.html > template_noshy.html;
	 $(DEV_ENV)/bin/weasyprint template_noshy.html template_tmp.pdf;
	 mv template_tmp.pdf template.pdf

