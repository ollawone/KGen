import os

from argparse import ArgumentParser
from sys import argv
from sys import path

from kb import KnowledgeBases

path.insert(0, '../')
from common.stanfordcorenlp.corenlpwrapper import CoreNLPWrapper
from common.nlputils import NLPUtils

class Linker:

    def link(self, input_filename, k_base='babelfy', verbose=False):
        if not input_filename.startswith('/'):
            input_filename = os.path.dirname(os.path.realpath(__file__)) + '/' + input_filename

        print('Processing text from {}'.format(input_filename))

        with open(input_filename, 'r') as input_file:
            contents = input_file.read()
            input_file.close()

        prefixes, links = KnowledgeBases(k_base).annotate(contents, verbose)

        np_entities, verbs = NLPUtils.extract_np_and_verbs(contents)
        entities_linked = self.__associate_np_to_entities(np_entities, links)
        verbs_linked = self.__associate_verbs_to_entities(verbs, links)

        output_filename = os.path.splitext(input_filename)[0] + '_links.txt'
        open(output_filename, 'w').close() # Clean the file in case it exists

        with open(output_filename, 'a') as output_file:
            for key in prefixes.keys():
                output_file.write('@PREFIX\t{}:\t<{}>\n'.format(prefixes[key], key))

            for key in verbs_linked.keys():
                output_file.write('@PREDICATE\t{};{}\n'.format(key.encode('utf-8'), verbs_linked[key]))

            for key in entities_linked.keys():
                output_file.write('@ENTITY\t{};{}\n'.format(key.encode('utf-8'), entities_linked[key]))
            output_file.close()
        print('Linked entities were stored at {}'.format(output_filename))

        return output_filename

    def __associate_np_to_entities(self, nps, links):
        nps_list = list(nps)
        nps_list.sort(key = len) # sort by string length

        np_entities = {}
        for np in nps_list:
            link_list = list()
            for key in links:
                if key.lower() == np.lower(): # exact match
                    link_list = [links[key]]
                    break;
                elif key.lower() in np.lower(): # composite
                    link_list.append(links[key])

            if not len(link_list) == 0:
                np_entities[np.lower()] = ','.join(link_list)

        for np in nps_list:
            if not np.lower() in np_entities.keys():
                np_entities[np.lower()] = 'notfound:' + np.lower().replace(' ', '_')

        return np_entities

    def __associate_verbs_to_entities(self, verbs, links):
        verbs_list = list(verbs)

        verbs_entities = {}
        for verb in verbs_list:
            for key in links:
                if verb.lower() in key.lower():
                    verbs_entities[verb.lower()] = links[key]
                    break

        for verb in verbs_list:
            if not verb.lower() in verbs_entities.keys():
                verbs_entities[verb.lower()] = 'notfound:' + verb.lower()

        return verbs_entities

def main(args):
    arg_p = ArgumentParser('python linker.py', description='Links the text entities to URIs from a knowledge base.')
    arg_p.add_argument('-f', '--filename', type=str, default=None, help='Text file')
    arg_p.add_argument('-k', '--kgbase', type=str, default='babelfy', help='Knowledge base to be used, e.g. babelfy (default) or ncbo')
    arg_p.add_argument('-v', '--verbose', action='store_true', help='Prints extra information')

    args = arg_p.parse_args(args[1:])
    filename = args.filename
    kg_base = args.kgbase
    verbose = args.verbose

    if filename is None:
        print('No file provided.')
        exit(1)

    linker = Linker()
    linker.link(filename, kg_base, verbose)

if __name__ == '__main__':
    exit(main(argv))
