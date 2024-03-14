#!/usr/bin/env python3
# -*- coding: iso-8859-13 -*-
#
# Autorius: Albertas Agejevas, 2003
# Koregavo: Laimonas V„bra, 2010-2016
#
# Veikia su Python v2.3+, v3.0+
#
"""
ispell-lt projekto/„odyno „rankis.
Suglaud„ia/suskliaud„ia pasikartojan„ius „od„ius (suliejant j„ afiks„
„ymas, jei toki„ turi), o taip pat prie„d„linius veiksma„od„ius, pvz.:
    pa|eina, nu|eina, at|eina, ... -> eina/bef...

ir i„veda surikiuot„ „od„i„ s„ra„„, tinkam„ galutiniam „odynui.

„od„iai skliaud„iami tik suderinamose (kalbos dali„) grup„se (dabar
tai: veiksma„od„iai, b„dvard„iai ir lik„).

Naudojimas:
    ./sutrauka „odynas.txt > sutraukta.txt
    cat „odynas.txt | ./sutrauka > sutraukta.txt

"""
import os
import sys
import locale
import fileinput
from itertools import chain


enc = "ISO8859-13"
loc = "lt_LT" + "." + enc

# Windows setlocale() nepriima POSIX lokal„s
if os.name is "nt":
    loc = "Lithuanian"

_setlocale_failed = False
try:
    locale.setlocale(locale.LC_COLLATE, loc)
except:
    _setlocale_failed = True
    sys.stderr.write(
        "Could not set locale '%s', default: '%s'. "
        "Won't be able to sort dictionary words correctly.\n"
        % (loc, locale.getdefaultlocale())
    )

# Nuo v2.4 set tipai built-in, o sets modulis deprecated nuo v2.6
if sys.version_info < (2, 4):
    from sets import Set

    set = Set

# Py2 ir Py3 dict iteratori„ suderinimas
if sys.version_info < (3,):
    items = dict.iteritems
else:
    items = dict.items


# global stat vars: constringed words and saved bytes count
c_wcount = 0
c_bsaved = 0

prefixes = (
    ("a", "ap"),
    ("a", "api"),
    ("b", "at"),
    ("b", "ati"),
    ("c", "„"),
    ("d", "i„"),
    ("e", "nu"),
    ("f", "pa"),
    ("g", "par"),
    ("h", "per"),
    ("i", "pra"),
    ("j", "pri"),
    ("k", "su"),
    ("l", "u„"),
    ("m", "apsi"),
    ("n", "atsi"),
    ("o", "„si"),
    ("p", "i„si"),
    ("q", "nusi"),
    ("r", "pasi"),
    ("s", "parsi"),
    ("t", "persi"),
    ("u", "prasi"),
    ("v", "prisi"),
    ("w", "susi"),
    ("x", "u„si"),
)


def _stats(word, wflags, swflags, pverb=False):
    global c_wcount, c_bsaved
    # Statistika (sutaupyta „od„i„ ir vietos).
    #
    # Kiek sutaupoma vietos (bcount) suskliaud„iant „od„:
    # „od„io ilgis + bendr„ „ym„ kiekis + _papildomai_ 1 arba 2 baitai,
    # priklausomai nuo varianto:
    #   - kai „odis be „ym„ arba prie„d. veiksma„odis (pverb): '\n' (1)
    #   - visais kitais atvejais sutaupoma: '/', '\n' (2)
    c_wcount += 1

    if pverb or not wflags:
        le = 2
    else:
        le = 1

    c_bsaved += len(word) + len(wflags & swflags) + le


def _msg(s, *args):
    if args:
        s = s % args
    sys.stderr.write(s)
    sys.stderr.flush()


def _progress(i, step=5000):
    if i % step == 0:
        _msg(".")


def _sort(wlist):
    if _setlocale_failed:
        wlist.sort()
    elif sys.version_info < (2, 4):
        wlist.sort(locale.strcoll)
    elif sys.version_info < (3,):
        wlist.sort(cmp=locale.strcoll)
    elif sys.version_info >= (3,):
        from functools import cmp_to_key

        wlist.sort(key=cmp_to_key(locale.strcoll))


def sutrauka(lines, outfile=sys.stdout, myspell=True):
    i = 0
    adjes = {}
    verbs = {}
    words = {}
    wcount = 0

    # Skliaud„iam„j„ „od„i„ klas„s (pagal afiks„ „ym„ rinkinius):
    vflags = set("TYEPRO")  # verb flags
    aflags = set("AB")  # adjective flags

    _msg("\n--- %s %s\nReading ", sys.argv[0], "-" * (55 - len(sys.argv[0])))

    for line in lines:
        _progress(lines.lineno())

        # Ignoruojamos tu„„ios ir komentaro eilut„s.
        line = line.split("#")[0]
        line = line.strip()
        if not line:
            continue

        wcount += 1

        # Eilut„ skeliama „ „od„ ir jo „ym„ rinkin„.
        sp = line.split("/")
        word = sp[0]
        if len(sp) > 1:
            wflags = set(sp[1])
        else:
            wflags = set()

        # Veiksma„od„iai ir b„dvard„iai „ atskirus dict.
        if vflags & wflags:
            d = verbs
        elif aflags & wflags:
            d = adjes
        else:
            d = words

        # „odis pridedamas „ dict arba jei jau yra -- suliejamos „ymos
        swflags = d.get(word)  # stored word flags
        if swflags is not None:
            _stats(word, wflags, swflags)
            swflags.update(wflags)
        else:
            d[word] = wflags

    _msg("\nProcessing ")

    # Prie„d„lini„ veiksma„od„i„ suskliaudimas.
    # XXX: d„l skirtingo py2 ir py3 dict vidinio eili„kumo, skiriasi ir
    # suglaudinimo rezultatas.
    # Nei„spr„sta problema: priklausomai nuo to, kurie „od„iai ir kokiu
    # eili„kumu i„renkami, skliaud„iant sudurtini„ prie„d. veiksma„od„ius,
    # i„ dict pa„alinamas skliaud„iamasis „odis ir tai v„liau nebeleid„ia
    # suskliausti kit„ „od„i„.
    # Pvz.:
    #    su|pana„inti -> pa|na„inti/k -> na„inti/fk
    # vs
    #    pa|na„inti -> na„inti/f;
    #    (v„liau 'supana„inti' nebesuskliaud„iamas, nes neb„ra 'pana„inti')
    #
    # Norint vieningo rezultato su py2/py3, reikia surikiuoti s„ra„„:
    #    lverbs = list(verbs); lverbs.sort()
    # nors problema i„lieka: algoritmas ne visai korekti„kai suskliaud„ia
    # sudurtini„ prie„d„li„ veiksma„od„ius.
    for word in list(verbs):
        i += 1
        _progress(i)

        # „od„io afiks„ „ym„ rinkinys.
        wflags = verbs[word]

        # Kiekvienam „odyno „od„iui derinami/tikrinami visi prie„d„liai.
        for pflag, pref in prefixes:

            if word.startswith(pref):
                # Jei pref sangr„„inis prie„d„lis, tai „odis atmetus paprast„j„
                # (nesangr„„in„) prie„d„l„, pvz.: i„{si}|urbia -> siurbia.
                # Kai toks „odis yra „odyne, tai situacija netriviali, nes
                # „odyne yra trys „od„io formos: su prie„d„liu, be prie„d„lio
                # ir be sangr„„inio prie„d„lio.  Tampa nebeai„ku kok„ prie„d„l„
                # (sangr„„in„ ar ne) ir kokiam „od„iui pritaikyti; toki„
                # „od„i„ savaime suskliausti ne„manoma, pvz.:
                #     i„{si}|urbia, siurbia, urbia (i„|siurbia ar i„si|urbia?)
                #     at{si}|joja, sijoja, joja;   (at|sijoja ar atsi|joja?)
                #
                # Kol kas tokie „od„iai neskliaud„iami.
                if pref.endswith("si"):
                    # word without reflexive prefix part
                    wrp_word = word[len(pref) - 2 :]
                else:
                    wrp_word = None

                # „odis be prie„d„lio, pvz.: per|„oko -> „oko.
                # (word without prefix)
                wp_word = word[len(pref) :]
                wp_wflags = verbs.get(wp_word)

                if wp_wflags is not None and wrp_word not in verbs:
                    # Skliaud„iant prie„d„linius veiksma„od„ius su /N /S /X
                    # afiks„ „ymomis, d„l ispell apribojimo jungiant afiksus,
                    # prarandamos kelios prie„d„lin„s formos, pvz:
                    #
                    #   pavartyti/X  >  te|pa|vartyti, tebe|pa|vartyti,
                    #                   be|pa|vartyti, ...
                    # vs
                    #    vartyti/Xf  >  tevartyti, tebevartyti, bevartyti, ...
                    #
                    # Susitaikius su vykstan„iu prie„d„lini„ form„:
                    #  [/N /S /X afiksai] {prie„d„lis} „odis
                    # praradimu, „odynas suglaudinamas vir„ 50 kB.
                    #
                    # ARBA atvirk„„iai: siekiant, kad neb„t„ praradim„, kaip
                    # tik nereik„t„ toki„ „od„i„ (jei prie„d„linis „odis turi
                    # /S /X /N „ymas) glaudinti.
                    _stats(word, wflags, wp_wflags, pverb=True)

                    # Suliejamos afiks„ „ymos ir pridedama prie„d„lio „yma.
                    wp_wflags.update(wflags)
                    wp_wflags.add(pflag)

                    # „odis sukliaustas (prie „akninio „od„io sulietos
                    # „ymos, prid„ta prie„d„lio afikso „yma).  Pa„aliname
                    # prie„d„lin„ „od„ i„ 'verbs' dict ir baigiame
                    # prie„d„li„ cikl„, nes prie„d„liai unikal„s ir „od„io
                    # prad„ia nebegali sutapti su jokiu kitu prie„d„liu.
                    del verbs[word]
                    break

    # beafiksini„ „od„i„ pa„alinimas, jei jie yra kitose afiksini„ klas„se
    for word, flags in items(words.copy()):
        if not flags and (word in verbs or word in adjes):
            _stats(word, flags, set())
            # _msg("Deleting %s\n", word)
            del words[word]

    wlist = []
    NS = set("NS")
    for word, flags in chain(items(words), items(verbs), items(adjes)):
        if flags:
            # /S perdengia /N, tod„l abiej„ nereikia
            if NS < flags:
                flags.remove("N")
            fl = list(flags)
            fl.sort()
            word += "/" + "".join(fl)

        wlist.append(word + "\n")

    _sort(wlist)

    _msg(
        " done.\nWords before: %d, words after: %d.\n"
        "(words constringed: %d, bytes saved: %d)\n%s\n",
        wcount,
        len(wlist),
        c_wcount,
        c_bsaved,
        "-" * 60,
    )

    # myspell'o „odyno prad„ioje -- „od„i„ kiekis.
    if myspell:
        outfile.write(len(wlist) + "\n")

    outfile.writelines(wlist)


if __name__ == "__main__":
    outfile = sys.stdout
    # Nuo v2.5+ fileinput galima nurodyti openhook'„ (dekodavimas i„
    # norimos koduot„s). Aktualu tik py3 (py2 dirba su byte strings;
    # perkodavimas „ unikod„ neb„tinas), ta„iau openhook'as neveikia
    # su stdin.
    if sys.version_info >= (3,):
        import io

        if not sys.argv[1:]:
            # jei n„ra argument„, tai duomenys i„ stdin
            sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding=enc)
        outfile = io.TextIOWrapper(sys.stdout.buffer, encoding=enc)
        _fileinput = fileinput.input(openhook=fileinput.hook_encoded(enc))
    else:
        _fileinput = fileinput.input()

    sutrauka(_fileinput, outfile=outfile, myspell=False)
