# Writing Literate Programms

Best practices for structuring your documents

TODO: Find out if there are conventions for writing RFC documents
which might be adopted.

The Craft of Writing Effectively - Larry McEnerney
https://www.youtube.com/watch?v=aFwVf5a3pZM

## Caveat Emptor

This chapter was written without extensive experience writing
a literate programs. The thoughts here are premonitions at
this point and are written to guide the development of litprog
itself.

## Philosphy

### Write as if Your Code Will be Maintained by Your Child

This project is born out of disapointment in the quality of the
software we produce and consume. Everything is not bad and one
should always take the constraints of developers and markets into
consideration. Programmers are not always lazy and managers are
not always short sighted, at the end of the day features must be
shipped and payroll must be met. LitProg is an attempt to raise
the bar of software quality by

 1. Providing tooling that can be used in any project
 2. Leading by example.

LitProg will succeed or fail based on how well it can show to
programmers that it is easier for them to understand a program
written with LitProg and to organizations that this implies lower
long term costs and greater ability to adapt software to new
needs as they arise. LitProg produces html and pdf artifacts, so
that programs written with LitProg become more accessible to
people with little experience in version control or programming.
This increased visibility may help to expose poorly documented
and highly convoluted code, helping to justify the time needed
to improve its quality.


### Why has Literate Programming not taken off?

Spending extra time to improve vague notions of quality, with
very definite short term costs, but only hypothetical long term
benefits can be hard to justify. To LitProg is a tool
which aims to:

 1. Minimize costs of adopting literate programming as a default.
 2. Expose the quality level of software.




Literate programming is more work than just programming, or
just writing technical documentation. To a certain extent the
lack of adoption of this style can be attributed to the extra
effort that is required.

The extra effort cannot be the full explanation however; after
all programmers have adopted some practices which appear to be
extra effort in the short term, but which have a good payoff in
the medium to long term. In particular automated testing has
become a widespread practice and the industry appears to trending
toward languages with stricter type safety.

From this we can assume that the costs vs benefits of literate
programming have simply not been demonstrated to be a net gain.

Another factor may be how projects naturally evolve. Programs
often start out very small to serve a particular use case, with
very little thought for the lifetime of a project. What starts
out as a little script, grows into a small module, and very
occasionally is refactored to deal with new use cases.



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


## Who is your reader?

There are three roles a reader may occupy that a literate program
needs to cater to.

 1. Users: Programmers who want to import and use the program and
    who are primarilly interested in using the public API of the
    program but otherwise want to treat it as a black box.
 2. Newbie: Programmer trying to (re)gain understanding of a
    program.
 3. Contributor: Programmers and editors familiar with the source
    text and structure, trying to extend or fix a part of it.

These are not fixed categories, rather they are roles and the same
person may have multiple roles at different times. A developer
may be a contributor in one part of a program, a newbie of another
part and a user of yet another, all at the same time. The purpose
of these roles is to scope what part of a text is relevant for
each role, so a developer can focus their attention.


### Users

Users are the most common kind of programmer and so they should be
catered to first. The initial chapters of a literate program should
illustrate usage of a program, expressed for example in the form of
test code that invokes the core API of a program. It should be
possible to read this documentation like an essay from beginning


### Newbies


### Contributors


## Programming Practices


### Parts, Chapters, Summaries and Sections

In the age of reddit and twitter, readers are well trained at
scanning for the content they're interested in. Long paragraphs
of text are only read if their headline has convinced the reader
that it is worth reading. Don't write a paragraph if a bulleted
list will do. Don't write a paragraph if the code speaks for
itself.


### Summaries

A summary is the first (or first few) paragraphs of a chapter. It
is reproduced of course in the chapter text itself, but also in
the "Program Overview" which is generated from the headings and
these summaries. It should be possible for a reader to read the
"Program Overview" and build a mental map of what portion of the
the program can be found in which chapter.


### Footnotes

For links/references only. It should be possible to understand
a text without reading footnotes.


### Asside

For anecdotes or other text not directly related to understanding
the program.


### Declare Above Usage

I'm undecided on this. If your going to have a convention in
program code, then this should be it, however for documentation
it is probably better to focus the attention of the reader on
usage code first, ie. to give the definition only later in the
text.

Declarations always have to precede their usage in the order of
execution, however this is not true for their lexical order in
the source code. A function can be declared after code in another
function which depends on it, just so long as the depending
function is only invoked after its dependancy has been declared.

Since there are quite a few cases where the order of execution
and order in the program text must be the same, if we have to
choose one lexical ordering for declarations, then it should be
to declare first and above any usage of a declaration. Ironically
this means that in order to get a high level understanding of a
program text, it should be read lexically from the bottom up.


### Single Source of Truth

### DRY and Metaprogramming

### Avoid Synonyms, be explicit

A program is not like fiction, where the reader will appreciate
variety in your vocabulary, particularly when it comes to
concepts of your program. Unfortunately we don't have compilers
for prose, but it may help for you to think about the terms you
use as if they were types to be parsed by a compiler.

If for example you use the word `file`, it might not be clear if
you mean by that, a `file_name`, a `file_path`, a `file_url`, a
`file_handle` with which the bytes of a file can be read, a
parsed `file_object` in memory, the `file_bytes` loaded into
memory, the bytes of a file on disk or in a database system or
somewhere on the network.

In short, if there is *any* chance of confusion:

 - define your terms
 - be explicit about your terms
 - use your terms consistently


Even worse is asking the user to do pointer chasing through
your text. Prefer using the explicit term you are talking about,
even if you have already mentioned it in the same paragraph and
you could just say "it", "its", "they", "them", "their". Remember
that you are writing technical documentation, so it is reasonable
for your text to be stilted.


### Relationships

When expressing a relationship between `x` and `y`, prefer `x` of
`y` as opposed to `y`'s `x`. `x` of `y` doesn't involve quotes
(which is especially good when , it sounds more punchy and is
therefore clearer.


## Chapter Ordering

Parsing of the markdown files is done in lexical order of their
filenames. A more flexible alternative would be to explicitly
declare the ordering in some form of metadata, but since authors
will be working with these files using their normal editors and
file system browsers a pragmatic choice is to use a simple fixed
width prefix, which we will refer to simply as the *chapter
prefix*.


## Generated Content

Some parts of a text are more important than others, so in
order to help users and newbies, there are three things
which `litprog` generates from the program text.

 - Table of Contents (from h1: part, h2: chapter headings)
 - Overview (from h1, h2, h3: section headings and summaries)
 - Glossary (from definitions)


TODO: what is a definition?


### On Gender

Gender is a distraction, don't write him/her his/hers, it is very
rare to encounter code where the gender of the author has any
bearing on the meaning of the text. Unless it's not possible,
prefer the use of they, them or their. Ideally your text should
be about your ideas, and my impression is that this is currently
the least bad compromise of side stepping this whole topic.


### Workflow

When writing, don't interrupt your flow, just write. Edit on a
second pass, when you feel you've expressed your ideas well.
Similarly, write code using your unittests, in a flow of red,
refactor, green. On a second pass run the formatter linter
and type checker to make sure you have dotted every "I" and
crossed every "t".

There is a recommended practice that says "PEP8 only unto
thyself", which is an admonishment to not correct other peoples
mistakes, but to allow them to correct them themselves. Well,
there are mistakes and then there are mistakes. Fixing other
peoples typos and linter errors has the risk of building
resentment. Either the person doing the fix resents that the
original author is lazy and sloppy to not have their tools set up
correctly, or the author resents being nitpicked at by a
coleague. The communication overhead involved in the back and
forth to report these minute issues, to communicate why something
is an issue, and to verify that the issue was fixed correctly,
can be much higher than simply fixing the issue in place. As an
editor, just fix the issue, point to the rule or just reproduce
the complaint of the linter.

To bot curb lazyness and sloppyness, and encourage a culture of
code review, I suggest a light hearted approach. Since developers
should have their tooling set up correctly correctly and
established muscle memory actually use that tooling, it is fair
to play the following game: Any build which fails because of a
trivial error which could have been caught by a linter,
introduces a debt


### Vocuabulary

The glossary is used as a source for spell checking. In addition
to a standard english word list and


### Itemised Lists are Fantastic

Comma separation should be reserved for very short lists, where
the commas are separated by only a very few words. It is
irritating to be in the middle of reading a sentance, to
then encounter a comma, to have to judge what kind of comma it is,
realse it's for the separation of items, reflect on the last
6 words of a sentence you've been reading are not just a
continuation of the previous sentence, but in fact the first item
in a list of items, so you have to reinterpret them before you
continue. An itemised list is a much better on the other hand,
since it gives an immediate visual queue to the reader.

### Conclusion First, Argumentation Second

State early and directly what it is that you want to communicate,
the idea that you want to stick in the mind of your reader. The
reader then has the oportunity to skip past a section because
they are already convinced, or to read on and judge if you are
making sense.


### Cowboy Programming

Inevitably you may want to bypass all of the best practices
because you are short on time and know what you're doing. Since
litproc only compiles to code which then is run separately, it is
easy for a cowboy to directly write code outside of litprog and
bypass all the linters and checkers it runs. In order to reduce
the temptation to do this, you can mark a file or peace of code
with a quality assurance level to control the build process of litprog:

 - `qa-disabled`
 - `qa-minimal`
 - `qa-full` (default)

Only under extrodenary circumstances should you have to mark code
with qa-disabled, very rarely and only for short periods (until
you have the time to refactor) should code be marked with
`qa-minimal`. `qa-full` reenables full checking for portions of
a file which has a lower qa level set at the file level.


