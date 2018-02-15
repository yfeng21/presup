import tables as tb
import gzip, codecs
import numpy as np
import os
from scipy.sparse import csr_matrix

def tbOpen(f, mode = 'r', compress = 'blosc'):
    '''
    Open a PyTables file handle.
    '''
    if mode == 'r':
        return tb.openFile(f, 'r')
    if mode == 'w' and compress == 'blosc':
        filters = tb.Filters(complevel = 1, complib = 'blosc')
        return tb.openFile(f, 'w', filters = filters)
    elif mode == 'w':
        return tb.openFile(f, 'w')


def write_h5f_array(h5f, h5fplace, name, atom, arr):
    if arr.shape == (0,):
        return
    place = h5f.createCArray(h5fplace, name, atom, shape = arr.shape)
    place[:] = arr
    
def write_h5f_strs(h5f, h5fplace, name, arr):
    s_place = h5f.createVLArray(h5fplace, name, tb.VLUnicodeAtom())
    for s in arr:
        s_place.append(s)

def write_h5f_dict(h5f, h5fplace, name, katom, vatom, d):
    '''
    Writes dictionary to a h5f file.
    '''
    if isinstance(katom, tb.VLUnicodeAtom) or isinstance(katom, tb.VLStringAtom):
        key_place = h5f.createVLArray(h5fplace, name + '_keys', katom)
        val_place = h5f.createCArray(h5fplace, name + '_values', vatom, shape = (len(d),))
        for i, (k, v) in zip(xrange(len(d)), d.iteritems()):
            key_place.append(k)
            val_place[i] = v
    else:
        key_place = h5f.createCArray(h5fplace, name + '_keys', katom, shape = (len(d),))
        val_place = h5f.createCArray(h5fplace, name + '_values', vatom, shape = (len(d),))
        for i, (k, v) in zip(xrange(len(d)), d.iteritems()):
            key_place[i] = k
            val_place[i] = v

def write_h5f_param(h5f, h5fplace, name, atom, param):
    arr = np.array([param])
    place = h5f.createCArray(h5fplace, name, atom, shape = arr.shape)
    place[:] = arr
    
def load_h5f_param(h5f, name):
    node = h5f.getNode(name)
    return node[0]

def load_h5f_dict(h5f, name):
    d = {}
    keys = h5f.getNode('%s_keys' % name)
    vals = h5f.getNode('%s_values' % name)
    for k, v in zip(keys, vals):
        d[k] = v
    return d

def load_h5f_csr(h5f, name):
    data = h5f.getNode('%s_data' % name)[:]
    indices = h5f.getNode('%s_indices' % name)[:]
    indptr = h5f.getNode('%s_indptr' % name)[:]
    shape = tuple(h5f.getNode('%s_shape' % name)[:])
    return csr_matrix((data, indices, indptr), shape = shape)

def load_h5f_array(h5f, name):
    try:
        return h5f.getNode(name)[:]
    except tb.exceptions.NoSuchNodeError:
        return np.array([])
    
def write_h5f_csr(h5f, h5fplace, name, atom, csr_mat):
    write_h5f_array(h5f, h5fplace, name + '_data', atom, csr_mat.data)
    write_h5f_array(h5f, h5fplace, name + '_indices', tb.Int32Atom(), csr_mat.indices)
    write_h5f_array(h5f, h5fplace, name + '_indptr', tb.Int32Atom(), csr_mat.indptr)
    write_h5f_array(h5f, h5fplace, name + '_shape', tb.Int32Atom(), np.array(csr_mat.shape))
    
def remove_h5f_csr(h5f, name):
    h5f.removeNode(name + '_data')
    h5f.removeNode(name + '_indices')
    h5f.removeNode(name + '_indptr')
    h5f.removeNode(name + '_shape')



def utf8_gzopen(filename, mode = 'r'):
    if mode == 'r':
        zf = gzip.open(filename)
        reader = codecs.getreader('utf-8')
        return reader(zf)
    elif mode == 'w':
        zf = gzip.open(filename, 'w')
        writer = codecs.getwriter('utf-8')
        return writer(zf)
    
def read_dict(f, splitf = lambda x: x.strip().split('\t'), kf = None, vf = None, commentf = None):
    '''
    Read a tab delimited kf(str) -> vf(str) dict.
    Pass in None to kf or vf to keep the original str.
    Removes leading and trailing whitespace.
    commentf is a function that returns True if a line is a comment
    '''
    if isinstance(f, str):
        f = open(f)
    d = {}
    for line in f.readlines():
        if len(line) <= 1:
            continue
        if commentf is not None and commentf(line):
            continue
        args = splitf(line)
        k = args[0]
        if kf is not None:
            k = kf(k)
        try:
            v = args[1]
        except:
            print args
            continue
        if vf is not None:
            v = vf(v)
        d[k] = v
    return d

def write_dict(towrite, f, kf = None, vf = None, close = True):
    '''
    Writes a dict to file
    '''
    if isinstance(f, str):
        f = open(f, 'w')
    for k, v in towrite.iteritems():
        if kf is not None:
            k = kf(k)
        if vf is not None:
            v = vf(v)
        f.write('%s\t%s\n' % (k, v))
    if close:
        f.close()
        
def read_word_freq(f):
    '''
    Read from a gzipped file with format
    word<tab>frequency
    
    Potential to do: cutoffs
    '''
    return read_dict(utf8_gzopen(f), vf = int)

def invert_bijection(d):
    '''
    Returns a dict where the key and value pairs have been reversed.
    Requres d to be a bijection.
    '''
    inv = {}
    for k, v in d.iteritems():
        assert v not in inv
        inv[v] = k
    return inv

def call_corenlp(corenlp_dir, filelist, output_dir, ssplit = True):
    '''
    This code works with the CoreNLP v3.4.1
    corenlp_dir: directory containing CoreNLP installation
    filelist: a text file containing the names of all the files of raw text to preprocess
    output_dir: where to write the output XML files
    ssplit: True --- get CoreNLP to split sentences. False --- use line breaks in the files as sentence boundaries
    '''
    print "Preprocessing corpus with CoreNLP"
    if ssplit:
        #cmd = "java -cp \"{0}stanford-corenlp-2012-05-22.jar;{0}stanford-corenlp-2012-05-22-models.jar;{0}xom.jar;{0}joda-time.jar\" -Xmx4g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref -filelist {1} -outputDirectory {2} -noClobber"
        cmd = "java -cp \"{0}stanford-corenlp-VV.jar;{0}stanford-corenlp-VV-models.jar;{0}xom.jar;{0}joda-time.jar;{0}jollyday.jar;{0}ejml-0.23.jar\" -Xmx4g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref -filelist {1} -outputDirectory {2} -noClobber"
        # 
    else:
        # use EOL as new sentence break
        #cmd = "java -cp \"{0}stanford-corenlp-2012-05-22.jar;{0}stanford-corenlp-2012-05-22-models.jar;{0}xom.jar;{0}joda-time.jar\" -Xmx4g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref -ssplit.eolonly -filelist {1} -outputDirectory {2} -noClobber"
        cmd = "java -cp \"{0}stanford-corenlp-VV.jar;{0}stanford-corenlp-VV-models.jar;{0}xom.jar;{0}joda-time.jar;{0}jollyday.jar;{0}ejml-0.23.jar\" -Xmx4g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref -ssplit.eolonly -filelist {1} -outputDirectory {2} -noClobber"
    
    cmd = cmd.replace('VV', '3.4.1')
    cmd = cmd.replace("{0}", corenlp_dir)
    cmd = cmd.replace("{1}", filelist)
    cmd = cmd.replace("{2}", output_dir)
    os.system(cmd)