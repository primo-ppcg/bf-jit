import os
from rpython.rlib.jit import JitDriver
from rpython.rlib.rarithmetic import build_int, widen

r_uint16 = build_int('r_short', False, 16)

jitdriver = JitDriver(
  greens = ['pc', 'proglen', 'program'],
  reds   = 'auto'
)

# one byte instructions
ZERO, SHFT, PUTC, GETC = 0x00, 0x20, 0x40, 0x60
# two byte instructions
ADD, MUL = 0x80, 0xA0
# variable length instructions
JRZ, JRNZ = 0xC0, 0xE0

def run(program):
  pc = 0
  proglen = len(program)
  tape = bytearray("\0"*65536)
  pointer = r_uint16(0)
  pointer_rel = r_uint16(0)

  while pc < proglen:
    jitdriver.jit_merge_point(pc=pc, proglen=proglen, program=program)

    code = ord(program[pc])
    # 5-bit signed shift
    shift = (code & 0x0F) - (code & 0x10)
    pointer_rel = r_uint16(widen(pointer_rel) + shift)
    command = code & 0xE0

    if command == ADD:
      tape[pointer_rel] += ord(program[pc + 1])
      pc += 2

    elif command == JRNZ:
      jump = 0
      i = 1
      val = ord(program[pc + i])
      while val > 0x7F:
        jump = jump << 7 | (val & 0x7F)
        i += 1
        val = ord(program[pc + i])
      jump = jump << 7 | val
      i += 1
      if tape[pointer_rel] != 0:
        pc -= jump
      else:
        pc += i

    elif command == JRZ:
      jump = 0
      i = 1
      val = ord(program[pc + i])
      while val > 0x7F:
        jump = jump << 7 | (val & 0x7F)
        i += 1
        val = ord(program[pc + i])
      jump = jump << 7 | val
      i += 1
      if tape[pointer_rel] == 0:
        pc += jump + i
      else:
        pc += i
      pointer = pointer_rel

    elif command == ZERO:
      tape[pointer_rel] = 0
      pc += 1

    elif command == MUL:
      tape[pointer_rel] += tape[pointer] * ord(program[pc + 1])
      pc += 2

    elif command == PUTC:
      os.write(1, chr(tape[pointer_rel]))
      pc += 1

    elif command == GETC:
      char = os.read(0, 1)
      if char:
        tape[pointer_rel] = ord(char[0])
      else:
        # NB: EOF leaves cell unmodified
        pass
      pc += 1

    else:
      pc += 1


def parse(program, i = 0, depth = 0):
  # TODO: unroll balanced loops without PUTC, GETC, JRZ as MUL
  parsed = bytes()
  proglen = len(program)
  shift = 0
  values = {}

  while i < proglen:
    char = program[i]
    if char in '><+-[].,':
      if char == '>':
        shift += 1
        if shift > 15:
          parsed += chr(SHFT | 0x0F)
          shift -= 15
      elif char == '<':
        shift -= 1
        if shift < -16:
          parsed += chr(SHFT | 0x10)
          shift += 16
      elif char == '[':
        if program[i + 1] in '+-' and program[i + 2] == ']':
          parsed += chr(ZERO | (shift & 0x1F))
          shift = 0
          i += 2
        else:
          subprog, i, _ = parse(program, i + 1, depth + 1)
          sublen = len(subprog)
          jump = chr(sublen & 0x7F)
          sublen >>= 7
          while sublen:
            jump = chr(sublen & 0x7f | 0x80) + jump
            sublen >>= 7
          parsed += chr(JRZ | (shift & 0x1F)) + jump + subprog
          shift = 0
      elif char == ']':
        sublen = len(parsed)
        jump = chr(sublen & 0x7F)
        sublen >>= 7
        while sublen:
          jump = chr(sublen & 0x7f | 0x80) + jump
          sublen >>= 7
        return parsed + chr(JRNZ | (shift & 0x1F)) + jump, i, depth - 1
      elif char == '.':
        parsed += chr(PUTC | (shift & 0x1F))
        shift = 0
      elif char == ',':
        parsed += chr(GETC | (shift & 0x1F))
        shift = 0
      else:
        value = 44 - ord(char)
        while i+1 < proglen and program[i+1] in '+-':
          i += 1
          value += 44 - ord(program[i])
        parsed += chr(ADD | (shift & 0x1F)) + chr(value & 0xFF)
        shift = 0
    i += 1

  return parsed, i, depth


def main(argv):
  from rgetopt import gnu_getopt, GetoptError

  try:
    optlist, args = gnu_getopt(argv[1:], 'hc:', ['help', 'code='])
  except GetoptError as ex:
    os.write(2, ex.msg + '\n')
    return 1

  source = ''
  for opt, val in optlist:
    if opt == '-c' or opt == '--code':
      source = val
    elif opt == '-h' or opt == '--help':
      display_usage(argv[0])
      display_help()
      return 1

  if source == '':
    try:
      with open(args[0]) as file:
        source = file.read()
    except IndexError:
      display_usage(argv[0])
      return 1
    except IOError:
      os.write(2, 'File not found: %s\n'%args[0])
      return 1

  program, i, depth = parse(source)
  if depth > 0:
    os.write(2, 'Unmatched `[` in source\n')
    return 1
  elif depth < 0:
    os.write(2, 'Unmatched `]` in source\n')
    return 1
  run(program)

  return 0


def display_usage(name):
  os.write(2, 'Usage: %s [-h] (<file> | -c <code>)\n'%name)

def display_help():
  os.write(2, '''
A just-in-time compiling interpreter for the brainfuck programming language.

Arguments:
  file          a brainfuck script file to execute

Options:
  -c, --code=   a string of instructions to be executed
                if present, the file argument will be ignored
  -h, --help    display this message
''')


def target(*args):
  return main
