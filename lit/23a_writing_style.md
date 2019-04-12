### Writing Style

While there are many (much more authoritative) sources on writing good prose, the specific kind of prose of a literate program, and the specific tooling used to compile it, does lend some justification for a short chapter with reccomendations on writing style.

#### Itemised Lists are Fantastic

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


#### Conclusion First, Argumentation Second

State early and directly what it is that you want to communicate,
the idea that you want to stick in the mind of your reader. The
reader then has the oportunity to skip past a section because
they are already convinced, or to read on and judge if you are
making sense.


#### Thing of Owner

When expressing a relationship between `x` and `y`, prefer `x` of
`y` as opposed to `y`'s `x`. `x` of `y` doesn't involve quotes
(which is especially good when , it sounds more punchy and is
therefore clearer.

#### Hedging is Giving in to Bullies

Assume good faith on the part of the reader. A reader who does not have good faith, will disregard your attempts to hedge against their criticisms. In the meantime you and all of your readers suffer through endless pleading to not be misunderstood.


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



### Declare Before Use

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


### Vertically vs Horizontal Writing

### Writing Style

 - Active vs Passive Voice
 - Offensive Wording/Pronouns

#### On Gender

Gender is a distraction, don't write him/her his/hers, it is very
rare to encounter code where the gender of the author has any
bearing on the meaning of the text. Unless it's not possible,
prefer the use of they, them or their. Ideally your text should
be about your ideas, and my impression is that this is currently
the least bad compromise of side stepping this whole topic.
