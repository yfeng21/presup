'''
Created on 2012-06-26

data_structures.py - data structures containing the corpus
@author: Jackie
'''

from nltk.stem import WordNetLemmatizer
import os, codecs
from xml.etree import cElementTree as ElementTree
#from lxml import etree as ElementTree # slower
import time
import re

def concatenate_corenlp_corpus(directory, filedict, out_f, toload = None):
    if toload is None:
        keys = filedict.keys()
        keys.sort()
    else:
        keys = sorted(toload)
    out_fh = codecs.open(out_f, 'w', encoding = 'utf-8')
    out_fh.write('''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet href="CoreNLP-to-HTML.xsl" type="text/xsl"?>
<root>\n''')
    
    for docnum in keys:
        fname = os.path.join(directory, filedict[docnum])
        fh = codecs.open(fname, 'r', encoding = 'utf-8')
        lines = fh.readlines()
        # create id for document
        out_fh.write('  <document id="%s">\n' % docnum)
        # skip first 4, last 1
        out_fh.write(''.join(lines[4:-1]))

    out_fh.write('</root>')
    out_fh.close()
        

def read_corenlp_corpus_singlefile(corpus_f, toload = None):
    '''
    Read the corpus as a single file, returning documents in the order 
    they are found in the file.
    '''
    
    t1 = time.clock()
    tree = ElementTree.parse(corpus_f) #filename=corpus_f
    t2 = time.clock()
    docnodes = tree.iterfind('document')
    t3 = time.clock()
    print t2 - t1, t3 - t2
    for docnode in docnodes:
        docnum = docnode.get('id') # warning: this is a str
        if toload is None or docnum in toload:
            doc = read_doc_from_node(docnode)
            yield (docnum, doc)
    
    
    """
    # This version is incremental:
    #   faster and more memory-efficient if you are reading only a little bit of the file
    #   slower if you are going read all of it anyway
    for event, elem in ElementTree.iterparse(corpus_f):
        if elem.tag == 'document':
            docnum = elem.get('id') # warning: this is a str
            if toload is None or docnum in toload:
                doc = read_doc_from_node(elem)
                yield (docnum, doc)
            elem.clear()
    """

def read_corenlp_corpus(directory, filedict, toload = None):
    '''
    A generator of (docnum, Document) tuples.
    directory - folder containing the CoreNLP output files
    filedict - docnum <int> -> filename (relative to directory) <str>

    Can use either the keys of filedict (default) or pass in a
    particular list of keys to load.
    '''
    if toload is None:
        keys = filedict.keys()
        keys.sort()
    else:
        keys = sorted(toload)

    for docnum in keys:
        filename = filedict[docnum]
        doc = read_corenlp_doc(os.path.join(directory, filename), docnum)
        yield (docnum, doc)

def read_corenlp_doc(xmlf, docnum, no_coref = False):
    '''
    New version that uses ElementTree
    '''
    #parser = ElementTree.XMLParser(encoding = 'utf-8') 
    #tree = ElementTree.parse(xmlf, parser = parser)
    
    # alternate version: ignore illegal characters because of CoreNLP encoding problem
    xmltext = codecs.open(xmlf, 'r', encoding='utf-8', errors='ignore').read()
    #print len(xmltext)
    tree = ElementTree.fromstring(xmltext) #parses string into an element
    docnode = tree.find('document')
    doc = read_doc_from_node(docnode, no_coref = no_coref)
    doc.num = docnum
    return doc


def read_doc_from_node(docnode, corenlp3 = True, corenlp_format = True, 
                       treetype = 'collapsed-ccprocessed-dependencies',
                       no_coref = False):
    '''
    corenlp3:
      = True: <dependencies type="collapsed-ccprocessed-dependencies"> ... </..>
      = False: <collapsed-ccprocessed-dependencies> ... </..>
    corenlp_format
      = True: <governor idx="#">word</governor>
      = False (annotated_gigaword_format): <governor>#</governor>

    treetype
      = basic-dependencies, collapsed-dependencies, or collapsed-ccprocessed-dependencies
    '''
    #times = []
    #times.append(('start', time.clock()))
    
    doc = Document()
    doc_children = list(docnode)
    if len(doc_children) < 1 or doc_children[0].tag != 'sentences': return doc
    sents_node = doc_children[0]
    
    for sentnode in sents_node:
        #assert sentnode.tag == 'sentence'
        # load basic information about tokens in sentences
        sent = Sentence()
        sent.num = int(sentnode.get('id'))
        doc.sents[sent.num] = sent
        tokennodes = sentnode.find('tokens')
        for tokennode in tokennodes:
            #assert tokennode.tag == 'token'
            token = Token()
            token.num = int(tokennode.get('id'))
            token.word = tokennode.findtext('word')
            token.lemma = tokennode.findtext('lemma')
            token.pos = tokennode.findtext('POS')
            token.ner = tokennode.findtext('NER')
            sent.tokens[token.num] = token

        # load parse
        if corenlp3:
            # newer format
            dependencies_nodes = sentnode.iterfind('dependencies')
            for dependencies_node in dependencies_nodes:
                if dependencies_node.get('type') == treetype:
                    depnodes = dependencies_node.iterfind('dep') 
        else:
            # older format
            depnodes = sentnode.find(treetype).iterfind('dep')
        for depnode in depnodes:
            node = DepNode()
            node.reltype = depnode.get('type')
            if corenlp_format:
                gov, dep = list(depnode)
                #assert gov.tag == 'governor'
                #assert dep.tag == 'dependent'
                node.governor = int(gov.get('idx'))
                node.dependent = int(dep.get('idx'))
            else:
                gov, dep = list(depnode)
                #assert gov.tag == 'governor'
                #assert dep.tag == 'dependent'
                node.governor = int(gov)
                node.dependent = int(dep)
            sent.parse.add(node.dependent, node)
        __add_head(sent)
    #times.append(('parse', time.clock()))
    
    # load coreference chains for document
    if not no_coref:
        corefstring = 'coreference'
        if not corenlp_format: corefstring = 'coreferences'
        corefs_node = None
        if len(doc_children) > 1:
            corefs_node = doc_children[1]
            #assert corefs_node.tag == corefstring
        
        if corefs_node is not None:
            for corefnode in corefs_node:
                chain = CorefChain()
                for mentionnode in corefnode.iterfind('mention'):
                    mention = CorefMention()
                    mention.representative = 'representative' in mentionnode.keys()
                    mention.sentence = int(mentionnode.findtext('sentence'))
                    mention.start = int(mentionnode.findtext('start'))
                    mention.end = int(mentionnode.findtext('end'))
                    mention.head = int(mentionnode.findtext('head'))
                    chain.mentions.append(mention)
                if len(chain.mentions) > 0:
                    doc.corefs.append(chain)
        #times.append(('coref', time.clock()))
        
        #for i in xrange(len(times) - 1):
        #    print '%s\t%.4fms' % (times[i + 1][0], (times[i + 1][1] - times[i][1]) * 1000)
        #print
    
    return doc


def __add_head(sent):
    '''
    Add the head of sent as a node in sent.parse, because
    Stanford parser does not do this automatically.

    Head of sentence: has dependents AND no governors
    Add it back in with governor = 0
    '''
    for tokennum in sent.tokens:
        if not sent.parse.nodes.has_key(tokennum) and \
           len(sent.parse.dependents_of(tokennum)) > 0:
            headnode = DepNode()
            headnode.reltype = 'root'
            headnode.governor = 0
            headnode.dependent = tokennum
            sent.parse.add(tokennum, headnode)
            break
        
"""
def read_doc_from_node(docnode, corenlp3 = True, corenlp_format = True, treetype = 'collapsed-ccprocessed-dependencies'):
    '''
    corenlp3:
      = True: <dependencies type="collapsed-ccprocessed-dependencies"> ... </..>
      = False: <collapsed-ccprocessed-dependencies> ... </..>
    corenlp_format
      = True: <governor idx="#">word</governor>
      = False (annotated_gigaword_format): <governor>#</governor>

    treetype
      = basic-dependencies, collapsed-dependencies, or collapsed-ccprocessed-dependencies
    '''
    doc = Document()

    sents_node = docnode.find('sentences')
    if sents_node is None: # no sentences
        return doc
    sentnodes = sents_node.findall('sentence')
    for sentnode in sentnodes:
        # load basic information about tokens in sentences
        sent = Sentence()
        sent.num = int(sentnode.get('id'))
        doc.sents[sent.num] = sent
        tokennodes = sentnode.find('tokens').findall('token')
        for tokennode in tokennodes:
            token = Token()
            token.num = int(tokennode.get('id'))
            token.word = tokennode.findtext('word')
            token.lemma = tokennode.findtext('lemma')
            token.pos = tokennode.findtext('POS')
            token.ner = tokennode.findtext('NER')
            sent.tokens[token.num] = token

        # load parse
        if corenlp3:
            # newer format
            dependencies_nodes = sentnode.findall('dependencies')
            for dependencies_node in dependencies_nodes:
                if dependencies_node.get('type') == treetype:
                    depnodes = dependencies_node.findall('dep') 
        else:
            # older format
            depnodes = sentnode.find(treetype).findall('dep')
        for depnode in depnodes:
            node = DepNode()
            node.reltype = depnode.get('type')
            if corenlp_format:
                node.governor = int(depnode.find('governor').get('idx'))
                node.dependent = int(depnode.find('dependent').get('idx'))
            else:
                node.governor = int(depnode.findtext('governor'))
                node.dependent = int(depnode.findtext('dependent'))
            sent.parse.add(node.dependent, node)
        __add_head(sent)
    # load coreference chains for document
    corefstring = 'coreference'
    if not corenlp_format: corefstring = 'coreferences'
    corefs_node = docnode.find(corefstring)
    if corefs_node is not None:
        for corefnode in corefs_node.getchildren():
            chain = CorefChain()
            for mentionnode in corefnode.findall('mention'):
                mention = CorefMention()
                mention.representative = 'representative' in mentionnode.keys()
                mention.sentence = int(mentionnode.findtext('sentence'))
                mention.start = int(mentionnode.findtext('start'))
                mention.end = int(mentionnode.findtext('end'))
                mention.head = int(mentionnode.findtext('head'))
                chain.mentions.append(mention)
            if len(chain.mentions) > 0:
                doc.corefs.append(chain)
    return doc


def __add_head(sent):
    '''
    Add the head of sent as a node in sent.parse, because
    Stanford parser does not do this automatically.

    Head of sentence: has dependents AND no governors
    Add it back in with governor = 0
    '''
    for tokennum in sent.tokens:
        if not sent.parse.nodes.has_key(tokennum) and \
           len(sent.parse.dependents_of(tokennum)) > 0:
            headnode = DepNode()
            headnode.reltype = 'root'
            headnode.governor = 0
            headnode.dependent = tokennum
            sent.parse.add(tokennum, headnode)
            break
"""


lemmatizer = WordNetLemmatizer()
def wn_lemmatize(word):
    '''
    Lemmatize a word, not knowing whether it is a verb or a noun.
    '''
    global lemmatizer
    v = lemmatizer.lemmatize(word, 'v')
    if v != word:
        return v
    n = lemmatizer.lemmatize(word, 'n')
    return n

def remap_helper(reltype):
    r = reltype
    if reltype == 'nsubjpass':
        r = 'dobj'
    elif reltype == 'agent' or reltype == 'xsubj':
        r = 'nsubj'
    elif reltype == 'csubjpass':
        r = 'ccomp'
    return r

def list_to_str(sent):
    sent = ' '.join(sent)
    sent = sent.replace(' ,' , ',')
    sent = sent.replace(' .' , '.')
    sent = sent.replace(' !' , '!')
    sent = sent.replace(' ?' , '?')
    sent = sent.replace('$ ' , '$')
    sent = sent.replace(' :' , ':')
    sent = sent.replace(' ;' , ';')
    sent = sent.replace(' %' , '%')
    sent = sent.replace(' \' ', '\' ')
    sent = sent.replace(' \'s' , '\'s')
    sent = sent.replace(' \'m' , '\'m')
    sent = sent.replace(' \'ve' , '\'ve')
    sent = sent.replace(' \'re' , '\'re')
    sent = sent.replace(' \'d' , '\'d')
    sent = sent.replace(' \'ll' , '\'ll')
    sent = sent.replace('`` ' , '"')
    sent = sent.replace(' \'\'' , '"')
    sent = sent.replace(' n\'t', 'n\'t')
    sent = sent.replace(' _ ', ' -- ')
    sent = sent.replace('-LRB- ', '(')
    sent = sent.replace(' -RRB-', ')')
    sent = sent.replace('` ' , '\'')
    sent = sent.replace(' can not ' , ' cannot ')
    return sent

class DepNode:
    governor = -1
    dependent = -1
    reltype = ''
    
    def __init__(self):
        self.governor = -1
        self.dependent = -1
        self.reltype = ''
    
    def govdep(self, sent, lemmatize_word = False, remap = False):
        reltype = self.reltype
        if remap:
            reltype = remap_helper(reltype)
        if self.governor == 0:
            return '>%s' % reltype
        if lemmatize_word:
            lemma = wn_lemmatize(sent.at(self.governor).word).lower()
            return '%s>%s' % (lemma, reltype)
        else:
            return '%s>%s' % (sent.at(self.governor).lemma, reltype)
    def __repr__(self):
        return '%s > %s > %s' % (self.governor, self.reltype, self.dependent)    
        
class DepTree:
    nodes = {}
    head = -1
    
    def __init__(self):
        self.nodes = {} # key is the dependent, value is a list
        self.head = -1
    def dependents_of(self, governor):
        '''
        Returns the immediate dependents of governor.
        '''
        return [node.dependent for dep_id, node in self.iternodes() 
                if node.governor == governor]
    def dependent_nodes_of(self, governor):
        '''
        Returns the immediate dependents of governor.
        '''
        return [node for dep_id, node in self.iternodes() 
                if node.governor == governor]
    def iternodes(self):
        '''
        Iterator over all the (tokennum, nodes) pairs.
        '''
        for dep_id, nodes in self.nodes.iteritems():
            for node in nodes:
                yield (dep_id, node)
    def span_of(self, head_node_id):
        '''
        Returns the start and end of the phrase headed by head_node.
        '''
        children = [child for child in self.dependents_of(head_node_id) if child != head_node_id]
        # base case
        if len(children) == 0:
            return (head_node_id, head_node_id)
        else:
            spans = [self.span_of(child) for child in children]
            start = min(head_node_id, *[x[0] for x in spans])
            end = max(head_node_id, *[x[1] for x in spans])
            return (start, end)
        
    def add(self, dep_id, node):
        '''
        Adder to nodes.
        '''
        list_nodes = self.nodes.setdefault(dep_id, [])
        list_nodes.append(node)
    
    def subtree_nodes(self, governor, reltype = None):
        '''
        Returns all the nodes that are the descendants of governor with the specified reltype,
        or any reltype if reltype is None.
        
        Note that the recursive call uses reltype = None, because we don't care what the
        future descendants' reltypes are.
        '''
        if reltype is None:
            children = {dep_id:node for dep_id, node in self.iternodes() 
                        if node.governor == governor and node.dependent != governor}
        else:
            children = {dep_id:node for dep_id, node in self.iternodes() 
                        if node.governor == governor and node.dependent != governor 
                        and node.reltype == reltype}
        for dep_id, node in children.items():
            descendants = self.subtree_nodes(dep_id, reltype = None)
            children.update(descendants)
        return children
                
class Document:
    """
    A representation of a document, preprocessed by CoreNLP.
    """
    num = -1
    sents = {}
    corefs = []
    docid = ''
    
    def __init__(self):
        self.num = -1
        self.sents = {}
        self.corefs = []
        self.docid = '' # optional element
        # optional element: self.doctype
        
    def at(self, sentnum):
        return self.sents.get(sentnum)

class Sentence:
    """
    A representation of a sentence with its parse, preprocessed by CoreNLP.
    """
    num = -1
    tokens = {}
    parse = DepTree()
    
    def __init__(self):
        self.num = -1
        self.tokens = {}
        self.parse = DepTree()
    def at(self, tokennum):
        return self.tokens.get(tokennum)
    def text(self):
        '''
        Returns a text string of the words in the sentence.
        '''
        keys = sorted(self.tokens.keys())
        return list_to_str([self.tokens[key].word for key in keys])
    def real_word_count(self):
        return len(self.text().split())
    
class Token:
    num = -1
    word = ''
    lemma = ''
    pos = ''
    ner = ''


class CorefChain:
    def __init__(self):
        self.mentions = []
        
class CorefMention:
    def __init__(self):
        self.representative = False
        self.sentence = -1
        self.start = -1
        self.end = -1
        self.head = -1
        
        
class DocInfo:
    """
    A data structure for storing information about a document in the
    TAC corpus, such as the domain/topic of the document, the LDC-assigned
    ID in Gigaword, etc.
    """
    def __init__(self, *my_args):
        if len(my_args) == 2:
            doc_line, topic_dict = my_args
            args = doc_line.split('\t')
            self.docid = int(args[0])
            self.ggwid = args[3]
            self.subtopicid = args[2]
            self.topicid = args[1]
            self.topiccat = topic_dict[self.topicid][0]
            self.topictitle = topic_dict[self.topicid][1]
        elif len(my_args) == 0:
            pass
        
            