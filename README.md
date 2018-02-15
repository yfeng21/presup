# presup

- main method is at presup-src/src/presup.py, which generates negative and positive data from corpus
- argument options include corpus (default is ptb), output directory (required), subset(test/dev/train/all, default is all), and window size (default is 50, as specified in paper)
- please change the path of corpus in presup-src/utils/paths.py
- you may change the split of train/dev/test in presup-src/resources/ptb2.py (or any other corresponding corpus config script)
