__author__ = 'stav.yardeni'


import sys, pdb, re
import utils
from collections import defaultdict

TEMP_FILE = 'temp.temp'


def fix_coordination(sent):
    """
    Receive a coordination structure where the head of each word is right before the "and"
    Returns a structure where the head is the first, and all other words are dependent on it.
    """
    for w in sent.bfs():
        if w.get_field('deprel') == 'conj':
            father_index= w.get_field('head_index')
            conjuncts = sent.get_deps(w.get_field('index'),'conj')+[w]
            for c in conjuncts:
                sent.set_field(c.get_field('index'),'head_index',father_index)

    return sent

if __name__ == '__main__':
    pattern = re.compile('_')
    if len(sys.argv) != 2:
        print('Usage: Coordination_Postprocessing.py <conll-style input>')
        sys.exit(-1)
    infile = open(sys.argv[1])
    # config_file = open(sys.argv[2])
    temp_file = open(TEMP_FILE,'w')

    # fix coordination structures
    for return_type, sent in utils.read_sents_from_file(infile):
        if return_type == 'SENT':
            labels = [w.get_field('deprel') for w in sent.word_range(None)]
            pos = [w.get_field('upos') for w in sent.word_range(None)]
            if 'conj' in labels:
                sent = fix_coordination(sent)
            temp_file.write(str(sent)+'\n')
        else:
            temp_file.write(str(sent)+'\n')
    temp_file.close()

    infile = open(TEMP_FILE)
    data = infile.read()
    outfile=open("/cs/guest/stav.yardeni/fork/childesann/eng_conversion/childes_conll_eng/Eve.Conll.Converted.Postprocessed.coordination.txt", "w")

    for line in data:
        outfile.write(line)
    outfile.close()