## Why use LitProg?

Ideas
  - The torch metaphor: https://divan.dev/posts/visual_programming_go/
  - The selfish contributor: https://fosdem.org/2020/schedule/event/selfish_contributor/
    - How dows LP improve the motivation for contributors
  - why are we so bad at software engineering (Iowa Caucus Fiasco)
    - https://www.bitlog.com/2020/02/12/why-are-we-so-bad-at-software-engineering/
    - https://www.reddit.com/r/programming/comments/f2rplr/why_are_we_so_bad_at_software_engineering/
  - Encouraging a Culture of Written Communication: https://news.ycombinator.com/item?id=23141353
  - Writing for Software Developers: https://news.ycombinator.com/item?id=23153469

### The Thin End of the Web

to write your programs, for example by stringing together a series of code blocks without spending any time on formulating a coherent narrative. No ghosts of LP purism will come to haunt you for using LitProg in this way 🤞.


A first step to using LitProg is to create technical papers or articles (such as this one), which don't just include code snippets that were copy and pasted from some other source, but which are the actual source that was used to explore a topic.

LitProg creates source code files and static documentation, you can adopt for part of an existing project where you feel it makes sense and it doesn't have to it over completely.

Perhaps some thought about a reasonable program structure and a few chapter or section headings are not too much effort. This gradual approach may already provide enough value to justify the use of LitProg, even if you can't justify the cost[fnote_exploration] of fully adopting LP.


### Capital Accumulation vs Consumption

The maintainers are fighting what I believe to be a loosing battle. They are trying to make people care more about the unsexy work of maintenance, rather than focusing on new shiny and innovative development work. They argue that maintenance work is seen as low status and neglected as a result.

http://themaintainers.org/blog/2019/7/30/why-do-people-neglect-maintenance

I argue that this is a lost cause and propose to hack this system. Instead of moralizing we should accept that developers want credit for new work and we should make it easer to produce small incremental deliverables that replace previous work. The derogetory German term "Wegwerfgesellschaft" (literally throwaway society) captures the attitude we should take to deliverables. Get a hold of the new shiny thing, forget about repairing stuff and throw out the old stuff. Fortunately software does not suffer from the same problems of waste and pollution that we have in the physical world.

In the line of programming, every line of code can be seen along a gradient, starting from throwaway experiment read only by the author (perhaps only entered once into a repl to clarify how something works) and ending at highly reusable well tested infrastructure code that changes very slowly if at all. The former can be seen as code that is produced merely for consumption, the latter for production. The former is produced quickly, cheaply and gives an immediate sexy result, the latter is boring and tedious.

The hack is to make infrastructure code much easier to write (decrease its cost) in a way that is more accessible (increase its value), so that it is more likely to be reused and leveraged for the production of code that is consumed. Ideally, each individual piece of infrastructure software will be much more focused, so that it is easier to use as a building block and each piece of consumer software is itself much smaller, but built on a much broader base.


### Embrace Competition

Smaller fragments of software make it possible to distribute credit more widely. This means that credit is diluted, but perhaps Linus Torvalds doesn't deserve all the credit for Linux. Replacing fragments (while giving due credit to predicessors) rather than maintaining and updating them, is a better fit to motivate developers to take ownership of existing software, while being able claim that some portion of it is theirs.


### More Contributors with different skillsets

Writers and editors

### Cultural Barriers

In the best case, LitProg will lower one barrier to LP, but by itself it cannot lower the most significant other barrier to adoption: LP requires a greater short term effort by programmers and maintainers.

LitProg will do little to change a culture in which the short-term price of writing software is always minimized, even at the cost of long-term maintainability. The development of such a culture is understandable: While short-term costs are visible and concrete, long-term costs are vague and may not not even materialize if a project fails early in its life.

Be that as it may, there are some projects for which a larger investment in quality and maintainability does make sense and project owners are to be the judge of that. LitProg is an experiment to provide examples of literate programs, so that you can judge if this approach makes sense.


### Contra LP

!!! quote "Martin Fowler"

    Any fool can write code that a computer can understand.
    Good programmers write code that humans can understand.


While LitProg aims to improve on tooling to generate code and documentation files, this does come at the cost of integration with tools used by many programmers. Common IDEs and programming environments will not provide the same level of support for code embedded in markdown files as they do for code in customary source code files. LitProg may be more appropriate for programmers who are comfortable working

Writing is a different skillset than programming. Adoption of LP will likely result in reduced speed of development, without much benefit if programmers don't know how to explain themselves.

Build step, layer of abtraction


### Costs and Benefits of LP

I won't claim that using LP is the cheapest way to write software, at least not in the short term or for exploratory programming. I do think LP has the potential to benefit long term projects. The longer the lifetime of a project, the more contributors involved, the more distributed those contributors are, the greater the potential benefits of LP. I have no data to back this up, but that seems to be a perenial problem with programming paradigms.

LitProg allows programmers to capture their state of mind, so that it is easier to reboot that mindset later and to move the project forward. Typical software projects offer little guidance new programmers, to help them gain a deep comprehension of a codebase. When they have difficulty understanding the approach of the original authors, there is a great temptation to write ad-hoc patches and dirty hacks rather than sustainable changes. Put differently, a lack of up front investment can lead to ever greater temptation to incur ever more [technical debt][href_wiki_techdebt].

LP allows for a more sustainable approach to software development. During development, programmers expose flaws in their own thinking as they try to express their thoughts. They can structure their program in ways that benefit human comprehension, rather than in ways that suit the compiler. The increased accessibility of their programs in the form of documentation. Put differently, LP enables the up front investment to prevent long run costs from spiralling out of control.

LitProg can be used to produce good documentation, including diagrams using [Svgbob][href_svgbob], equations that use [KaTeX][href_katex] for typesetting, footnotes, tables, and much more. Keep in mind however, that the primary goal of LitProg is to make it possible to write programs with a coherent narrative, and only secondarilly to create pretty PDF files. The layout, typesetting and esthetics of the documentation is secondary to the extend it causes friction during programming. The primary goal is for programmers to focus on the logic and narrative of their programs. The purpose of the documentation is to make programs more accessible to more people and in a more situations. The the documentation is not there to be pretty, but so that more eyeballs can take a deep look at your program.




### Introduction to `litprog`

    "The craft of programming begins, not with formatting or
    languages or tools or algorithms or data structures; the
    craft of programming begins with empathy."
                                - Kent Beck (paraphrased)

    "Any fool can write code that a computer can understand.
    Good programmers write code that humans can understand."
                                - Martin Fowler


I have spent most of my programming career as the sole or main
developer of the software I've developed. As I look to the
future, with the prospect of writing software that more people
have to understand, I know that I must change my ways. In the
past I could keep a whole system in my head and junior
programmers had a difficult time wrapping their heads around the
software I wrote. The software I wrote was full of implicit and
undocumented conventions, known only to me. Writing documentation
has seldom been an integral part of my development workflow, only
recently have I tentatively started doing readme driven
development.

I realize that I must change my ways and I feel that I am not
alone. I want to write software that is of high quality, and code
which is more accessible to other programmers. As a starting
point on this journey, I've decided experiment with literate
programming and vowed to not write any software that involves
networking or threading until I have demonstrated (at least to
myself), that it is possible to write more simple systems that
can be understood, used, maintained and extended by other
developers.



### Documentation is Always Outdated

I cannot count the times I have witnessed a comments and code being inconsistent with each other, because the code was updated without updating the comment. In one particularly memorable case it was a one line comment, with one line of code directly next to it. If developers cannot be expected to do the most trivial documentation, how can they be expected to adopt a whole new paradigm that is centered around documentation.

#### Document Why not What

As much as possible the code should express by itself what it actually does, but code can rarely express why it was written or why it was written the way it was.

 - Tech Choices
 - Trade-offs
 - Business Needs


### The Price of Documentation

Programmers go back and forth between complaining that
code is not documented, that the documentation is
out of date, and if it is up to day, nobody reads it.

In order of priority, your attention as a contributor
should be focused on:

 - The existence of the code.
 - The correctness of the code
 - The continued correctness of your code. Ensured through
   tests that catch regressions.
 - The simplicity of your API. Reduce the cognitive
   load of your users as much as possible.
 - The expressiveness of the code. Ideally it should speak for
   itself. Review the [conventions](/conventions) for examples on
   how to do this.
 - Documentation of outputs. Ideally with short examples
   which are easily reproduces.
 - Documentation of inputs.
 - Headlines so readers can find what they want to read.
 - Metadata so generated output can be filtered




### The Human Element

#### Accessibility and Visibility

With automated testing, when using a continuous integration environment, members of the project who are not intimately involved in the details of the code-base can gain some insight into the health of the codebase. Programmers who diligently write tests with high coverage can keep themselves honest and the temptation to cut corners is either kept in check or at the very least exposed. If coverage goes down, if builds are failing and if deployments are happening anyway, then all of this may be justified in the context of a project, but it is a sure sign of degeneration in the standards of the project and may reduce the long-run viability of the project.

Literate programming offers a similar kind of exposure. Programmers who express the intent, the abstractions, the workarounds and the trade-offs in plain English, who express ideas that are not expressed in the code, will keep themselves more honest as they can assume that their peers will not simply gloss over an undocumented and cryptic part of the codebase. If they simply hack together some code and only half understand what it's actually doing, then the lack of or incoherence of documentation will more readily expose the degraded health and long-run viability of the project.


### Sync vs Async Communication

 - Online goes to the void
 - Paper is forever
 - An idea in writing leaves less room be vague
 - Remote developers
 - Onboarding Speed
 - Shared Language
 - Deep Work: Scurrying around at the surface, running frantically but getting nowhere fast. Know the limits of [YAGNI][ref_wiki_yagni], build foundations and the top layer will be thin and easy to write.



### Ownership and Accountability

 - Hacking together something that just barely works, just enough to get a manager off your back.
 - Broader Contributor Base


#### Sentimentality, Artifacts and Ownership

    Der Mensch ist doch ein Augentier,
    nur schöne Dinge wünsch' ich mir.

        – Goethe


    The saying goes: "By their fruits ye shall know them.", not
    "By their words ye shall know them.". Actions speak louder
    than words.

Humans are sentimental creatures. I want to write good software,
and I know this is not an obvious way to make money, certainly
not in the short term. But I do want to have pride in my work and
a sense of accomplishment. Part of that sense of accomplishment
is to have a physical artifact that can be understood and
appreciated by as wide of an audience as possible, perhaps even
by people in my social circles that are not programmers.

I hope that forgoing short term benefits of hacking together
something that works just good enough, will pay off in the long
term. I hope that people who can see and understand and
appreciate my work will see and feel the value of treating
programming as a wonderful mix of the arts of engineering,
mathematics and writing.


If the following code were to fail, the output document would have pragmatically generated visual indication that this was the case.

```yaml
lpid   : demo
lptype : session
command: bash
timeout: 1
echo   : False     # output
term   : True
expected_exit_code: 1
```

```bash
# lpid = demo
echo "hello world";
```

This code block continues from the LitProg declarations of the previous block. In this case it is a continuation of the previous session with `lpid=demo`.

```bash
# lpid = demo
echo $(expr 40 + 2);
exit 1;               # The captured output should be an error
```


### What is Quality

Quality has these dimensions:

 - Maintainability
 - Efficiency (low ba)
 - Performance


### Writing in Order to Think

A wise man once said, that "People think by talking and in order
to think, you have to have someone to listen to you, because it's
very hard to think. Hardly anyone can think! Even the people who
can think, can only think about a limited number of things."


### The Tipping Point

> If you plan to go through a jungle, do you march forward with
> your bare feet? Do you at least get some provisions and a good
> pair of boots and a sharp machete? Or, do you stand back for
> a moment and think? Think about what you're trying to accomplish,
> about how often you're going to make this trip in the future,
> about all the other people who are on the same journey as you
> are, and perhaps the right way forward is not to march through
> the jungle, but to first clear a path and to then build a road.

Programmers often forge ahead when writing software, churning out
code until the compiler stops complaining and ship it. This is
fine for one off programs, and it's even fine as a first step.
Code that runs and does what you want is better than no code at
all. Any effort you would have spent to make your program more
maintainable would have come at the expense of functionality.


At some point however, the balance tips. Some people start
cursing themselves for the hairballs they have produced, others
move on and leave the mess to another poor soul, managers become
disheartened about the apparent reduction in productivity.

Before we become too disheartened, we should realise that it is
the easiest thing in the world to point a finger and say that
other people should have put in more time and effort, so that
your life would be easier. We don't know their circumstances and
constraints, so I try to refrain from passing judgement.

Patching an existing codebase can require more effort than
in some idealized scenario. Just to name some things, you might
for example be better off spending your time on:

 - Better developer tooling to catch errors earlier
 - Writing a meta-program, to reduce boilerplate
 - Rewrite a module with the wisdom of hindsight.

None of these produce a direct result in terms of features. They
are investments that may or may not pay off.
Whenever it is that we come to the realization, that




### Focus on Writing vs Layout


In order to make integration with existing tools easy and so that LitProg is language agnostic, the macro and plugin system works strictly with text, and does not do any AST/parsing of code blocks. The exception to this is LitProg metadata in the form of code block options.

- `litprog` declarations for code blocks use language specific comment syntax.
  In other words, a LitProg declaration in a python code block the first line
  would start with `# litprog` and in a c++ code block the code the first line
  would start with `// litprog`. This choice was made



## Sustainable Complexity

The complexity an individual programmer can hold in their head, because they were the ones who generated that complexity, is more than the complexity that a project can sustain. Once an new developer wants to take over the project, it is unlikely that the previous programmer can fully transmit a very complex system forward. So beyond a certain level of complexity, a project is doomed to fail.

Programmers need to work with abstractions with well defined constraints. Figuring out how 10 distinct concepts fit together the same level is next to impossible. The mind needs to be able to linearize the relationsips of concepts into a heirarchy if their connections are to be understood.

Abstractions can be a blessing and a curse. Simple software results from finding the appropriate abstractions to iteratively build upon. Finding the appropriate building blocks out of which to compose at higher and higher levels, without going so high that the air gets too thin to breath.



[ref_wiki_yagni]: https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it



[fnote_exploration]: Especially in exploratory phases of development, when creating new modules and implementing new features, spending time on explanations and justifications of logic that may well disapear very shorty, can reasonablly seen as a waste of time.

