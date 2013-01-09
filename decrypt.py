#!/usr/bin/python

import copy
import re
from itertools import combinations

try:
    from string import maketrans
except ImportError:
    maketrans = str.maketrans

MAX_GOODNESS_LEVEL = 2  # 1-7
MAX_BAD_WORDS_RATE = 0.06

ABC = "abcdefghijklmnopqrstuvwxyz"


class WordList:
    MAX_WORD_LENGTH_TO_CACHE = 8

    def __init__(self):
        # words struct is
        # {(length,different_chars)}=[words] if len > MAX_WORD_LENGTH_TO_CACHE
        # {(length,different_chars)}=set([words and templates]) else

        self.words = {}
        for goodness in range(MAX_GOODNESS_LEVEL):
            for word in open("words/" + str(goodness) + ".txt"):
                word = word.strip()
                word_len = len(word)
                properties = (word_len, len(set(word)))

                if word_len > WordList.MAX_WORD_LENGTH_TO_CACHE:
                    words = self.words.get(properties, [])
                    words.append(word)
                    self.words[properties] = words
                else:
                    # add all possible combinations of the word and dots
                    words = self.words.get(properties, set([]))
                    for i in range(word_len + 1):
                        for dots_positions in combinations(range(word_len), i):
                            adding_word = list(word)
                            for j in dots_positions:
                                adding_word[j] = '.'

                            words.add(''.join(adding_word))
                    self.words[properties] = words

    def find_word_by_template(self, template, different_chars):
        """ Finds the word in the dict by template. Template can contain
        alpha characters and dots only """

        properties = (len(template), different_chars)
        if properties not in self.words:
            return False

        words = self.words[properties]

        if properties[0] > WordList.MAX_WORD_LENGTH_TO_CACHE:
            template = re.compile(template)

            for word in words:
                if template.match(word):
                    return True
        else:
            if template in words:
                return True
        return False


class KeyFinder:
    def __init__(self, enc_words):
        self.points_threshhold = int(len(enc_words) * MAX_BAD_WORDS_RATE)
        self.dict_wordlist = WordList()
        self.enc_words = enc_words
        self.different_chars = {}
        self.found_keys = {}  # key => bad words
        for enc_word in enc_words:
            self.different_chars[enc_word] = len(set(enc_word))

    def get_key_points(self, key):
        """ The key is 26 byte alpha string with dots on unknown places """

        trans = maketrans(ABC, key)
        points = 0

        for enc_word in self.enc_words:
            different_chars = self.different_chars[enc_word]
            translated_word = enc_word.translate(trans)

            if not self.dict_wordlist.find_word_by_template(translated_word,
                                                            different_chars):
                points += 1
        return points

    def recursive_calc_key(self, key, possible_letters, level):
        """ Returns True if solution is founded """
        print("Level: %3d, key: %s" % (level, key))

        if '.' not in key:
            points = self.get_key_points(key)
            print("Found: %s, bad words: %d" % (key, points))
            self.found_keys[key] = points

            return True

        for pos in range(len(ABC)):
            if key[pos] == ".":
                for letter in list(possible_letters[pos]):
                    new_key = key[:pos] + letter + key[pos + 1:]

                    if self.get_key_points(new_key) > self.points_threshhold:
                        possible_letters[pos].remove(letter)
                        if not possible_letters[pos]:
                            return False

        nextpos = -1
        minlen = len(ABC) + 1

        for pos in range(len(ABC)):
            if key[pos] == ".":
                if len(possible_letters[pos]) < minlen:
                    minlen = len(possible_letters[pos])
                    nextpos = pos

        for letter in list(possible_letters[nextpos]):
            new_possible_letters = copy.deepcopy(possible_letters)
            for pos in range(len(ABC)):
                new_possible_letters[pos] -= set([letter])
            new_possible_letters[nextpos] = set([letter])
            new_key = key[:nextpos] + letter + key[nextpos + 1:]
            found = self.recursive_calc_key(new_key, new_possible_letters,
                                            level + 1)
            if not found:
                possible_letters[nextpos].remove(letter)

    def find(self):
        if not self.found_keys:
            possible_letters = [set(ABC) for i in range(len(ABC))]
            self.recursive_calc_key("." * len(ABC), possible_letters, 1)
        return self.found_keys


def main():
    enc_text = open("encrypted.txt").read().lower()
    enc_words = re.findall(r"[a-z']+", enc_text)

    # skip the words with apostrophs
    enc_words = [word for word in enc_words
                      if "'" not in word and
                         len(word) <= WordList.MAX_WORD_LENGTH_TO_CACHE
                ]
    enc_words = enc_words[:200]

    print("Loaded %d words in encrypted.txt, loading dicts" % len(enc_words))

    keys = KeyFinder(enc_words).find()
    if not keys:
        print("Key not founded, try to increase MAX_BAD_WORDS_RATE")
    for key, bad_words in keys.items():
        print("Possible key: %s, bad words:%d" % (key, bad_words))
    best_key = min(keys, key=keys.get)
    print("Best key: %s, bad_words %d" % (best_key, keys[best_key]))
    trans = maketrans(ABC, best_key)
    print(open("encrypted.txt").read().translate(trans))

if __name__ == "__main__":
    try:
        #import cProfile
        #cProfile.run('main()')
        main()
    except Exception as E:
        print("Error: %s" % E)
