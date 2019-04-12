## File Reorganization

Adding a new part or chapter can lead to a cascade of renamed files. Imagine you have a chapter that you want to split in two, in this case the chapter `xx_core.md` into `xx_build.md` and `xx_parse.md`.

```
  51_core.md
+ 5x_build.md
+ 5x_parse.md
  52_plugins.md
  53_md2html.md
```

To keep the desired ordering, we would have to also rename the files `52_plugins.md` and `53_md2html.md`, even though nothing about them changed.

We can avoid this by providing metadata in each file which delcares the relative position of each file within the project. This way you only have to update the metadata of one or two parts/chapters and use the `litprog reorder` command.


