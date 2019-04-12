## Why use LitProg?

Long term thinking pays of in the long run.



### Introduction to `litprog`

    "The craft of programming begins, not with formatting or
    languages or tools or algorithms or data structures; the
    craft of programming begins with empathy."
                                - Kent Beck (paraphrased)

    "Any fool can write code that a computer can understand.
    Good programmers write code that humans can understand."
                                - Martin Fowler


I have spent most of my programming carreer as the sole or main
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
 - Tradeoffs
 - Business Needs


### The Price of Documentation

Programmers go back and forth between complaining that
code is not documented, that the documentation is
out of date, and if it is up to day, nobody reads it.

In order of priority, your attention as a contributor
should be focused on:

 - The existence of the code.
 - The correctness of the code
 - The continued correctess of your code. Ensured through
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

Literate programming offers a similar kind of exposure. Programmers who express the intent, the abstractions, the work-arounds and the trade-offs in plain english, who express ideas that are not expressed in the code, will keep themselves more honest as they can assume that their peers will not simply gloss over an undocumented and cryptic part of the codebase. If they simply hack together some code and only half understand what it's actually doing, then the lack of or incoherence of documentation will more readilly expose the degraded health and long-run viability of the project.


### Sync vs Async Communication

 - Online goes to the void
 - Paper is forever
 - An idea in writing leaves less room be vague
 - Remote developers
 - Onboarding Speed
 - Shared Language
 - Deep Work: Scurrying around at the surface, running frantically but getting nowhere fast. Know the limits of YAGNI, build foundations and the top layer will be thin and easy to write.

### Ownership and Accountability

 - Hacking together something that just barely works, just enough to get a manager off your back.
 - Broader Contributor Base


#### Sentimentality, Artifacts and Ownership

    Der Mensch ist doch ein Augentier,
    nur schöne Dinge wünsch' ich mir.
    
        – Goethe


    The saying goes: "By their fruits ye shall know them.", not
    "By their words ye shall know them.". Actions speek louder
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


If the following code were to fail, the output document would have programatically generatiod visual indication that this was the case.

```yaml
lpid   : demo
lptype : session
command: python3
timeout: 1
echo   : False     # output
term   : True
expected_exit_code: 1
```

```python
# lpid = demo
assert True
```

```python
# lpid = demo
# This code block inherits the LitProg declarations of
# the previous block. In this case it is a continuation of the previous
# "validation" session.
print(1 + 1)
assert False          # The captured output should be an error
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
> a moment and think? Think about what you're trying to acomplish,
> about how often you're going to make this trip in the future,
> about all the other people who are on the same journey as you
> are, and perhaps the right way forward is not to march through
> the jungle, but to first clear a path and to then build a road.

Programmers often forge ahead when writing software, churning out
code until the compiler stops complaining and ship it. This is
fine for one off programms, and it's even fine as a first step.
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
 - Writing a metaprogram, to reduce boilerplate
 - Rewrite a module with the wisdom of hindsight.

None of these produce a direct result in terms of features. They
are investments that may or may not pay off.
Whenever it is that we come to the realization, that




### Focus on Writing vs Layout


In order to make integration with existing tools easy and so that LitProg is language agnostic, the macro and plugin system works strictly with text, and does not do any ast/parsing of code blocks. The exception to this is LitProg metadata in the form of code block options.

- `litprog` declarations for code blocks use language specific comment syntax.
  In other words, a LitProg declaration in a python code block the first line
  would start with `# litprog` and in a c++ code block the code the first line
  would start with `// litprog`. This choice was made






[ref_wiki_litprog]: https://en.wikipedia.org/wiki/Literate_programming
