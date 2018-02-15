'''
Created on Mar 11, 2016

@author: jcheung
'''

__count_noun_f = './external/count_nouns.txt'
__mass_noun_f = './external/mass_nouns.txt'

__count_nouns = set()
with open(__count_noun_f) as f:
    for n in f:
        __count_nouns.add(n.strip())
 

__mass_nouns = set()
with open(__mass_noun_f) as f:
    for n in f:
        __mass_nouns.add(n.strip())

def countability(n):
    '''
    returns one of 'count', 'mass', 'either', 'unknown'
    
    '''
    count = (n in __count_nouns)
    mass = (n in __mass_nouns)
    
    if count and not mass:
        return 'count'
    elif not count and mass:
        return 'mass'
    elif count and mass:
        return 'either'
    return 'unknown'

if __name__ == '__main__':
    only_mass = __mass_nouns.intersection(__count_nouns)
    print only_mass
    print len(only_mass)
    