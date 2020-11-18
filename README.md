# bf-jit

A just-in-time compiling brainfuck interpreter, to be built with the RPython Toolchain.

Download the latest [pypy source](https://www.pypy.org/download.html#source), and build as follows:

`python /path/to/pypy3.7-v7.3.2-src/rpython/bin/rpython --opt=jit bf-jit.py`

The resulting executable will be named bf-jit-c or similar in the current working directory.
