import string
import hunspell


hun = hunspell.HunSpell("build/myspell/lt_LT.dic", "build/myspell/lt_LT.aff")


def print_suggestions(text: str):
    for word in text.strip().split():
        word = word.strip(string.punctuation)
        if not hun.spell(word):
            print(word, hun.suggest(word))


text = """"""


print_suggestions(text)
