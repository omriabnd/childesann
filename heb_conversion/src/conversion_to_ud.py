import sys, pdb, re
import utils
from depedit import run_depedit
from collections import defaultdict

TEMP_FILE = 'temp.temp'


def fix_coordination(sent):
    """
    Receive a coordination structure where the coordinating conjunction is the head.
    Returns a structure where the head is the first, and all other words are dependent on it.
    """
    for w in sent.bfs():
        if w.get_field('upos') == 'conj':
            conjuncts = sent.get_deps(w.get_field('index'),['COORD']) + [w]
            conjuncts = sorted(conjuncts,key=lambda x:x.get_field('index'))
            
            # assign the first as the head
            sent.set_field(conjuncts[0].get_field('index'),'head_index',w.get_field('head_index'))
            sent.set_field(conjuncts[0].get_field('index'),'deprel',w.get_field('deprel'))
            
            # assign the others as its dependents
            for c in conjuncts[1:]:
                sent.set_field(c.get_field('index'),'head_index',conjuncts[0].get_field('index'))
                if c.get_field('index') == w.get_field('index'):
                    sent.set_field(c.get_field('index'),'deprel','cc')
                else:
                    sent.set_field(c.get_field('index'),'deprel','conj')
    return sent


def fix_flat_structure(sent,label,first_or_last,new_label_head,new_label_others):
    """
    Receive a structure where the last word is the head, and
    change it to the first word being the head.
    """
    structs = defaultdict(list)
    for w in sent.word_range(None):
        if w.get_field('deprel') == label:
            structs[w.get_field('head_index')].append(w)
    for head_ind,words in structs.items():
        head_word = sent.word_by_index(head_ind)
        struct_words = sorted(words + [head_word],key=lambda x:x.get_field('index'))
        if not first_or_last:
            struct_words = reversed(struct_words)
        
        struct_words = list(struct_words)
        # assign the first as the head
        sent.set_field(struct_words[0].get_field('index'),'head_index', head_word.get_field('head_index'))
        sent.set_field(struct_words[0].get_field('index'),'deprel',head_word.get_field('deprel'))
        
        # assign the others as its dependents
        for c in struct_words[1:]:
            sent.set_field(c.get_field('index'),'head_index',struct_words[0].get_field('index'))
            if c.get_field('index') == head_word.get_field('index'):
                sent.set_field(c.get_field('index'),'deprel',new_label_head)
            else:
                sent.set_field(c.get_field('index'),'deprel',new_label_others)

    return sent


    


if __name__ == '__main__':
    pattern = re.compile('_')
    if len(sys.argv) != 3:
        print('Usage: conversion_to_ud.py <conll-style input> <depedit config>')
        sys.exit(-1)
    infile = open(sys.argv[1])
    config_file = open(sys.argv[2])
    temp_file = open(TEMP_FILE,'w')

    # fix coordination structures
    for return_type, sent in utils.read_sents_from_file(infile):
        if return_type == 'SENT':
            labels = [w.get_field('deprel') for w in sent.word_range(None)]
            pos = [w.get_field('upos') for w in sent.word_range(None)]
            if 'COORD' in labels:
                sent = fix_coordination(sent)
            if 'ENUM' in labels:
                sent = fix_flat_structure(sent,'ENUM',True,'list','list')
            if 'ACOP' in labels:
                sent = fix_flat_structure(sent,'ACOP',False,'aux','nsubj')
            temp_file.write(str(sent)+'\n\n')
        else:
            temp_file.write(str(sent)+'\n')
    temp_file.close()
    
    infile = open(TEMP_FILE)
    for t, line in run_depedit(infile, config_file):
        print(line.strip())


