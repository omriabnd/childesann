import sys, utils

if len(sys.argv) != 2:
    print('Usage: strip_annotation.py <input fn>')
    sys.exit(-1)

f = open(sys.argv[1])
for t,sent in utils.read_sents_from_file(f):
    if otype == 'SENT':
        print(sent.str_strip()+'\n')
    else:
        print(sent)
f.close()


