
## Parallel Build Steps

For now the build is completely linear, but eventually we may want to speed
things up. This is something to keep in mind when making design decisions

A very interesting approach to dealing with log output produced by parallel
build steps: https://apenwarr.ca/log/20181106

Long story short, the log output of a build step is persisted and only
written to stdout incrementally if it belongs the first and lowest level
step.

~~~
t01  A: redo J
t02  J:   ...stuff...
t03  J:   redo X
t04  X:     redo Q
t05  Q:       ...build Q...
t06  X:     ...X stuff...
t06  J:   redo Y
t06  Y:     redo Q
t07  Y:     ...Y stuff...
t08  J:   redo Z
t08  Z:     redo Q
t08  Z:     ...Z stuff...
t08  J:   ...stuff...
t08  A: exit 0
~~~

Notice that the output which belonged to the concurrently running steps was
buffered and written all at once only after steps which were started
earlier or as its own dependencies were completed.
