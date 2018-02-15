import cPickle,os,numpy
def pickleLoader(pklFile):
    try:
        while True:
            yield cPickle.load(pklFile)
    except EOFError:
        pass

def get(path):
    print "getting corpus and label from %s" % path
    positive=os.path.join(path, "positive_data.pkl")
    negative=os.path.join(path, "negative_data.pkl")
    corpus=[]
    labels=[]
    POS=[]
    with open(positive) as f:
        for line in pickleLoader(f):
            corpus.append(line[1])
            POS.append(line[2])
            if line[0] == "also":
                labels.append(1)
            if line[0] == "still":
                labels.append(2)
            if line[0] == "yet":
                labels.append(3)
            if line[0] == "again":
                labels.append(4)
            if line[0] == "too":
                labels.append(5)
    with open(negative) as f:
        for line in pickleLoader(f):
            labels.append(0)
            corpus.append(line[1])
            POS.append(line[2])
    return corpus,labels,POS
    # out=os.path.join(path, "corpus.pkl")
    # out=open(out,"wb")
    # cPickle.dump(corpus, out)
    # out.close()
    # out=os.path.join(path, "labels.pkl")
    # out=open(out,"wb")
    # cPickle.dump(labels, out)
    # out.close()
    # out=os.path.join(path, "POS.pkl")
    # out=open(out,"wb")
    # cPickle.dump(POS, out)
    # out.close()



# read a single line
def readLine(pklFile1):
    f=open(pklFile1, 'rb')
    # X = cPickle.load(f)
    Y = cPickle.load(f)
    f.close()
    return Y


def printLine(file):
    out=readLine(file)
    print out


#read a pickle file such as positive_data.pkl
def readSplitData(pklFile):
    with open(pklFile) as f:
        for line in pickleLoader(f):
            # y.append(line[0]) #label
            context1 = " ".join(line[1])
            context2 = " ".join(line[2])
            print (line[0],context1,context2)
            # raw_input("---")

def readFile(pklFile):
    with open(pklFile) as f:
        for line in pickleLoader(f):
            print (line)
            raw_input("---")

def build_dict(path):
    corpus=os.path.join(path, "corpus.pkl")
    out=os.path.join(path, "dict.pkl")
    sentences = readLine(corpus)
    #print 'Building dictionary..',
    wordcount = dict()
    for ss in sentences:
        for w in ss:
            if w.lower() not in wordcount:
                wordcount[w.lower()] = 1
            else:
                wordcount[w.lower()] += 1

    counts = wordcount.values()
    keys = wordcount.keys()

    sorted_idx = numpy.argsort(counts)[::-1]

    worddict = dict()

    for idx, ss in enumerate(sorted_idx):
        worddict[keys[ss]] = idx+2  # leave 0 and 1 (UNK)

    #print "  "
    print numpy.sum(counts), ' total words ', len(keys), ' unique words'

    out = open(out,"wb")
    cPickle.dump(worddict, out)
    out.close()

def build_dict_from_train(path):
    print "building dictionary from %s" % path
    get(path)
    build_dict(path)


def extract_info(path1):
    test= os.path.join(path1,"test")
    dev=os.path.join(path1,"dev")
    train = os.path.join(path1,"train")

    build_dict_from_train(train)
    get(test)
    get(dev)

if __name__ == '__main__':

    path1="E:/Summer/wsj_mrg/"
    extract_info(path1)
    # printLine("E:\Summer\yulan/new_wsj_Y.pkl")
    # test=readLine("E:\Summer\presup-src\src\presup_ptb\presup_giga_all_adverbs_tagged.pkl")
    # print len(test),len(test[0]),len(test[1])
    # get_label(path1)
