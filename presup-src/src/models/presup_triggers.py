'''
Created on Feb 18, 2016

@author: jcheung
'''

import sys
sys.path.insert(0, r'../')

import cPickle
import random
import numpy as np
import csv, os, glob
import tables as tb
from scipy.sparse import lil_matrix, csr_matrix
from utils.utils import tbOpen, load_h5f_csr, write_h5f_csr, write_h5f_array, load_h5f_array
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

pos_stoplist = set(['DT', ',', '.', '$', "''", '#', '-LRB-', '-RRB-', ':', '``'])
target_words = ['too', 'again', 'also', 'still', 'yet'] #, 'anymore', 'just', 'only', 'even']
# subroot=' /home/ml/yfeng21/giga_dataset/train1'
subroot="E:\Summer\wsj_mrg"
# anymore # rare, can be predicted by presence of DEO
#'just' # very ambiguous
#'only'
#'even' # also ambiguous; many uses are not presuppositional or related to context

class PresupExtractor(object):
    '''
    Extract features
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        self.params = params
        self.debug = params.get('debug', True)
        self.records_dict = None


    def run(self, corpus,output_root,subset='all',window_size = 25):
        subdir = os.path.join(output_root, subset)
        if not os.path.exists(subdir):
            os.mkdir(subdir)
        ndocs = 0
        self.records_dict = {} # doc -> list of records
        verb_loc = {}

        for doc in corpus.doc_iter(subset,0):
            # self.extract_num(doc,verb_loc)
            self.records_dict[doc.num] = self.extract_records(doc)
            ndocs += 1
            if self.debug and ndocs >= 5:
                break
            # print doc.num

###########################Edited##########################
        # a dict to store the verbs modified by adverb

        verb_dict={}
        counts = dict.fromkeys(target_words, 0)
        for _, records in self.records_dict.iteritems():
            for r in records:
                counts[r.label] += 1
                # if self.params.get('records_out'):
                verb_loc[r.loc[:2]]= r.governor
                if not r.governor in verb_dict:
                    verb_dict[r.governor] = 1
                else:
                    verb_dict[r.governor] += 1
                # print '%s\t%s\t%s\t%s' % (str(r.loc), r.governor, r.gov_pos, r.label)

        print counts,sum(counts.itervalues())
        # with open(os.path.join(subdir,"counts.pkl"),"wb") as f:
        #     tuple=(counts,sum(counts.itervalues()))
        #     cPickle.dump(tuple,f)
        # print sum(verb_dict.itervalues())
        # with open(os.path.join(subdir,"verbdict.pkl"),"wb") as f:
        #     cPickle.dump(verb_dict,f)
        print "got verb_dict"

        # window_size = 25
        print "extracting positive cases"
        self.extract_positive(window_size,corpus,subset,verb_loc, os.path.join(subdir,'positive_data.pkl'))
        print "done extracting positive cases"
        print "extracting negative cases"
        self.extract_negative(window_size,corpus,subset,verb_dict,os.path.join(subdir,'negative_data.pkl'))
        print "done extracting negative cases"

    def extract_negative(self, window_size, corpus,subset,verb_dict,out):
        # extract the negative cases
        with open(out, 'wb') as output:
            for doc in corpus.doc_iter(subset,1):
                stop_set = set()
                name_list = self.extract_num_negative(doc)
                word_list = [word[0] for word in name_list]
                pos_list = [word[1] for word in name_list]
                # print name_list
                for one in word_list:
                    if one in verb_dict and one not in stop_set:
                        stop_set.add(one)
                        indices_of_verb, indices_of_end = self.search(word_list, one)
                        # print indices_of_verb, indices_of_end
                        if len(indices_of_verb)>1:
                            # new_indices=random.sample(indices,len(indices))  #shuffle indices for unbiased sample
                            # indices = new_indices
                            combined = zip(indices_of_verb, indices_of_end)
                            random.shuffle(combined)
                            indices_of_verb, indices_of_end = zip(*combined)
                            # print indices_of_verb, indices_of_end
                        for i in range(len(indices_of_verb)):
                            j = indices_of_verb[i]  # position of verb
                            k = indices_of_end[i]  # position of end of sentence
                            if set(target_words).isdisjoint(word_list[j - 3:j + 3]):
                                if verb_dict[one] >= 1:
                                    verb_dict[one] -= 1
                                    if j <= window_size:
                                        tuple = (0, word_list[:j]+["@@@@"]+word_list[j:k], pos_list[:j]+["@@@@"]+pos_list[j:k])
                                    else:
                                        tuple = (0, word_list[j - window_size:j]+["@@@@"]+word_list[j:k], pos_list[j - window_size:j]+["@@@@"]+pos_list[j:k])
                                    # print tuple
                                    # raw_input("---")
                                    assert len(tuple[1])==len(tuple[2]),"word list and pos list length not match"
                                    cPickle.dump(tuple, output)
        # print "getting rare verblist"
        # rare_verblist=[(i, verb_dict[i]) for i in verb_dict if verb_dict[i] != 0]
        # subdir = os.path.join(subroot, subset)
        # with open(os.path.join(subdir, 'rare_verblist.pkl'), 'wb') as f:
        #     cPickle.dump(rare_verblist,f)
        # print "got rare verblist"


    def extract_positive(self,window_size,corpus,subset,verb_loc,out):
        positive_doc=[loc[0] for loc in verb_loc.keys()]
        with open(out, 'wb') as output:
            for doc in corpus.doc_iter(subset, 0):
                if doc.num in positive_doc:
                    name_list = self.extract_num(doc,verb_loc)
                else:
                    continue
                word_list = [word[0] for word in name_list]
                pos_list = [word[1] for word in name_list]
                for one in target_words:
                    if one in word_list:
                        # print " ".join(x for x in word_list)
                        indices_of_adverb, indices_of_end = self.search(word_list, one)
                        for i in range(len(indices_of_adverb)):
                            j= indices_of_adverb[i] #position of adverb
                            k= indices_of_end[i] #position of end of sentence
                            if j<=window_size:
                                tuple=(one,word_list[:j]+word_list[j+1:k],pos_list[:j]+pos_list[j+1:k])
                            else:
                                tuple = (one, word_list[j-window_size:j]+word_list[j+1:k],pos_list[j-window_size:j]+pos_list[j+1:k])
                            assert len(tuple[1])==len(tuple[2]),"word list and pos list length not match"
                            cPickle.dump(tuple,output)


    def search(self, name_list, key_word):
        # print name_list
        indices_of_adverb = [i for i, x in enumerate(name_list) if x==key_word]
        indices_of_end = []
        # try:
        #     indices_of_end = [number+name_list[number:].index(".")for number in indices_of_adverb] #indices of the end of the sentence
        # except ValueError:
        #     indices_of_end = [number + 10 for number in indices_of_adverb]
        for number in indices_of_adverb:
            try:
                end_index=name_list[number:].index(".")
                if end_index>10:
                    end_index=10
            except ValueError:
                end_index=10
            indices_of_end.append(number+end_index) #indices of the end of the sentence
        return indices_of_adverb,indices_of_end

    def extract_num_negative(self, doc):
        name_list = []  # (word,pos)
        for sentn, sent in doc.sents.iteritems():
            for k in sent.tokens.keys():
                word = sent.tokens[k].word
                pos = sent.tokens[k].pos
                tuple = (word, pos)
                name_list.append(tuple)
        return name_list

    def extract_num(self, doc,verb_loc):
        name_list = [] #(word,pos)
        for sentn, sent in doc.sents.iteritems():
            head_verb = None
            if (doc.num,sentn) in verb_loc:
                head_verb=verb_loc[doc.num,sentn]
            for k in sent.tokens.keys():
                word = sent.tokens[k].word
                pos = sent.tokens[k].pos
                if word == head_verb:
                    name_list.append(("@@@@","@@@@"))
                tuple = (word,pos)
                name_list.append(tuple)
        return name_list


    def extract_records(self, doc):
        '''
        Extract records from a Document.
        Returns a list of Records
        '''
        records = []
        for sentn, sent in doc.sents.iteritems():
            # print sentn, sent.text()
            records.extend(self.extract_from_sent(doc.num, sentn, sent))
        return records

        
    def extract_from_sent(self, docn, sentn, sent):
        '''
        Extract records from a Sentence.
        '''
        records = []
        explored = set()
        for depid, node in sent.parse.iternodes():
            par = node.governor
            rel = node.reltype
            chi = node.dependent
            if chi in explored: continue
            if rel.startswith('conj'): continue # in conjoined NPs, use the other incoming edge
            explored.add(chi) # prevent duplicates
            
            chi_token = sent.at(chi)
            #print chi_token.word, chi_token.pos, rel,
            w = chi_token.word.lower()
            if w in target_words:
                #print '*'
                r = self.extract_record(docn, sentn, chi, sent, chi_token, node)
                # this is a record!
                if r is not None:
                    records.append(r)
                    # print node
                    # print r
                    # print w
                    # print docn
                    # print chi_token.word
                    # raw_input('record')
            else:
                pass
        return records
                
    def extract_record(self, docn, sentn, wordn, sent, hnoun, node):
        '''
        Extract from the sentence at the specified token hnoun, using the node (i.e., edge) 
        whose child is the location in the sentence 
        '''
        r = PresupRecord()
        r.label = hnoun.word.lower()
        r.loc = (docn, sentn, wordn)
        
        i = node.governor
        if i >= 1:
            r.governor = sent.at(i).word
            r.gov_pos = sent.at(i).pos
            # too + ADJ is another "too"
            if r.label == 'too' and r.gov_pos.startswith(('JJ', 'RB')):
                return None
        return r


class PresupRecord:
    def __init__(self):
        self.fdict = {} # fname -> fval
        self.label = None
        self.governor = None
        self.gov_pos = None
        self.loc = None # (docnum, sentnum, tokennum)
    def __str__(self):
        return '%s\t%s\t%s' % (self.loc, self.label, str(self.fdict))
