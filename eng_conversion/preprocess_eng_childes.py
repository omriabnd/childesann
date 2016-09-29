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


def to_conll(morphdep, debug=False):
    """
    Receives a sentence in morphdep format, return CoNLL style.
    """

    def fix_offsets(output, fixed_set, index_map):
        """
        Fixes the head indices, given the added indices.
        1. go over all words execpt those with indices in fixed_set
        2. change their head_index to index_map[head_index]
        """
        for word in output:
            if word[0] in fixed_set:
                continue
            else:
                word[6]=index_map[word[6]]

        return output

    output = []
    offset = 1
    added_indices = []
    fixed_set = set()
    index_map = dict()
    for word_index in range(len(morphdep)):
        if None in morphdep[word_index]:
            return None
        index_map[morphdep[word_index][3]]=morphdep[word_index][3]
    for index, word in enumerate(morphdep):
        pos = word[1]
        if pos in ['+...', '+/.']:
            return None
        elif '+' in word[0]:  # noun compound
            sub_words = word[0].split('+')
            last_word=sub_words[-1]
            position_last_word=index+offset+len(sub_words)-1
            for c, w in enumerate(sub_words[0:-1]):
                output.append([index + offset + c, w, w, 'n', 'n', '_', position_last_word, 'compound', '_', '_'])
            output.append([position_last_word, last_word, last_word, 'n', 'n', '_', \
                           word[3], word[4], '_', '_'])

            # index_map -- 1. all indices greater than index+offset should be added len(sub_words), 2. change index+offset to position_last_word
            for key in index_map:
                if index_map[key]>index+offset:
                    index_map[key]=index_map[key]+len(sub_words)-1
                elif index_map[key]==index+offset:
                    index_map[key]=position_last_word
            fixed_set.update(list(range(index+offset,position_last_word)))
            offset += len(sub_words) - 1
        elif '_' in word[0]:  # MWE
            sub_words = word[0].split('_')
            output.append([index + offset, sub_words[0], sub_words[0], 'X', 'X', '_', word[3], word[4], '_', '_'])
            for c, w in enumerate(sub_words[1:]):
                output.append([index + offset + c + 1, w, w, 'X', 'X', '_', index + offset, 'mwe', '_', '_'])
            # same, but here we don't need to change the head index+offset
            for key in index_map:
                if index_map[key]>index+offset:
                    index_map[key]=index_map[key]+len(sub_words)-1
            fixed_set.update(list(range(index+offset+1,index+offset+len(sub_words))))
            offset += len(sub_words) - 1
        else:
            output.append([index + offset, word[0], word[0], pos, pos, '_', word[3], word[4], '_', '_'])

    output = fix_offsets(output, fixed_set, index_map)
    return output


def process_dir(dir, output_file):
    """
    Processes all the xmls in dir and its sub-directories.
    """
    eng = CHILDESCorpusReader(dir, '.*.xml')
    f = open(output_file, 'w')
    for fileid in eng.fileids():
        for ind, morph_dep in enumerate(eng.morph_deps(fileid, speakers='is_adult')):
            conll_lines = to_conll(morph_dep)
            if conll_lines:
                f.write('#' + fileid + ',' + str(ind) + '\n')
                for line in conll_lines:
                    for field in line:
                        if isinstance(field, unicode):
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

    # default directory: '/cs/++/staff/oabend/nltk_data/corpora/childes/data-xml/'
    process_dir(sys.argv[1], sys.argv[2])



