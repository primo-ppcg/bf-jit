# bf-jit

A just-in-time compiling interpreter for the [brainfuck](https://esolangs.org/wiki/Brainfuck) programming language, to be built with the RPython Toolchain.

Download the latest [pypy source](https://www.pypy.org/download.html#source), and build as follows:

`python2 /path/to/pypy3.10-v7.3.13-src/rpython/bin/rpython --opt=jit bf-jit.py`

Build dependencies are listed separately: https://doc.pypy.org/en/latest/build.html#install-build-time-dependencies

The resulting executable will be named bf-jit-c or similar in the current working directory. It can also be built without JIT support by removing the `--opt=jit` option. Build time will be shorter, and the resulting executable smaller.

Note that RPython is a dialect of python2, and accordingly the version of python/pypy used for the build must be 2.7. If python2 is no longer available for your system, it may be easiest to use a pre-built pypy2.7: https://www.pypy.org/download.html
