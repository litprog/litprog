```python
# lp_def: aaaa
aaaa = 1111
# lp_dep: bbbb
AAAA = 9999
```

```python
# lp_def: bbbb
bbbb = 2222
# lp_dep: cccc
```

```python
# lp_addto: aaaa
BBBB = 2.22
```

```python
# lp_file: examples/test_lp_deps.py
# lp_def: outfile
# lp_dep: aaaa, bbbb
# lp_dep: bbbb
# ----------------------
```

```python
# lp_def: cccc
cccc = 3333
```

```python
# lp_addto: cccc
CCCC = 3.33
```

