# Serving A WebApp

In order to minimize page load time, the ideal page that needs
javascript would.

01. Initial dns lookup is the first bottleneck users will
    encounter. Mitigate it for repeat visitors by using service
    workers.
02. Perform an initial reander without any javascript, ideally
    including a headline and the first paragraph.
03. Have one bundle with all javascript.
04. Have the bundle compiled in a way that a minifier can easilly
    inline across module boundaries.
05. Defer js parsing by putting function definitions in strings
    and using eval to parse them when they are needed.
06. Set a cookie with the version number of the js that was
    loaded. This way a http2 server can determine if an update
    bundle needs to be sent, or if it is cached by the browser.
07. Everything needed in the first few seconds, should be served
    from the same domain, avoid dns lookups.
08. Horizontal page layout and navigation should be final after
    initial reflow of the page.
09. Use sized containers (images in particular) for lazy loaded
    content so that reflow is not required when the content is
    finished loading.

Avoid Juddering/Reflowing layout

01. Set the scroll property on your body, even if the content
    might initially fit on one screen. Once the rest of your
    docuemnt loads, everything will shift to the left as the
    scrollbar is tacked on to the right.

02. Slideouts should be avoided like the plague, but if you
    reeeeaaly need them, they should be overlays and not shift
    the body content in any way.

03. When adding an overlay, consider the aspect of your users
    screen. On a vertically oriented (portrait/typically mobile)
    screen, you should prefer adding them at the bottom, with the
    ok and close buttons on the right. On a horizontally oriented
    (landscape/typically desktop) screen, they should be on the
    right, ideally so that they don't cover the actual content
    the user is interested in.

04. If you have a full screen overlay,
    make sure that ESC maps to closeing/canceling it, and
    ENTER/SPACE maps to accepting it.

05. The layout of tables, charts and images (figures/block
    elements) is not as flexible as headlines and paragraphs of
    text. There is a risk that they are not displayed on the same
    page as than the paragraph which references them. You should
    not explicitly declare page layout in your litprog source,
    but to make good page layout possible you should follow a few
    rules. Introduce tables you need to reference before the
    paragraphs that reference them. Readers may be able to
    understand a chart or image without context, or if not, they
    will read the text directly after it. On the other hand,
    reading a paragraph which references an block element that is
    nowhere to be seen, may not be registered at all, until two
    paragraphs later the page is turned and the reader realizes
    what the author was talking about If at all possible, a block
    element should always be introduced directly after a section
    heading or a summary paragraph, and if a paragraph is to
    reference it, it should be directly after it. Also give your
    figures unique names/titles, so they can be referenced later
    without having to care about reordering, as is the case with
    the enumerated Fig. N naming commonly used in books.
