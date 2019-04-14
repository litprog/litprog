
### Build a Map for your Reader

Different readers care about different things and it should be as easy as possible for each find what they are looking for without having to read through prose or code that is not relevant to them. End users should be able to find the tutorial and examples, maintainers should be able to find specific modules, developers.


### Chapter Ordering

Parsing of the markdown files is done in lexical order of their
filenames. A more flexible alternative would be to explicitly
declare the ordering in some form of metadata, but since authors
will be working with these files using their normal editors and
file system browsers a pragmatic choice is to use a simple fixed
width prefix, which we will refer to simply as the *chapter
prefix*.


### File Naming

With a non literate program the order of files is usually not so important. The compiler or interpreter can figure out how to process the the files and in which order based on include/import declarations and the developer doesn't have to pay much attention. For a Literate Program this is of course different. To establish a narrative, some things should come before others.

LitProg processes markdown files in lexicographical/alphabetical order, so you can add a prefix to your files that enforce a certain ordering. 


```
.--- Part           #   h1. Header
|.-- Chapter        ##  h2. Header
||
10_overview.md
11_introduction.md
12_motivation.md

20_user_documentation.md
21_public_api.md
22_example_usage.md

30_implementation.md
31_code_style.md
32_types_and_datastructures.md

40_porcelain.md
41_config.md
42_cli.md

50_core.md
51_parse.md
52_build.md
53_session.md
54_metaprogramming.md

60_docgen.md
61_md2html.md
62_html_postproc.md
63_html2pdf.md
64_pdf_join.md

70_plugins.md
71_spellcheck.md
72_readability.md
73_python_fmt.md
```

