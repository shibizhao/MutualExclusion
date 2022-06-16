"""
    Parse input arguments
"""

import argparse


class Options:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Mutual Exclusion Demo')

        parser.add_argument("--algorithm", type=str, help="select algorithm (LA for Lamport & RA for Ricart Agrawala)", default='LA')
        parser.add_argument("--node_num", type=int, help="the number of nodes", default=4)
        parser.add_argument("--runtime", type=int, help="the number of visit CS for each node", default=1)
        parser.add_argument("--begin_port", type=int, help="socket port", default=30000)
        
        self.parser = parser

    def parse(self):
        return self.parser.parse_args()
