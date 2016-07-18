from nltk.corpus.reader.childes import CHILDESCorpusReader
import sys, codecs
import pdb
from collections import Counter
from depedit import run_depedit

"""
Morphdep format:
x[0]: word
x[1]: POS
x[2]: token index
x[3]: head index
x[4]: dep label

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


def to_conll(morphdep,debug=False):
    """
    Receives a sentence in morphdep format, return CoNLL style.
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
    
    output = []
    offset = 1
    added_indices = []
    for index,word in enumerate(morphdep):
        if None in word:
            return None
        pos = word[1]
        if pos in ['+...', '+/.']:
            return None
        elif pos in ['prep:pro', 'acc:pro', 'acc:det']:
            word1 = word[0].split('&')[0]
            word2 = '&'.join(word[0].split('&')[1:])
            if word2 == "":
                word2 = "empty_pronoun"
            if pos == 'acc:pro':
                pos1 = 'acc'
                pos2 = 'pro'
                dep1 = 'APREP'
            elif 'prep:pro':
                pos1 = 'prep'
                pos2 = 'pro'
                dep1 = 'APREP'
            elif pos == 'acc:det':
                pos1 = 'acc'
                pos2 = 'det'
                dep1 = 'APREP'
            output.append([index+offset,word1,word1,pos1,pos1,'_',word[3],word[4],'_','_'])
            output.append([index+offset+1,word2,word2,pos2,pos2,'_',index+offset,dep1,'_','_'])
            added_indices.append((index+offset,1,0))  # (original token number after which the addition occured, how many tokens were added, which of them is the head (0,1,2 etc.))
            offset += 1
        elif pos == 'n:det':  # a compound with a determiner
            sub_words = word[0].split('+')
            if len(sub_words) != 3 or sub_words[1] != 'ha':
                sys.stderr.write('Unencountered compound case\n')
                pdb.set_trace()
            else:
                output.append([index+offset,sub_words[0],sub_words[0],'n','n','_',word[3],word[4],'_','_'])
                output.append([index+offset+1,sub_words[1],sub_words[1],'det','det','_',index+offset+2,'det','_','_'])
                output.append([index+offset+2,sub_words[2],sub_words[2],'n','n','_',index+offset,'nmod','_','_'])
                added_indices.append((index+offset,2,0))
                offset += 2
        elif '+' in word[0]:  # noun compound
            sub_words = word[0].split('+')
            output.append([index+offset,sub_words[0],sub_words[0],'n','n','_',\
                           word[3],word[4],'_','_'])
            for c,w in enumerate(sub_words[1:]):
                output.append([index+offset+c+1,w,w,'n','n','_',index+offset,'nmod','_','_'])
            added_indices.append((index+offset,len(sub_words)-1,0))
            offset += len(sub_words) - 1
        elif '_' in word[0]: # MWE
            sub_words = word[0].split('_')
            output.append([index+offset,sub_words[0],sub_words[0],'X','X','_',word[3],word[4],'_','_'])
            for c,w in enumerate(sub_words[1:]):
                output.append([index+offset+c+1,w,w,'X','X','_',index+offset,'mwe','_','_'])
            added_indices.append((index+offset,len(sub_words)-1,0))
            offset += len(sub_words) - 1
        else:
            output.append([index+offset,word[0],word[0],pos,pos,'_',word[3],word[4],'_','_'])

    output = fix_offsets(output,added_indices)
    return output


def process_dir(dir,output_file):
    """
    Processes all the xmls in dir and its sub-directories.
    """
    he = CHILDESCorpusReader(dir,'.*-gold.xml')
    f = open(output_file,'w')
    for fileid in he.fileids():
        for ind,morph_dep in enumerate(he.morph_deps(fileid,speakers='is_adult')):
            conll_lines = to_conll(morph_dep)
            if conll_lines:
                f.write('#'+fileid+','+str(ind)+'\n')
                for line in conll_lines:
                    for field in line:
                        if isinstance(field,unicode):
                            f.write(field.encode("utf-8"))
                        else:
                            f.write(str(field))
                        f.write('\t')
                    f.write('\n')
                f.write('\n')
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
    


