import pandas as pd
import os
from _boxes_ import plot_boxes
from _annotating_ import annotate_submuttype, annotate_in_domain, calc_negative_controls


### INPUTS

in_ref = '../Downloads/NZL10196_v9_comparisons.csv'
interface_list = '../Downloads/3A-3L_interface_residues.txt'
cat_list = '../Downloads/Cat_pocket_residues.txt'
in_reps = '../Downloads/NZL10196_v9_t0norm_reps.csv' #t0 normalized
in_cond = '../Downloads/NZL10196_v9_t0norm_conds.csv' #t0 norm. and averaged

# list of domains
domains_list = ['PWWP','ADD','MTase']
# Define list of annotations
list_annocols = ['sgRNA_ID', 'Gene', 'Targeted_exon', 'C_count', 'is_C',
                 'Splice_check', 'Mut_type', 'Edit_site_3A1', 'Domain', 'in_domain',
                 'submut_type']
# Define list of comparisons
list_compnames = ['d3-pos', 'd3-neg', 'd6-pos', 'd6-neg', 'd9-pos', 'd9-neg']

df_data = pd.read_csv(in_ref)
df_reps = pd.read_csv(in_reps)
df_cond = pd.read_csv(in_cond)

out_prefix = '../Downloads/'
plot_window = (224, 912)
plot_name='DNMT3A_in_domain'

neg_ctrl_category = "NON-GENE"
y_value = 'log2_fc'






# Implement extra annotations necessary for plotting

df_data = df_data.assign(submut_type = df_data.apply(
    lambda x: annotate_submuttype(x.Mut_type, x.Gene), axis=1)) ### what is the point when Gene col has this info

df_data = df_data.assign(in_domain = df_data.apply(
    lambda x: annotate_in_domain(x.Domain, domains_list), axis=1))

df_not_normalized = df_data.copy()

print(df_data)





# Normalize data to intergenic controls
# calculate negative control stats
df_negctrl, list_negctrlstats, avg_dict = calc_negative_controls(df_data, list_compnames, neg_ctrl_category)
# perform normalization
for comp in list_compnames:
    df_data[comp] = df_not_normalized[comp].sub(avg_dict[comp])
# tidy data
list_cols = list_annocols + list_compnames
df_ordered = df_data[list_cols].copy()
df_tidy = df_ordered.melt(id_vars=list_annocols,
                          value_vars=list_compnames,
                          var_name='comparison',
                          value_name=y_value)





# Plotting function calls

# Side-by-side scatter- and box-plots. The scatter shows only Exonic, Yes C guides.
# The boxplot shows everything except essential controls by submut_type.
# For the scatter, only plot residues between 224-912 (proper DNMT3A2)

plot_boxes(df_input=df_tidy.loc[df_tidy['Mut_type']=='Missense'],
           plot_x_list=list_compnames, y_val=y_value, 
           cat_col='in_domain', hue_order=['in domain','not in domain'], palette=None,
           plot_name=plot_name, out_prefix=out_prefix, 
           list_negctrlstats=list_negctrlstats, jitter=0.25, dimensions=(2,4))




df_tidy_trim = df_tidy.loc[(df_tidy['Edit_site_3A1']>=plot_window[0]) & (df_tidy['Edit_site_3A1']<=plot_window[1])].copy()

# ColorBrewer2, 9 data classes, qualitative, 4th color scheme hex codes
color_list = ['#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9',
              '#8dd3c7', '#ffffb3', '#bebada', '#bc80bd']

# Additional information for analysis of samples/replicates/conditions:
list_samples = [
    'NL0',
    'NL1', 'NL10', 'NL19', 'NL2', 'NL11', 'NL20', 'NL3', 'NL12', 'NL21',
    'NL4', 'NL13', 'NL22', 'NL5', 'NL14', 'NL23', 'NL6', 'NL15', 'NL24',
    'NL7', 'NL16', 'NL25', 'NL8', 'NL17', 'NL26', 'NL9', 'NL18', 'NL27'
    ]
list_conds = [
    'd0',
    'd3-uns', 'd3-pos', 'd3-neg',
    'd6-uns', 'd6-pos', 'd6-neg',
    'd9-uns', 'd9-pos', 'd9-neg'
    ]

# Dictionary that maps condition names to sample IDs for PCA
dict_conds = {'d0':list_samples[0],
              'd3-uns':list_samples[1:4], 'd3-pos':list_samples[4:7], 'd3-neg':list_samples[7:10],
              'd6-uns':list_samples[10:13], 'd6-pos':list_samples[13:16], 'd6-neg':list_samples[16:19],
              'd9-uns':list_samples[19:22], 'd9-pos': list_samples[22:25], 'd9-neg': list_samples[25:]}
