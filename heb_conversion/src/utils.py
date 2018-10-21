"""
All sorts of useful utility methods.
"""
import re, sys, pdb

WORD_FORMAT = ['index','form','lemma','upos','xpos','feats','head_index','deprel','deps','misc']
INT_FIELDS = ['index','head_index']

ALWAYS_AUX = ['am','is', 'are', 'was', 'were', 'be', 'been', 'being']
AUX_WORDS = ALWAYS_AUX + ['have', 'has', 'had', 'do', 'does', 'did']

tab_regexp = re.compile('\\s*\\t\\s*')

def get_list_from_file(filename, as_float = False, exclude_neg=False, comment=None):
    """
    as_float: whether to return a list of floats
    exclude_neg: exclude all entries that are below 0
    """
    f = open(filename)
    L = []
    for line in f:
        if as_float:
            x = float(line.strip())
            if exclude_neg and x < 0:
                continue
            else:
                L.append(x)
        else:
            if comment != None and line.strip().startswith(comment):
                continue
            else:
                L.append(line.strip())
    return L


def read_sents_from_file(f):
    """
    An iterator that returns the sentences of the file, sentence by sentence.
    """
    sent = []
    for line in f:
        line = line.strip()
        if line == "":
            if sent != []:
                yield 'SENT', Sentence(sent)
                sent = []
        elif line.startswith('#'):
            yield 'COMMENT', line
        else:
            sent.append(line)
    if sent != []:
        yield 'SENT', Sentence(sent)
    f.close()

        
class Sentence:
    "A sentence in the dependency format."
    
    def __init__(self, sent_str):
        self._words = []
        for word_str in sent_str:
            try:
                w = DepWord(word_str)
            except ValueError:
                w = None
            if w:
                self._words.append(w)
    
    def bfs(self):
        """
        Returns the words in the tree in a BFS order.
        """
        Q = [self.head()]
        visited = []
        while Q != []:
            cur = Q[0]
            visited.append(cur)
            Q = Q[1:]
            Q.extend([ch for ch in self.get_deps(cur.get_field('index'))])
        for x in reversed(visited):
            yield x

    def head(self):
        for word in self._words:
            if word.get_field('head_index') == 0:
                return word
        return None
    
    def word_by_index(self, index):
        return self._words[index-1]

    def get_deps(self, word_index, label_set=None):
        if label_set:
            return [w for w in self._words if w.get_field('head_index') == word_index and \
                    w.get_field('deprel') in label_set]
        else:
            return [w for w in self._words if w.get_field('head_index') == word_index]
    
    def get_subtree(self, word):
        "returns all the the words in this word's subtree"
        output = [word]
        Q = [word]
        while len(Q) > 0:
            w = Q.pop()
            Q.extend(self.get_deps(w.get_field('index')))
            output.extend(self.get_deps(w.get_field('index')))
        return sorted(output, key=lambda w: w.get_field('index'))

    def word_range(self, index2, index1 = 1, excludes = []):
        """
        returns all the words according to their order up to (and excluding) index. 
        if index1 is specified, it is the first index excluded. indices starts at 1.
        exclude are indices which should not be included.
        """
        if index2 == None:
            return [w for w in self._words[(index1-1):] if w.get_field('index') not in excludes]
        else:
            return [w for w in self._words[(index1-1):(index2-1)] if w.get_field('index') not in excludes]

    def set_field(self,ind,name,val):
        "ind starts at 1"
        self._words[ind-1].set_field(name,val)


    def __str__(self):
        s = [w.full_str() for w in self._words]
        return '\n'.join(s)

    def str_strip(self):
        s = [w.stripped_str() for w in self._words]
        return '\n'.join(s)
   
class DepWord:
    "A word in the dependency format."
    def __init__(self, line):
        fields = tab_regexp.split(line)
        self._fields = dict(zip(WORD_FORMAT, fields))
        for key in [x for x in self._fields if x in INT_FIELDS]:
            if self._fields[key] != '_':
                self._fields[key] = int(self._fields[key])

    def set_field(self, name, val):
        self._fields[name] = val

    def get_field(self, name):
        return self._fields[name]
    
    def __str__(self):
        return self._fields['word']
    
    def full_str(self):
        return '\t'.join([str(self._fields[x]) for x in WORD_FORMAT])

    def stripped_str(self,exclude_fields = ['head_index','deprel']):
        return '\t'.join([(str(self._fields[x]) if x not in exclude_fields else '_') for x in WORD_FORMAT])


