import pandas as pd
import os
import seaborn as sns
import matplotlib as mpl

from _boxes_ import plot_boxes
from _correlation_heatmap_ import plot_corr_heatmap
from _annotating_ import annotate_submuttype, annotate_in_domain, calc_negative_controls
from _correlation_scatter_ import plot_corr_scatter
from _scatterplot_ import plot_scatterplot

from _clustering_ import calc_centroids, calc_pairwise_dist

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





# sns mpl params
sns_context='paper'
sns_palette='deep'
pdf_font_size=42
ps_font_size=42
mpl_font='Arial'

# Plotting parameters and variables
sns.set_context(sns_context)
sns.set_palette(sns_palette)
mpl.rcParams['pdf.fonttype'] = pdf_font_size
mpl.rcParams['ps.fonttype'] = ps_font_size
mpl.rcParams['font.sans-serif'] = [mpl_font]

##################################################

# Plotting function calls

# Side-by-side scatter- and box-plots. The scatter shows only Exonic, Yes C guides.
# The boxplot shows everything except essential controls by submut_type.
# For the scatter, only plot residues between 224-912 (proper DNMT3A2)
plot_boxes(df_input=df_tidy.loc[df_tidy['Mut_type']=='Missense'],
           plot_x_list=list_compnames, y_val=y_value, 
           cat_col='in_domain', hue_order=['in domain','not in domain'], palette=None,
           plot_name=plot_name, out_prefix=out_prefix, 
           list_negctrlstats=list_negctrlstats, jitter=0.25, dimensions=(2,4))

##################################################

# ColorBrewer2, 9 data classes, qualitative, 4th color scheme hex codes
color_list = ['#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', 
              '#d9d9d9', '#8dd3c7', '#ffffb3', '#bebada', '#bc80bd']
# Define lists to use for setting plotting parameters
list_muttypes = ['Nonsense', 'Missense', 'Silent', 'Non-exon', 'Splice', 
                 'No_C/Exon', 'No_C/Non-exon', 'Control']
list_subtypes = ['Nonsense', 'Missense', 'Silent', 'Non-exon', 'Splice', 
                 'No_C/Exon', 'No_C/Non-exon', 'Intergenic', 'Non-targeting', 'Essential']


df_tidy_trim = df_tidy.loc[(df_tidy['Edit_site_3A1']>=plot_window[0]) & (df_tidy['Edit_site_3A1']<=plot_window[1])].copy()

plot_scatterplot(df_scatter=df_tidy_trim.loc[df_tidy_trim['Mut_type'].isin(list_muttypes[:3])],
                plot_col='comparison', hue_col='Mut_type', 
                xval='Edit_site_3A1', yval='log2_fc', xlab='Amino Acid Position', ylab='sgRNA Score', 
                hue_order_s=list_muttypes[:3], palette_s=color_list[:3],
                plot_x_list=list_compnames, list_negctrlstats=list_negctrlstats,
                plot_name='DNMT3A', out_prefix=out_prefix
                )

##################################################


# Keep only data (raw log2 or condition values) columns of dataframes and re-order
#df_reps = df_reps[list_samples]
list_compnames = ['d3-pos', 'd6-pos', 'd9-pos', 'd3-neg', 'd6-neg', 'd9-neg']
df_comp = df_data[list_compnames].copy()
plot_type = 'spearman'
plot_name = 'Spearman Correlation Heatmap'
line_pos = [2,4]
heatmap_center = 0

# Plot correlation heatmaps
# Spearman by comparisons (log2 fold change relative to unsorted)
plot_corr_heatmap(df_input=df_comp, plot_type=plot_type,
                  plot_name=plot_name, out_prefix=out_prefix, 
                  line_pos=line_pos, center=heatmap_center)

##################################################

subtypes = 'submut_type'
xmin, xmax, ymin, ymax = -1, 1, -1.5, 2

cond1, cond2, name1, name2 = 'd3-neg', 'd9-pos', 'd3-neg score', 'd9-pos score'

# Correlation scatter plots
# Correlation between d9-pos and d3-neg samples (each lfc from same-day unsorted)
plot_corr_scatter(df_input=df_data.loc[df_data[subtypes].isin(list_subtypes[:7])],
                  x_col=cond1, x_name=name1,
                  y_col=cond2, y_name=name2,
                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                  out_prefix=out_prefix, out_suffix='comps', hue_col=subtypes,
                  hue_order=list_subtypes[6::-1], palette=color_list[6::-1])

cond1, cond2, name1, name2 = 'd6-pos', 'd9-pos', 'd6-pos score', 'd9-pos score'

plot_corr_scatter(df_input=df_data.loc[df_data[subtypes].isin(list_subtypes[:7])],
                  x_col=cond1, x_name=name1,
                  y_col=cond2, y_name=name2,
                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                  out_prefix=out_prefix, out_suffix='comps', hue_col=subtypes,
                  hue_order=list_subtypes[6::-1], palette=color_list[6::-1])






# Structures and parameters to use for PWES calculations
struct_A = '4U7T'
struct_B = '4U7P'
clust_num = 8
std, m, theta = (16,2,0.8) #(std, m, theta)

in_comps = '220407_NZL10196_Analysis_v9_Full.csv'
df_comps = pd.read_csv(in_comps)

d_norm = 'd9pos_norm'
d = 'd9-pos'

df_comps[d_norm] = df_comps[d].copy()
df_missense = df_comps.loc[df_comps['Mut_type'] == 'Missense'].copy()
# Round edit sites to whole numbers (0.5 rounded to nearest even) and convert
# to long isoform numbering (note: 3A2 residues <25 don't map, but these
# will be filtered out later since no structure extends to this region).
df_missense['Clust_site'] = df_missense['Edit_site_3A2'].round(decimals=0)
df_missense['Clust_site'] = df_missense['Clust_site'].add(189)

# Get centroids
# 4U7T: chains A/C are both 3A. C has 1 less unresolved aa, though no guide maps to it.
df_centroids_A = calc_centroids(pdb_id=struct_A, aa_sel='chain C and resi 476-912')
# 4U7P: chain A is 3A
df_centroids_B = calc_centroids(pdb_id=struct_B, aa_sel='segi A')

# Calculate pairwise distances
df_pwdist_A = calc_pairwise_dist(df_centroids_A)
df_pwdist_B = calc_pairwise_dist(df_centroids_B)

# Filter guides to only those that map to residues resolved in...
# Structure A only
#df_lfc_A = df_missense.loc[df_missense['Clust_site'].isin(df_pwdist_A.index)].copy()
#df_lfc_A = df_lfc_A.sort_values(by=['Clust_site', 'sgRNA_ID']).reset_index()
# Structure B only
#df_lfc_B = df_missense.loc[df_missense['Clust_site'].isin(df_pwdist_B.index)].copy()
#df_lfc_B = df_lfc_B.sort_values(by=['Clust_site', 'sgRNA_ID']).reset_index()
# Both Structure A and Structure B
df_lfc_AB = df_missense.loc[df_missense['Clust_site'].isin(df_pwdist_A.index)].copy()
df_lfc_AB = df_lfc_AB.loc[df_lfc_AB['Clust_site'].isin(df_pwdist_B.index)]
df_lfc_AB = df_lfc_AB.sort_values(by=['Clust_site', 'sgRNA_ID']).reset_index()

##################################################
##################################################
##################################################
##################################################








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

# df_data.to_csv(out_prefix+'_Full.csv', index=False)
