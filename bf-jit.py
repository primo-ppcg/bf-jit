import os
from rpython.rlib.jit import JitDriver

jitdriver = JitDriver(
  greens = ['pc', 'proglen', 'program'],
  reds   = ['pointer', 'pointer_rel', 'tape'])

# one byte instructions
MV, SHFT, PUTC, GETC = 0x00, 0x20, 0x40, 0x60
# two byte instructions
ADD, MUL = 0x80, 0xA0
# three byte instructions
JRZ, JRNZ = 0xC0, 0xE0

def mainloop(program):
  pc = 0
  proglen = len(program)
  tape = bytearray("\0"*65536)
  pointer = 0
  pointer_rel = 0

  while pc < proglen:
    jitdriver.jit_merge_point(
      pc=pc, proglen=proglen, program=program,
      pointer=pointer, pointer_rel=pointer_rel, tape=tape
    )

    code = ord(program[pc])
    # 5-bit signed shift
    shift = (code & 0x0F) - (code & 0x10)
    pointer_rel = pointer_rel + shift & 65535
    command = code & 0xE0

    if command == ADD:
      tape[pointer_rel] += ord(program[pc + 1])
      pc += 2

    elif command == JRNZ:
      if tape[pointer_rel] != 0:
        pc -= ord(program[pc + 1]) << 8 | ord(program[pc + 2])
      else:
        pc += 3
      pointer = pointer_rel

    elif command == JRZ:
      if tape[pointer_rel] == 0:
        pc += ord(program[pc + 1]) << 8 | ord(program[pc + 2])
      else:
        pc += 3
      pointer = pointer_rel

    elif command == MV:
      pc += 1
      pointer = pointer_rel

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


def parse(program, i = 0):
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
        if program[i + 1] in '-+' and program[i + 2] == ']':
          parsed += chr(MV | (shift & 0x1F)) + chr(MUL) + chr(255)
          shift = 0
          i += 2
        else:
          subprog, i = parse(program, i + 1)
          sublen = len(subprog)
          jump = chr((sublen + 3) >> 8) + chr((sublen + 3) & 0xFF)
          parsed += chr(JRZ | (shift & 0x1F)) + jump + subprog
          shift = 0
      elif char == ']':
        sublen = len(parsed)
        jump = chr(sublen >> 8) + chr(sublen & 0xFF)
        return parsed + chr(JRNZ | (shift & 0x1F)) + jump, i
      elif char == '.':
        parsed += chr(PUTC | (shift & 0x1F))
        shift = 0
      elif char == ',':
        parsed += chr(GETC | (shift & 0x1F))
        shift = 0
      else:
        value = 44 - ord(char)
        while i < proglen and program[i+1] in '+-':
          i += 1
          value += 44 - ord(program[i])
        parsed += chr(ADD | (shift & 0x1F)) + chr(value & 0xFF)
        shift = 0
    i += 1

  return parsed, i

def run(fp):
  program_contents = ''
  while True:
    read = os.read(fp, 4096)
    if len(read) == 0:
      break
    program_contents += read
  os.close(fp)
  program, i = parse(program_contents)
  mainloop(program)

def main(argv):
  filename = ''
  try:
    filename = argv[1]
    fp = os.open(filename, os.O_RDONLY, 0777)
  except IndexError:
    os.write(2, 'Usage: %s program.bf'%argv[0])
    return 1
  except OSError:
    os.write(2, 'File not found: %s'%filename)
    return 1

  run(fp)
  return 0

def target(*args):
  return main

if __name__ == '__main__':
  import sys
  main(sys.argv)