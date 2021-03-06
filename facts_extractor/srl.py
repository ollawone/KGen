from sys import path

path.insert(0, '../')
from common.nlputils import NLPUtils
from common.senna.sennawrapper import SennaWrapper
from common.triple import Triple

class SemanticRoleLabeler:

    def extract(self, input_filename, output_filename, verbose=False):
        return self.__senna(input_filename, output_filename, verbose)

    def __senna(self, input_filename, output_filename, verbose=False):
        if verbose:
            print('Performing Sentence Role Labeling with SENNA...')

        senna = SennaWrapper()

        out_contents = ''
        with open(input_filename, 'r') as input_file:
            sentence_number = 0
            for line in input_file.readlines():
                if len(line) < 1:
                    continue

                senna_output = senna.srl(line, verbose=False)
                for predicate in senna_output.keys():
                    pred_args = senna_output[predicate]
                    pred_arg_names = NLPUtils.get_verbnet_args(predicate, verbose)
                    if len(pred_arg_names) < 1:
                        print('WARNING -- Unable to retrieve predicate arg names for "{}"'.format(predicate))

                    if verbose:
                        print('predicate: {}, args: {}'.format(predicate, pred_args))

                    for pred_arg in pred_args: # iterating over list of tuples
                        if pred_arg[0].startswith('AM-'): # Adjuncts
                            #if 'AM-NEG' == pred_arg[0]: # Check https://etd.ohiolink.edu/!etd.send_file?accession=osu1430876809&disposition=inline
                            #    predicate = 'not {}'.format(predicate)
                            #else:
                            #    predicate = ' '.join([pred_arg[1].strip(), predicate])

                            # Remove initial stopwords (e.g. determiners)
                            s = pred_arg[1].strip()
                            split = s.split(' ', 1)

                            while NLPUtils.is_stopword(split[0]) and len(split) > 1:
                                s = s.split(' ', 1)[1]
                                split = s.split(' ')

                            triple = Triple(sentence_number, predicate, 'local:{}'.format(pred_arg[0]), s)
                            if verbose:
                                print(triple.to_string())

                            out_contents += triple.to_string() + '\n'

                        elif pred_arg[0].startswith('C-'): # Continuities
                            print('Ignoring Continuity')
                        elif pred_arg[0].startswith('R-'): # References
                            print('Ignoring Reference')
                        elif pred_arg[0].startswith('V'): # Verbs
                            print('Ignoring Verb')
                        else: # Arguments (A0, A1, A2, etc.)
                            # Remove initial stopwords (e.g. determiners)
                            s = pred_arg[1].strip()
                            split = s.split(' ', 1)

                            while NLPUtils.is_stopword(split[0]) and len(split) > 1:
                                s = s.split(' ', 1)[1]
                                split = s.split(' ')

                            role_index = int(pred_arg[0][-1])
                            try:
                                role = pred_arg_names[role_index]
                            except IndexError:
                                print('No role index found for {}. Falling back to defaults!'.format(pred_arg[0]))
                                if role_index == 0:
                                    role = 'subject'
                                elif role_index == 1:
                                    role = 'object'
                                elif role_index == 2:
                                    role = 'indirect_object'
                                else:
                                    role = 'other'
                            triple = Triple(sentence_number, predicate, 'vn.role:{}'.format(role), s)
                            if verbose:
                                print(triple.to_string())

                            out_contents += triple.to_string() + '\n'

                sentence_number += 1

            input_file.close()

        with open(output_filename, 'w') as output_file:
            output_file.write(out_contents)
            output_file.close()

        return output_filename
