import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

colors_list = [ '#BF3028',   '#5FF0F0', '#AFF820', '#FF8030', '#BF3028',  '#AFF820', '#5FF0F0', '#FF8030','#FFD030', '#EFC068', '#7FC850',  '#98D8D8', '#F85888']

time_data_to_plot = pd.read_csv("D:\\00Research\\00Fog\\004-Zara\\Her SLA\\Charts\\Comparison\\pplot-res-time-03-10-22.csv")

sns.set(font_scale = 2.5)
sns.set_style(style='white')
ax1 = sns.boxplot(x=" ", y="Response time (s)", hue="method", data=time_data_to_plot, width=0.75,palette=colors_list,fliersize=0)
#ax1.set_adjustable(hspace = 0.8)
handles, labels = ax1.get_legend_handles_labels()
plt.yticks([0,1,2,3])
plt.legend(handles[0:4], labels[0:4], loc='upper left',  fontsize=25)
#plt.margins(x=-0.32)
plt.show()

success_data_to_plot = pd.read_csv("D:\\00Research\\00Fog\\004-Zara\\Her SLA\\Charts\\Comparison\\pplot-success-03-10-22.csv")

sns.set(font_scale = 2.5)
sns.set_style(style='white')
ax1 = sns.boxplot(x=" ", y="Success rate", hue="method", data=success_data_to_plot, width=0.75,palette=colors_list,fliersize=0)
#ax1.set_adjustable(hspace = 0.8)
handles, labels = ax1.get_legend_handles_labels()
plt.yticks([0,0.2,0.4,0.6,0.8,1])
plt.legend(handles[0:4], labels[0:4], loc='lower left',  fontsize=25)
#plt.margins(x=-0.32)
plt.show()


deadline_data_to_plot = pd.read_csv("D:\\00Research\\00Fog\\004-Zara\\Her SLA\\Charts\\Comparison\\pplot-deadline-03-10-22.csv")

sns.set(font_scale = 2.5)
sns.set_style(style='white')
ax1 = sns.boxplot(x=" ", y="Deadline satisfaction rate", hue="method", data=deadline_data_to_plot, width=0.75,palette=colors_list,fliersize=0)
#ax1.set_adjustable(hspace = 0.8)
handles, labels = ax1.get_legend_handles_labels()
plt.yticks([0,0.2,0.4,0.6,0.8,1])
plt.legend(handles[0:4], labels[0:4], loc='lower left',  fontsize=25)
plt.show()