
### Use Cases

 - Small Libraries/Tools
 - Blog Articles
 - Reports
 - Applications
 
`litprog` is primarilly intended for technical documentation and
high quality source code. It can be used in an existing code base
to generate a subset of its files, while leaving others alone.
You can start out writing a quick and dirty prototype and start
using `litprog` once you've proven your idea.


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


### Markdown vs Latex vs Scribble ...

The choice of Markdown/GFM as the source format is primarilly due to its ubiquity and the corresponding availability of tools, which includes syntax highliting in editors, extensions for tables, code blocks, diagrams. There may well be better markup languages, but Markdown is simple enough and sufficient for the purposes of LitProg. Reducing the friction to adopt LitProg gives plenty of reason to eschew other less well known markup languages.

The focus of LitProg is to write a program
 - reuse of tooling





### LitProg vs Docco vs Pweave

> [Docco](http://ashkenas.com/docco/) is a quick-and-dirty documentation generator. It produces an HTML document that displays your comments intermingled with your code. 

The approach of Docco and friends does not allow the literate program to be ordered as the author might wish to create a certain narative. Docco does a relatively straitforward compilation from with either html or 
The downside of this approach are the restrictions is that the order of documentation and code 

Report generation

https://github.com/pystitch/stitch
https://github.com/jankatins/knitpy
https://github.com/mpastell/Pweave

Witness the fact that none of these are self hosted compilers.

[Markdown-based Literate Programming][ref_gist_md_litprog]

[ref_gist_md_litprog]: https://gist.github.com/mrtns/da998d5fde666d6da26807e1f246246e
