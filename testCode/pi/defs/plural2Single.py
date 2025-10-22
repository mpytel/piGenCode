# plural2Single functions - synced from existing code
from pi.piClasses.piPiClasses import PiPiClasses


def plural2Single(pluralWord, piPiClasses: PiPiClasses):
    '''Returns singuler version of a plural type name.
        simple removem es or s'''

    piIndexerTypes = piPiClasses.piIndexerTypes
    piIndexerSTypes = piPiClasses.piIndexerSTypes
    if pluralWord in piIndexerSTypes:
        #print('p0')
        singleWord = piIndexerTypes[piIndexerSTypes.index(pluralWord)]
    elif pluralWord in piIndexerTypes:
        #print('p1',pluralWord, piIndexerTypes)
        singleWord = pluralWord
    else:
        #print('p2',pluralWord, piIndexerTypes)
        import inflect as infl
        p = infl.engine()
        singleWord = p.singular_noun(pluralWord)
    return singleWord
