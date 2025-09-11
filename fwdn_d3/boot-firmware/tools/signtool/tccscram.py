##
# TCC Scrambler
#
import ctypes
import os

scramlib = ctypes.cdll.LoadLibrary(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib", "tccscram.so"))

def tccscram(buf):
    char_array = ctypes.c_char * len(buf)
    scramlib.tccscram_encrypt(char_array.from_buffer(buf), len(buf))
    return buf
