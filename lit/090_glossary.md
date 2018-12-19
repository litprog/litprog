Random grabbag of ideas. Most of it will be the basis for some things

 - The LitProg glossary
 - Zen of LitProg
 - List of Best practices
  - https://www.info.ucl.ac.be/~pvr/VanRoyChapter.pdf

 - readers: user, newbie, contributor
 - info tags:
 - meta tags: processed by some plugin
  - info-tag-def: a definition used for example in hover texts
    to explain the meaning of a section

 - tags: public, private, util, pure, legacy, historical, core, data, depricated, critical, validation, boilerplate, meta, qa-disabled, qa-minimal, qa-full
    - tradoff: certain design choices may be made out of
      inertial, because the authors didn't know any better or as
      a conscious choice. Code does not speak for itself about
      why it was written a certain way, nor about what other
      alternatives were considered.
    - public: Used as part of public documentation. Use this to
      hide/spare your users from implementation details (private
      is the default).
    - dragons: code which is especially messy or which works in
      a counterintuitive, complicated way.
    - core: Some concepts are key to understanding an entire program.
      When they are understood, everything else falls into place.
    - critical: Programs often spend 99% of their time churning away
      on the same few lines of code. This tag warns that this portion
      of
    - pure: may imply for example that a function can be relocated
    - historical: information that is no longer relevant to
      the current state of a codebase, but perhaps interesting to
      understand how the codebase came to its current state
    - depricated: Code that is kept for compatability should
      always include
       - a link to code by which it is superceded
       - a policy regarding when the code will be removed
       - a policy regarding what level of maintenance applies
    - legacy: similar to depricated, but there is no time horizon
      where the functionality will ever be removed. instead it
      has to be maintained

 - codebase: litprog source text
 - headlines
 - part
 - chapter
 - chapter summary
 - asside/quote
 - chapter prefix
 - section

 - block
 - code block
 - output file path
 - derived block

 - artifact
 - overview
 - glossary
 - conventions
 - code artifact
 - html artifact
 - pdf artifact

 - programming user experience:
  - statefulness is evil but unavoidable: think long and hard
    about how to encapsulate statefullness so that programmers
    can live as if they were in a functional world.
  - writing headlines, which creates an outline, is the foundation
    of a mental map for future programmers.
  - usage friction: a cognitive burdon that an developer must
    bare in order to use your code. this includes overly
    explicit api calling conventions (lack of defaults), but
    also excessive startup time. If the user has to wait 30
    seconds for your system to respond, then they cannot do
    interactive development.
  - muscle memory: programmers don't just program computers, they
    have memory in their muscles which they can program. A programmer
    will be in a state of flow, when their muscle memory and the
    responsiveness of your application, allows them
  - Ego out: remove yourself from the equation and what is left?
    if your software solves a probem a user was not even aware
    that they had, then your software is ideal. you should strive
    to move humanity forward and accept that the vast majority
    will never know your name or how grateful they should be to
    you.
  - code quality: surfacing the quality of the code so that it is
    visible to managers, makes it more likely that they will care
    about the actual implementation. poor code quality is partially
    a consequence of the fact that barely anybody ever looks at it.
    if you saw a bridge made of straw and cellotape, you might think
    twice about crossing it. yet that is what our machines look like
    on the inside, if you ever cared to look. documentation and
    structure for your code, surfaces it so that it is visible to
    users who don't have an ide, don't have an editor and who don't
    understand version control. If they can see it, and understand
    part of it, then you have a chance of them caring about it.
  - professionalism: programmers are not professional engeneers.
    at best they are craftsmen, more often they . litprog is an
    effort to raise the bar as much as possible, through
    1. leading by example 2. tooling where possible, 3. using
    established practices if they exits 4. education
    as a last resort
  - quality is not a property of an individual compoent, it an
    emergent property of a whole system. High quality software systems
    assumes the possibly errors and
    0. validates its assumptions as early as possible so are
       errors actually generated close to where they occurred
    1. reports errors in a way that is easy to understand and reproduce
    2. minimizes their damage
    3. corrects errors where possible

 - conventions: these are the things you would point to in a
   merge request to justify making a change.
  - early exit/guard clause (to avoid excessive nesting)
  - think positive: boolean logic
  - named > positional
  - flat > nested
  - fail fast / errors > c
  - single source of truth
  - dogfooding
  - canonical meat: as much as possible, the meat of your program should
    only deal with a single canonical form of data for a given concept. Outside
    of your program, various formats and synonyms may be used, but these should
    be translated to your canoncial form as soon as possible for your inputs and
    as late as possible for your outputs. This reduces the number
    of places you have to deal with the complexity of translating
    concepts between their different forms.
    - https://www.youtube.com/watch?v=nqwZIJ4KCRw
      - the incorrect is inexpressible
      - value objects
  - inversion of control/
  - hidden/implicit else
    - https://www.lvguowei.me/post/you-think-you-know-if-else/
    - https://www.youtube.com/watch?time_continue=2&v=eEBOvqMfPoI
  - hidden/implicit else vs early exit/guard clause:
        For procedural code involving validation/termination
        logic, the early exit rule is applicable: For functional code
        the hidden else rule is more applicable (especially when your
        language doesn't have a case statement). If the hidden else
        rule bothers you because of excessive nesting, consider how to
        refactor your code, so it can be written with only two levels
        of indentation.
  - vertical > horizontal: multiple lines with names/variables instead of oneliners
    with nested expressions
  - automation > discipline: Anything produced by humans which can be incorrect in some
    way, and for which an automated check can be written, should be automated, rather
    than wagging a finger.
  - convention > configuration: A common cause of human error is invalid configuration.
    If there is nothing to configure in the first place, then this is preferrable.
  - explicit > implicit
  - explicit > implicit vs convention > configuration
  - simple and verbose > complicated but consise
  - validated vs parsed: parsing introduces an extra layer of
    abstraction. This can be warrented, but it may be better
    to write code to validate a more verbose format than that
    is stupidly simple, than it is to write a parser for a
    format that people will have to learn first.
  - aligned > unaligned: don't underestimate the ability of
    humans to recognize minute visual details that fall outside
    of a pattern. If you align your data, many typos pop out
    visually.
  - sorted > random
  - setup/dependeny mayhem:
  - a priority is a  position in a queue, it's not a label. Priorities are
    relative to each other, not absolute.
  - automation of trivial tasks can be worth it, even despite
    this chart https://xkcd.com/1319/. The smallest bit of
    friction can change your workflow. You avoid creating small
    isolated merge requests, because the steps involved are just
    a bit too cumbersome. Instead you just commit to master and
    the culture of code review in your organization suffers.
  - footgun
  - declarative > imperative: assuming you can afford the
    metaprogramming to parse the declarative language
  - functional > procedural
  - structured <> procedural ?
  - forgiveness > permission
  - lazy + dynamic schema > no schema > hardcoded schema:
  - premature performance optimization is often a red herring:
    not understanding the performance of your code, at least on
    the level of its complexity then you don't understand your
    code. using a profiler or tracer is not just about analyzing
    performance, it's about analyzing what your program is actually
    doing. if you don't do performance analysis, then do you really
    know what your program is doing?
  - reacting > polling: an event system is more flexible and resource efficient than
    writing polling logic
  - encapsulate/modularize: the best thing you can do to avoid big piles of spaghetti is
    to think about how to sensibly factor your code into little reusable pieces
  - pureness
 - naming conventions
  - verbs in function names
  - common prefixes: `iter_` for generators, `new_` for
    factories/constructors
  - prefixes unless called with namespace (`def info` is fine
    because it's always called as `logger.info`)
  - mappings: {value}_by_{key}
  - example > explanation : https://www.youtube.com/watch?v=_ahvzDzKdB0

 - programs vs scripts vs libraries:
  - programs are self contained and must be
    maintained. There is a certain level of
    quality implied,
  - scripts are what you write to drive programs. if you start
    maintainging
  - typing is not the bottleneck. verbose code is ok if
    its easy to understand.
    - this is not excuse to not learn touch typing. if your
    eyes are looking at the keyboard, they're not looking
    at your code. if your brain is focused on the mechanics
    of typing, it's not focused on the logic of your program.


 - hidden defaults
  - best practices and coding conventions simplify things for
    readers who know about these practices and coding
    conventions. each convention should have a name and an icon,
    so that new programmers review your coding guidlines to
    build the mental context required in order to read your
    code. declare your best practices and coding conventions
    explicitly by name (especially those not checked by a linter
    or type checker), so that experienced programmers can scim
    over your guidlines to get an idea of what they can expect.