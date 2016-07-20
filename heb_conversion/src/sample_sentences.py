import sys, utils, random

if len(sys.argv) != 3:
    print('Usage: sample_sentences <input fn> <#samples>')
    sys.exit(-1)
    
num_samples = int(sys.argv[2])

f = open(sys.argv[1])
sents = [x for x in utils.read_sents_from_file(f)]
f.close()

comments = [s for t,s in sents if t == 'COMMENT']
proper_sents = [s for t,s in sents if t == 'SENT']

if len(comments) != len(proper_sents):
    sys.stderr.write('Error '+str(len(comments))+' '+str(len(proper_sents))+'\n')
    sys.exit(-1)

sample_inds = random.sample(range(len(comments)),num_samples)
for ind in sample_inds:
    print(comments[ind])
    print(proper_sents[ind])
    print('')



