# bf-jit

A just-in-time compiling brainfuck interpreter, to be built with the RPython Toolchain.

Download the latest [pypy source](https://pypy.org/download.html), and build as follows:

    python /path/to/pypy2.7-v7.1.0-src/rpython/bin/rpython --opt=jit bf-jit.py

The resulting executable will be named bf-jit-c or similar in the current working directory.
