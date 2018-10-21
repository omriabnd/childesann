from nltk.corpus.reader.childes import CHILDESCorpusReader
import sys, codecs
import pdb
from collections import Counter
from depedit import run_depedit


FIELD_NAMES = ['ID', 'FORM', 'LEMMA', 'UPOSTAG', 'XPOSTAG', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC']

"""
CoNLL format: (from http://universaldependencies.org/format.html) 
'#' for comments
ID: Word index, integer starting at 1 for each new sentence; may be a range for tokens
with multiple words.
FORM: Word form or punctuation symbol.
LEMMA: Lemma or stem of word form.
UPOSTAG: Universal part-of-speech tag drawn from our revised version of the Google
universal POS tags.
XPOSTAG: Language-specific part-of-speech tag; underscore if not available.
FEATS: List of morphological features from the universal feature inventory or from a defined
language-specific extension; underscore if not available.
HEAD: Head of the current token, which is either a value of ID or zero (0).
DEPREL: Universal Stanford dependency relation to the HEAD (root iff HEAD = 0) or a
defined language-specific subtype of one.
DEPS: List of secondary dependencies (head-deprel pairs).
MISC: Any other annotation.
"""

stringify = lambda L: [(str(x) if ind in [0,6] else x) for ind,x in enumerate(L)]

def check_inds(parsed_sent):
    """
    Checks that the parsed sentence has all the indices
    """
    indices = [int(x[0]) for x in parsed_sent]
    return set(indices) == set(range(1,max(indices)+1))
    

def retokenize(conll_sent,debug=False):
    """
    Receives a sentence in conll format, return CoNLL style.
    """
    def fix_offsets(output,added_indices):
        """
        Fixes the head indices, given the added indices.
        """
        fixed_set = set()
        for added in added_indices:
            fixed_set.update([added[0]+c for c in range(added[1]+1)])
            fixed_set.remove(added[0]+added[2])
        for added in added_indices:
            for ind in range(len(output)):
                if output[ind][0] in fixed_set:
                    continue
                if output[ind][6] > added[0]:
                    output[ind][6] += added[1]
                elif output[ind][6] == added[0]:
                    output[ind][6] += added[2]
        return output

    if conll_sent.strip() == '':
        return None
    output = []
    offset = 1
    added_indices = []
    for index,word in enumerate(conll_sent.split('\n')):
        fields = dict(zip(FIELD_NAMES,word.split('\t')))
        if 'ID' in fields:
            if '-' in fields['ID']:
                continue
        pos = fields['XPOSTAG']
        fields['HEAD'] = int(fields['HEAD'])
        
        if pos in ['+...', '+/.']:
            return None
        elif pos in ['prep:pro', 'acc:pro', 'acc:det']:
            word1 = fields['FORM'].split('&')[0]
            word2 = '&'.join(fields['FORM'].split('&')[1:])
            if word2 == "":
                word2 = "empty_pronoun"
            if pos == 'acc:pro':
                pos1 = 'acc'
                pos2 = 'pro'
                dep1 = 'APREP'
            elif pos == 'prep:pro':
                pos1 = 'prep'
                pos2 = 'pro'
                dep1 = 'APREP'
            elif pos == 'acc:det':
                pos1 = 'acc'
                pos2 = 'det'
                dep1 = 'APREP'
            output.append([index+offset,word1,word1,pos1,pos1,'_',fields['HEAD'],fields['DEPREL'],'_','_'])
            output.append([index+offset+1,word2,word2,pos2,pos2,'_',index+offset,fields['DEPREL'],'_','_'])
            added_indices.append((index+offset,1,0))  # (original token number after which the addition occured, how many tokens were added, which of them is the head (0,1,2 etc.))
            offset += 1
        elif pos == 'n:det':  # a compound with a determiner
            sub_words = fields['FORM'].split('+')
            if len(sub_words) != 3 or sub_words[1] != 'ha':
                sys.stderr.write('Unencountered compound case\n')
                sys.exit(-1)
            else:
                output.append([index+offset,sub_words[0],sub_words[0],'n','n','_',fields['HEAD'],fields['DEPREL'],'_','_'])
                output.append([index+offset+1,sub_words[1],sub_words[1],\
                               'det','det','_',index+offset+2,'det','_','_'])
                output.append([index+offset+2,sub_words[2],sub_words[2],\
                               'n','n','_',index+offset,'nmod','_','_'])
                added_indices.append((index+offset,2,0))
                offset += 2
        elif '+' in fields['FORM']:  # noun compound
            sub_words = fields['FORM'].split('+')
            output.append([index+offset,sub_words[0],sub_words[0],'n','n','_',fields['HEAD'],fields['DEPREL'],'_','_'])
            for c,w in enumerate(sub_words[1:]):
                output.append([index+offset+c+1,w,w,'n','n','_',index+offset,'nmod','_','_'])
            added_indices.append((index+offset,len(sub_words)-1,0))
            offset += len(sub_words) - 1
        elif '_' in fields['FORM']: # MWE
            sub_words = fields['FORM'].split('_')
            output.append([index+offset,sub_words[0],sub_words[0],'X','X','_',fields['HEAD'],fields['DEPREL'],'_','_'])
            for c,w in enumerate(sub_words[1:]):
                output.append([index+offset+c+1,w,w,'X','X','_',index+offset,'mwe','_','_'])
            added_indices.append((index+offset,len(sub_words)-1,0))
            offset += len(sub_words) - 1
        else:
            output.append([index+offset,fields['FORM'],fields['LEMMA'],pos,pos,'_',fields['HEAD'],fields['DEPREL'],'_','_'])

    output = fix_offsets(output,added_indices)
    if not check_inds(output):
        return conll_sent
    else:
        return '\n'.join(['\t'.join(stringify(x)) for x in output])


def process_dir(dir,output_file):
    """
    Processes all the xmls in dir and its sub-directories.
    """
    he = CHILDESCorpusReader(dir,'.*.xml')
    f = open(output_file,'w')
    for fileid in he.fileids():
        conllu_parse = []
        for ind,parse_line in enumerate(he.conllu_parses(fileid,speakers='is_adult',skip_unanalyzed_tokens=True)):
            f.write('#'+fileid+','+str(ind)+'\n')
            parse_line = retokenize(parse_line)
            if parse_line:
                f.write(parse_line.encode("utf-8"))
                f.write('\n\n')
    f.close()

###############
# MAIN        #
###############

if __name__ == "__main__":
       
    if len(sys.argv) != 3:
        print('Usage query_corpus.py <directory> <output>')
        sys.exit(-1)

    #default directory: '/cs/++/staff/oabend/nltk_data/corpora/childes/data-xml/'
    process_dir(sys.argv[1],sys.argv[2])



