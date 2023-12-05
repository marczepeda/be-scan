"""
Author: Calvin XiaoYang Hu
Date: 230906

{Description: taking in a gene file, generating guides, and filtering potential guides based on 
              PAM, availability of target residue in editing window, etc}
"""

import pandas as pd

from be_scan.sgrna._genomic_ import bases, cas_key
from be_scan.sgrna._guides_ import filter_guide, filter_repeats
from be_scan.sgrna._gene_ import GeneForCRISPR
from be_scan.sgrna._genomic_ import process_PAM, rev_complement, complements

# from be_scan.sgrna._genomic_ import complements
# from be_scan.sgrna._genomic_ import , complement, protein_to_AAseq, process_PAM, make_mutations
# from be_scan.sgrna._aminoacid_ import find_aa_edits_fwd, find_aa_edits_rev


def generate_BE_guides(gene_filepath, gene_name, 
                       cas_type, edit_from, edit_to, 
                       PAM=None, window=[4,8], 
                       output_name='guides.csv', output_dir=''
                       ): 
    """
    Generates a list of guides based on a gene .fasta file,
    and filtering these guides based on PAM and edit available
    in a given window. 

    Dataframe contains: 
       'sgRNA_seq'      : str,    the sequence of the guide fwd if on sense strand and rev if on antisense
       'starting_frame' : int,    (0, 1, 2) coding position of the first bp in fwd sgRNA or last bp in rev sgRNA
       'chr_pos'        : int,    the genome position of the first bp in a fwd sgRNA or last bp of a rev sgRNA
       'gene_pos'       : int,    the gene position of the first bp in a fwd sgRNA or last bp of a rev sgRNA
       'coding_seq'     : str,    the sense strand sequence of the guide, always fwd
       'exon'           : int,    the exon number according to the input gene_file
       'sgRNA_strand'   : str,    (ie sense or antisense)
       'gene_strand'    : str,    (ie plus or minus)
       'editing_window' : tuple,  the gene positions of the editing windows bounds inclusive
       'gene'           : str,    name of the gene
       'win_overlap'    : str,    where the window sits (Exon, Exon/Intron, Intron)

    Parameters
    ------------
    gene_filepath: str or path
        The file with the gene .fasta sequence
    gene_name: str
        The name of the gene, can be any string
    cas_type: str
        A type of predetermined Cas (ie Sp, SpG, SpRY, etc)
        This variable is superceded by PAM
    edit_from: char
        The base (ACTG) to be replaced
    edit_to: char
        The base (ACTG) to replace with
    PAM: str, default None
        Optional field to input a custom PAM or a known PAM
        This field supercedes cas_type
    window: tuple or list, default = (4,8)
        Editing window, 4th to 8th bases inclusive by default

    output_name : str or path, default 'guides.csv'
        Name of the output .csv guides file
    output_dir : str or path, defailt ''
        Directory path of the output .cs guides file

    Returns: 
    ------------
    df_no_duplicates : pandas dataframe
        Contains fwd and rev guides in 'sgRNA_seq', and columns 
        'starting_frame', 'sgRNA_pos', 'exon', 'sgRNA_strand', 
        'gene_strand', 'editing_window', 'gene', 'coding_seq'
    """

    # create gene object and parses all guides as preprocessing
    gene = GeneForCRISPR(filepath=gene_filepath)
    print('Create gene object from', gene_filepath)
    gene.parse_exons()
    print('Parsing exons:', len(gene.exons), 'exons found')
    gene.extract_metadata()
    gene.find_all_guides()
    print('Preprocessing sucessful')

    # process cas_type
    if cas_type not in list(cas_key.keys()): 
        raise Exception('Improper cas type input, the options are '+str(list(cas_key.keys())))
    
    # checks editing information is correct
    assert edit_from in bases and edit_to in bases
    edit = edit_from, edit_to
    
    # process PAM, PAM input overrides cas_type
    if PAM is None: 
        PAM = cas_key[cas_type]
    PAM_regex = process_PAM(PAM)

    # process window
    assert window[1] >= window[0] and window[0] >= 0 
    assert window[1] <= len(gene.fwd_guides[0][0])

    # filter for PAM and contains editable base in window
    #    (seq, frame012 of first base, index of first base, exon number)
    fwd_results = [g.copy() for g in gene.fwd_guides if filter_guide(g, PAM_regex, PAM, edit, window)]

    # filter for PAM and contains editable base in window 
    #    (seq, frame012 of last base, index of last base, exon number)
    rev_results = [g.copy() for g in gene.rev_guides if filter_guide(g, PAM_regex, PAM, edit, window)]

    # filter out repeating guides in fwd_results list
    fwd_results = filter_repeats(fwd_results)
    # filter out repeating guides in rev_results list
    rev_results = filter_repeats(rev_results)

    # adding extra annotations for fwd and rev
    for x in fwd_results: 
        x.append(x[0])
        x.append('sense')
        x.append(gene.strand)
        x.append((x[2]+window[0], x[2]+window[1]))
        x.append(gene_name)
        x.append("Exon" if (x[5][window[0]:window[1]+1].isupper()) else "Exon/Intron")
    for x in rev_results: 
        x.append(rev_complement(complements, x[0]))
        x.append('antisense')
        x.append(gene.strand)
        x.append((x[2]-window[0], x[2]-window[1]))
        x.append(gene_name)
        x.append("Exon" if (x[5][window[0]:window[1]+1].isupper()) else "Exon/Intron")


    # set column names for outputing dataframe
    column_names = ['sgRNA_seq', 'starting_frame', 
                    'chr_pos', 'gene_pos', 
                    'coding_seq', 'exon', 
                    'sgRNA_strand', 'gene_strand', 
                    'editing_window', 'gene', 
                    'win_overlap'
                    ]

    # delete entries with duplicates between fwd and rev guides
    df = pd.DataFrame(fwd_results + rev_results, columns=column_names)
    duplicate_rows = df.duplicated(subset='coding_seq', keep=False)
    df_no_duplicates = df[~duplicate_rows]

    # output df
    df_no_duplicates.to_csv(output_dir + output_name)
    return df_no_duplicates


# # this is the main function for taking in lists of guides, 
# # then annotating all their predicted edits
# def annotate_BE_guides(protein_filepath, fwd_guides, rev_guides, edit_from, edit_to, window=[4,8]): 
#     ### ADD DOCS
#     # Parameters
#     #    protein_filepath: filepath to an amino acid sequence corresponding to gene file
#     #    fwd_guides, rev_guides: generated from identify_guides
#     #    edit_from: the base (ACTG) to be replaced
#     #    edit_to: the base (ACTG) to replace with
#     #    window: editing window, 4th to 8th bases inclusive by default
#     # outputs: a dataframe
    
#     ### target_codons: list of codons that we want to make with our base edit

#     # codon indices, predicted edits made
#     amino_acid_seq = protein_to_AAseq(protein_filepath)
#     num_aa = 3 # this is the num of amino acids we look ahead in our frame

#     for g in fwd_guides: 
#         # mutates all residues according to the mode, every combination of residue mutations
#         original = g[0][:12] # a string
#         guide_window = g[0][window[0]-1:window[1]] # a string
#         mutateds = [g[0][:window[0]-1] + m + g[0][window[1]:12] for m in make_mutations(guide_window, edit_from, edit_to)] # list of strings 

#         # compares the residues to find which amino acids were altered and catalogs them
#         edits, edit_inds = [], [] # lists of lists, of all edits for all possible mutations
#         start = (-1*g[1])+3
#         orig = original[start:start+(num_aa*3)]
#         for m in mutateds: 
#             # for each possible mutation, come up with the list of amino acid changes
#             edit, edit_ind = find_aa_edits_fwd(m, g, start, orig, num_aa, amino_acid_seq)
#             edits.append(edit)
#             edit_inds.append(edit_ind)
#         # append all information to dataframe
#         g.extend([edits, edit_inds, 'fwd'])
#         assert(len(g)) == 7
        
#     for g in rev_guides: 
#         # mutates all residues according to the mode, every combination of residue mutations
#         original = g[0][:12] # a string
#         guide_window = g[0][window[0]-1:window[1]] # a string
#         mutateds = [g[0][:window[0]-1] + m + g[0][window[1]:12] for m in make_mutations(guide_window, edit_from, edit_to)] # a list of strings

#         # compares the residues to find which amino acids were altered and catalogs them
#         edits, edit_inds = [], [] # lists of lists, of all edits for all possible mutations
#         start = g[1]+1
#         orig = rev_complement(complements, original[start:start+(num_aa*3)])
#         for m in mutateds: 
#             # for each possible mutation, come up with the list of amino acid changes
#             edit, edit_ind = find_aa_edits_rev(m, g, start, orig, num_aa, amino_acid_seq)
#             edits.append(edit)
#             edit_inds.append(edit_ind)
#         # append all information to dataframe
#         g.extend([edits, edit_inds, 'rev'])
#         assert(len(g)) == 7
        
# #     print(pd.DataFrame(fwd_guides + rev_guides))
#     return pd.DataFrame(fwd_guides + rev_guides)
