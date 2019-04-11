```yaml
filepath     : "src/litprog/html_postproc_v1.py"
inputs       : [
    "license_header_boilerplate",
    "generated_preamble",
    "common.imports",
    "module_logger",
    "html_postproc_v1.imports",
    "html_postproc_v1.code",
]
```

```python
# lpid = html_postproc_v1.imports
import html.parser 
import html5lib
```

```python
# lpid = html_postproc_v1.code

class Parser(html.parser.HTMLParser):

    def __init__(self, strict: bool = False, *, convert_charrefs: bool = True) -> None:
        super().__init__(strict, convert_charrefs=convert_charrefs)
    
    def handle_decl(self, decl) -> None:
        """Handle an HTML doctype declaration (e.g. <!DOCTYPE html>).

        The decl parameter will be the entire contents of the declaration
        inside the <!...> markup (e.g. 'DOCTYPE html').
        """    

    def handle_starttag(self, tag, attrs) -> None:
        """Handle the start of a tag (e.g. <div id="main">).

        The tag argument is the name of the tag converted to lower case. The
        attrs argument is a list of (name, value) pairs containing the
        attributes found inside the tag’s <> brackets. The name will be
        translated to lower case, and quotes in the value have been removed,
        and character and entity references have been replaced.

        For instance, for the tag <A HREF="http://www.cwi.nl/">, this method
        would be called as handle_starttag('a', [('href',
        'http://www.cwi.nl/')]).

        All entity references from html.entities are replaced in the attribute
                values.
        """
  
    def handle_endtag(self, tag) -> None:
        """Handle the end tag of an element (e.g. </div>).

        The tag argument is the name of the tag converted to lower case.
        """
    
    def handle_data(self, data) -> None:
        """Handle arbitrary data (e.g. text nodes and the content of
        <script>...</script> and <style>...</style>).
        """

    def handle_comment(self, data) -> None:
        """Handle a comment is (e.g. <!--comment-->).

        For example, the comment <!-- comment --> will cause this method to be
        called with the argument ' comment '.

        The content of Internet Explorer conditional comments (condcoms) will
        also be sent to this method, so, for <!--[if IE 9]>IE9-specific
        content<![endif]-->, this method will receive '[if IE 9]>IE9-specific
        content<![endif]'.
        """

    
#     def handle_pi(self, data) -> None:
# Method called when a processing instruction is encountered. The data parameter will contain the entire processing instruction. For example, for the processing instruction <?proc color='red'>, this method would be called as handle_pi("proc color='red'"). It is intended to be overridden by a derived class; the base class implementation does nothing.

# Note The HTMLParser class uses the SGML syntactic rules for processing instructions. An XHTML processing instruction using the trailing '?' will cause the '?' to be included in data.
# HTMLParser.unknown_decl(data)
# This method is called when an unrecognized declaration is read by the parser.

# The data parameter will be the entire contents of the declaration inside the <![...]> markup. It is sometimes useful to be overridden by a derived class. The base class implementation raises an HTMLParseError when strict is True.



def main() -> int:
    # parser = MyHTMLParser()
    # print("moep")
    # assert False, "moep"
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

```yaml
lpid   : html_postproc_v1.test
lptype : session
command: /usr/bin/env python3
requires: [src/litprog/html_postproc_v1.py]
```

```python
# lpid = html_postproc_v1.test
import litprog.html_postproc_v1

litprog.html_postproc_v1.main()
```
