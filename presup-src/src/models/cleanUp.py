import cPickle

def pickleLoader(pklFile):
    try:
        while True:
            yield cPickle.load(pklFile)
    except EOFError:
        pass


def alignSample(line):
    # newline1 = line[1]
    # newline2 = line[2]
    pivot1 = line[1].index("@@@@")
    pivot2 = line[2].index("@@@@")
    pivot = min(pivot1,pivot2)
    left1 = len(line[1])-pivot1
    left2 = len(line[2])-pivot2
    left = min(left1,left2)
    print pivot1,pivot2,pivot,pivot1-pivot,pivot2-pivot
    print left1,left2,left
    newline1 = line[1][pivot1-pivot:pivot1+left]
    newline2 = line[2][pivot2-pivot:pivot2+left]
    return (line[0],newline1,newline2)



def cleanFile(baseName):
    inFile = baseName+".pkl"
    outFile = baseName+"cleaned.pkl"
    outFile = open(outFile,"wb")
    with open(inFile,"rb") as f:
        for line in pickleLoader(f):
            if len(line[1])== len(line[2]):
                cPickle.dump(line,outFile)
            else:
                try:
                    pivot1 = line[1].index("@@@@")
                    pivot2 = line[2].index("@@@@")
                    newLine = alignSample(line)
                    cPickle.dump(newLine,outFile)
                except ValueError:
                    continue
    outFile.close()

def checkFile(inFile):
    count = 0
    with open(inFile,"rb") as f:
        for line in pickleLoader(f):
            if len(line[1])!= len(line[2]):
                count += 1
            if count ==0:
                print line
                count-=1
    print count

if __name__ == '__main__':
    # line = (0,
    #         ['Islamic', 'radical', 'had', 'come', 'to', 'Paris', 'from', 'Afghanistan', 'last', 'month', 'with', 'the', 'intention', 'of', 'committing', 'an', 'attack', 'against', 'French', 'interests', 'Speaking', 'to', 'Parliament', 'Prime', 'Minister', 'Alain', 'Juppe', 'noted', 'the', 'great', 'similarity', 'between', 'the', 'bomb', 'attacks', 'last', 'year', 'and', 'the', 'one', 'this', 'year', 'As', 'several', 'other', 'cabinet', 'ministers', 'did', 'Wednesday', 'he', '@@@@', 'called', 'on', 'the', 'French', 'people', 'to', 'show', 'sang-froid', '--', 'to', 'maintain', 'calm', '--', 'in', 'the', 'face', 'of', 'the', 'threat'],
    #         ['NNP', 'NN', 'VBD', 'VBN', 'TO', 'NNP', 'IN', 'NNP', 'JJ', 'NN', 'IN', 'DT', 'NN', 'IN', 'VBG', 'DT', 'NN', 'IN', 'JJ', 'NNS', 'VBG', 'TO', 'NNP', 'NNP', 'NNP', 'NNP', 'NNP', 'VBD', 'DT', 'JJ', 'NN', 'IN', 'DT', 'NN', 'NNS', 'JJ', 'NN', 'CC', 'DT', 'CD', 'DT', 'NN', 'IN', 'JJ', 'JJ', 'NN', 'NNS', 'VBD', 'NNP', 'PRP', '@@@@', 'VBD', 'IN', 'DT', 'JJ', 'NNS', 'TO', 'VB', 'NN', 'TO', 'VB', 'NN', 'IN', 'DT', 'NN', 'IN', 'DT', 'NN']
    #         )
    checkFile('E:\\Summer\\wsj_mrg\\test\\positive_data.pkl')
