#!/usr/bin/python

import random
import string

abc = "abcdefghijklmnopqrstuvwxyz"

key = list(abc)
random.shuffle(key)
key = "".join(key)

text = open('text.txt').read().lower()

trans = string.maketrans(abc, key)

print text.translate(trans)
