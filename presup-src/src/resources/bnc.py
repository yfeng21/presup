'''
Created on Mar 2, 2016

@author: jcheung
'''
import os
import glob
from utils.data_structures import read_corenlp_doc, Document

class BNCCorpus:
    def __init__(self, root_d):
        self.root_d = root_d # e.g. /home/rldata/BNC/corenlp_xml
        self.offset_d = os.path.join(self.root_d, 'bnc_offsets')
        
        
    def doc_iter(self, subset = 'all'):
        
        sections = [''] # '' for everything
        
        for section in sections:
            fs = glob.glob(os.path.join(self.root_d, section + '*.out'))
            fs.sort()
            for f in fs:
                try:
                    _, tail = os.path.split(f)
                    #print tail
                    prefix = tail.rsplit('.', 1)[0]
                    doc = read_corenlp_doc(f, tail, no_coref = True)
                    offset_f = prefix + '.xml.offset'
                    offsets = self.read_offsets(os.path.join(self.offset_d, offset_f))
                    #print offsets
                    for subdoc in self.split_doc(prefix, doc, offsets):
                        yield subdoc
                except:
                    with open('log.txt', 'a') as fh:
                        fh.write('%s\n' % f)
                    continue
                            
    def read_offsets(self, offset_f):
        with open(offset_f, 'r') as fh:
            lines = fh.readlines()
            lines = [map(int, line.strip().split(' ')) for line in lines]
            
            return lines
    
    def split_doc(self, prefix, doc, offsets):
        '''
        Split sentences in Document into multiple Documents at the indicated
        offset points
        '''
        if len(offsets) <= 1:
            return [doc]
        docs = []
        for i in xrange(len(offsets) - 1):
            num, start = offsets[i]
            end = offsets[i+1][1]
            docid = prefix + '-' + str(num)
            #print docid, start, end
            new_doc = Document()
            new_doc.num = docid
            for sentnum, sent in doc.sents.iteritems():
                if start <= sentnum < end:
                    new_doc.sents[sentnum - start + 1] = sent
            docs.append(new_doc) 
        # last doc
        num, start = offsets[-1]
        docid = prefix + '-' + str(num)
        #print docid, start
        new_doc = Document()
        new_doc.num = docid
        for sentnum, sent in doc.sents.iteritems():
            if start <= sentnum:
                new_doc.sents[sentnum - start + 1] = sent
        docs.append(new_doc) 
        return docs