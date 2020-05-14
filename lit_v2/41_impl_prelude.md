
# Implementation of LitProg

LitProg is a self-hosting compiler written in pure python. The compiler source code is written to `src/` from the literate source in `lit/`. During development, a previous and known-good version of the compiler is used.

## manifest

The literate source is ordered according to the following manifest. Using the `litprog sync-manifest` sub-command makes it easy to add new chapters and have the chapter number prefixes of the markdown files be updated appropriately.

```yaml
lptype  : meta
title   : LitProg
subtitle: Pragmatic Literate Programming
language: en
authors : [
    "Manuel Barkhau",
]
manifest: [
    "overview::overview",
    "overview::technical_pitch",
    "overview::touchy_feely_pitch",
    "overview::use_cases",

    "user_docs::user_docs",
    "user_docs::example_usage",
    "user_docs::public_api",

    "how_to_write::how_to_write",
    "how_to_write::project_organization",
    "how_to_write::document_structure",
    "how_to_write::writing_style",

    "impl_prelude::impl_prelude",
    "impl_prelude::boilerplate",
    "impl_prelude::code_style",
    "impl_prelude::test_setup",
    "impl_prelude::types_and_datastructures",

    "porcelain::porcelain",
    "porcelain::config",
    "porcelain::cli",
    "porcelain::watch",

    "plumbing::plumbing",
    "plumbing::context",
    "plumbing::parse",
    "plumbing::build",
    "plumbing::session",
    "plumbing::metaprogramming",

    "docgen::docgen",
    "docgen::md2html",
    "docgen::html_postproc",
    "docgen::html_postproc_v0",
    "docgen::general_ui",
    "docgen::screen_ui",
    "docgen::print_ui",
    "docgen::html2pdf",
    "docgen::pdf_join",

    "plugins::plugins",
    "plugins::spellcheck",
    "plugins::readability",
    "plugins::rename",
    "plugins::python_fmt",
    "plugins::lint_litprog",
]
```

