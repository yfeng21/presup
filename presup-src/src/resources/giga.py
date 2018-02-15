import os
import glob
from utils.data_structures import read_corenlp_doc

import random

class PTB2Corpus:
    def __init__(self, root_d):
        self.root_d = root_d

    def doc_iter(self, subset = 'all',control=1):
        if subset == 'toy':
            sections = [0];



        for section in sections:
            subfolder = '%02d' % section
            fs = glob.glob(os.path.join(self.root_d, subfolder, '*.xml'))
            fs.sort()
            #####
            if control:
                # fs_index = range(len(fs))
                # random.shuffle(fs_index)
                # fs_new = [fs[x] for x in fs_index]
                fs_new=random.sample(fs,len(fs))
                fs = fs_new
            #####
            for f in fs:
                _, tail = os.path.split(f)
                yield read_corenlp_doc(f, tail)