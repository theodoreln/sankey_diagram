""" The goal of this file is to be able to import results from Balmorel and Optiflow and to plot the Sakey Diagram """

# Import needed extension for the creation of the Sankey Diagram
import gams.transfer as gt
import plotly.graph_objects as go
import plotly.io as pio
import re
import pandas as pd

# Open the Sankey Diagram in the browser
pio.renderers.default = 'browser'


""" Path to the file """
 
# results_path = 'C:/Users/theod/Documents/Documents importants/DTU/Job/Balmorel/Balmorel + Optiflow/20230914 Balmorel model/01 Balmorel model/base/model/'
# results_file_opti = 'Optiflow_MainResults_DK_WP' + '.gdx'
# results_file_bal = 'MainResults_DK_WP' + '.gdx'

results_path = 'C:/Users/theod/Documents/Documents importants/DTU/Job/Balmorel/Balmorel + Optiflow/20230914 Balmorel model/Old results/No differenciation with WP/'
results_file_opti = 'Optiflow_MainResults_DK+' + '.gdx'
results_file_bal = 'MainResults_DK+' + '.gdx'
csv_path = 'C:/Users/theod/Documents/Documents importants/DTU/Job/Balmorel/Balmorel + Optiflow/'
csv_file = 'Sankey_Diagram_Options.csv'

""" Uploading the GAMS file and the results we want to plot """

# Import results of a country and a given year
def Import_gams(results_file_path, df_name, column_country, select_country, column_year, select_year) :
    results = gt.Container(results_file_path)
    df = results.data[df_name].records
    df = df[df[column_country] == select_country]
    df = df[df[column_year] == select_year]
    df.reset_index(drop=True, inplace=True)
    return (df)

""" Importing the CSV file with all options for the sankey diagram plotting """

# Import and create four lists from the csv options file
def Import_csv(csv_path, csv_file, Options_plot) :
    CSV_df = pd.read_csv(csv_path+csv_file, sep=';')
    CSV_df = CSV_df[CSV_df['TYPE'].isin(Options_plot)]
    CSV_df.reset_index(drop=True, inplace=True)
    return(CSV_df)

""" Old version of the sankey diagram, without any modification """

# Going throught IPROCFROM and select each unique element + numbers of occurences
def Count_From(df) :
    L = []
    C = []
    for value in df['IPROCFROM'] :
        if value in L :
            i = L.index(value)
            C[i] += 1
        else :
            L.append(value)
            C.append(1)
    return(L,C)

# Going throught IPROCTO and select each unique element + numbers of occurences
def Count_To(df) :
    L = []
    C = []
    for value in df['IPROCTO'] :
        if value in L :
            i = L.index(value)
            C[i] += 1
        else :
            L.append(value)
            C.append(1)
    return(L,C)

# Construct a list with every unique element (node of the Sankey Diagram)
def Count(df) :
    Lf, _ = Count_From(df)
    Lt, _ = Count_To(df)
    L = []
    for value in Lf :
        if value not in L :
            L.append(value)
    for value in Lt :
        if value not in L :
            L.append(value)
    return(L)

# Construct the source, target and value lists to plot the Sankey Diagram
def sankey_data(df) :
    label = Count(df)
    source, target, value = [], [], []
    for i in range(len(df)) :
        if df['value'][i]>0.0001 :   
            source.append(label.index(df['IPROCFROM'][i]))
            target.append(label.index(df['IPROCTO'][i]))
            value.append(round(df['value'][i], 5))
    return(label, source, target, value)

# Function used to delete one final node of the sankey diagram (originally build to get rid of the money buffer)
def sankey_fnode_delete(label, source, target, value, value_to_delete):
    i = label.index(value_to_delete)
    k = 0
    while k == 0 :
        if i in target :
            j = target.index(i)
            del source[j]
            del target[j]
            del value[j]
        else :
            k = 1
    return label, source, target, value

# Old clean flow
def sankey_clean_flow(source, target, value) :
    flow = list(zip(source, target))
    source2 = []
    target2 = []
    value2 = []
    for i in range(len(flow)) :
        if value[i] != 0 :
            flow2 = list(zip(source2, target2))
            if flow[i] in flow2 :
                index = flow2.index(flow[i])
                value2[index] = value2[index] + value[i]
            else :
                source2.append(flow[i][0])
                target2.append(flow[i][1])
                value2.append(value[i])
    return(source2, target2, value2)  

""" Creating the lists for the sankey diagram """

# Creating the label list from the csv options file
def create_label(CSV_df) :
    label = []
    for var in CSV_df['FLOW_IN_FINAL'] :
        if var not in label :
            label.append(var)
    for var in CSV_df['FLOW_OUT_FINAL'] :
        if var not in label :
            label.append(var)
    return(label)

files = {'BAL' : results_path+results_file_bal,
         'OPTI' : results_path+results_file_opti}

color_sector = {'flow' : {'Fuel' : 'rgba(0, 255, 0, 0.4)',
                          'Elec' : 'rgba(0, 0, 255, 0.4)',
                          'DH' : 'rgba(255, 0, 0, 0.4)'},
                'node' : {'Fuel' : 'rgba(0, 255, 0, 0.4)',
                          'Elec' : 'rgba(0, 0, 255, 0.4)',
                          'DH' : 'rgba(255, 0, 0, 0.4)'}}

transform = {'BAL' : 3.6,
             'OPTI' : 1}

country = {'BAL' : 'C',
           'OPTI' : 'CCC'}

# Creating the flow lists from the csv options file
def create_flow(label, CSV_df, Country, Year) :
    n_flows = len(CSV_df['FLOW_IN_FINAL'])
    source = [0]*n_flows
    target = [0]*n_flows
    value = [0]*n_flows
    flow_color = [0]*n_flows
    node_color = [0]*len(label)
    for i in range(n_flows) :
        sector = CSV_df['TYPE'][i]
        df = Import_gams(files[CSV_df['FILE'][i]], CSV_df['DF'][i], country[CSV_df['FILE'][i]], Country, 'Y', Year)
        
        # Condition 1 
        if CSV_df['EXACT_1'][i] == 'Yes' :
            condition_1 = df[CSV_df['COLUMN_COND_1'][i]] == CSV_df['COND_1'][i]
            condition_1_out = pd.Series(True, index=df.index)
        else :
            condition_1 = df[CSV_df['COLUMN_COND_1'][i]].str.contains(CSV_df['COND_1'][i], case=False)
            list_1 = list(CSV_df['COND_1'])
            var_1 = CSV_df['COND_1'][i]
            exclude_1 = [name for name in list_1 if name != var_1 and name not in var_1]
            if not not exclude_1 :
                exclude_pattern_1 = '|'.join(r'\b{}\b'.format(re.escape(word)) for word in exclude_1)
                condition_1_out = ~df[CSV_df['COLUMN_COND_1'][i]].str.contains(exclude_pattern_1, case=False, regex=False )
            else :
                condition_1_out = pd.Series(True, index=df.index)
            
        # Condition 2
        if pd.notna(CSV_df['COLUMN_COND_2'][i]):
            if CSV_df['EXACT_2'][i] == 'Yes' :
                condition_2 = df[CSV_df['COLUMN_COND_2'][i]] == CSV_df['COND_2'][i]
                condition_2_out = pd.Series(True, index=df.index)
            else :
                condition_2 = df[CSV_df['COLUMN_COND_2'][i]].str.contains(CSV_df['COND_2'][i], case=False)
                list_2 = list(CSV_df['COND_2'])
                var_2 = CSV_df['COND_2'][i]
                exclude_2 = [str(name) for name in list_2 if str(name) != var_2 and str(name) not in var_2 and not pd.isna(name)]
                if not not exclude_2 :
                    exclude_pattern_2 = '|'.join(r'\b{}\b'.format(re.escape(word)) for word in exclude_2)
                    condition_2_out = ~df[CSV_df['COLUMN_COND_2'][i]].str.contains(exclude_pattern_2, case=False)
                else :
                    condition_2_out = pd.Series(True, index=df.index)
        else :
            condition_2 = pd.Series(True, index=df.index)
            condition_2_out = pd.Series(True, index=df.index)
            
        # Applying all conditions
        val = df.loc[condition_1 & condition_2 & condition_1_out & condition_2_out , 'value']
           
        # Exporting results
        if val.empty :
            source[i] = label.index(CSV_df['FLOW_IN_FINAL'][i])
            target[i] = label.index(CSV_df['FLOW_OUT_FINAL'][i])
            value[i] = 0
        else :
            source[i] = label.index(CSV_df['FLOW_IN_FINAL'][i])
            target[i] = label.index(CSV_df['FLOW_OUT_FINAL'][i])
            value[i] = sum(val.values.tolist())*transform[CSV_df['FILE'][i]]
        # Colors
        flow_color[i] = color_sector['flow'][sector]
        node_color[source[i]] = color_sector['node'][sector]
        if node_color[target[i]] == 0 :
            node_color[target[i]] = color_sector['node'][sector]
            
    return(source, target, value, flow_color, node_color)

    
""" Create only one flow when 2 similar flows """

def clean_flow(source, target, value, flow_color) :
    flow = list(zip(source, target))
    source2 = []
    target2 = []
    value2 = []
    flow_color2 = []
    for i in range(len(flow)) :
        if value[i] != 0 :
            flow2 = list(zip(source2, target2))
            if flow[i] in flow2 :
                index = flow2.index(flow[i])
                value2[index] = value2[index] + value[i]
            else :
                source2.append(flow[i][0])
                target2.append(flow[i][1])
                value2.append(value[i])
                flow_color2.append(flow_color[i])
    return(source2, target2, value2, flow_color2)               

""" Plot the Sankey Diagram """

def plot_sankey(label, source, target, value, flow_color, node_color, Country, Year) :
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 30,
          thickness = 10,
          line = dict(color = "black", width = 0.5),
          label = label,
          color = node_color
        ),
        link = dict(
          source = source,
          target = target, 
          value = value,
          color = flow_color
      ))])
    fig.update_layout(title_text=str(Country)+' - '+str(Year), font_size=10)
    fig.show()

""" For the final plotting """

def Plotting_oneyear_onecountry(csv_file, Country, Year, Options_plot):
    # Old version
    V_FLOW_C = Import_gams(files['OPTI'], 'VFLOW_Opti_C', 'CCC', 'NORWAY', 'Y', '2050')
    label, source, target, value = sankey_data(V_FLOW_C)
    label, source, target, value = sankey_fnode_delete(label, source, target, value, 'Money_buffer_T')
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 70,
          thickness = 10,
          line = dict(color = "black", width = 0.5),
          label = label
        ),
        link = dict(
          source = source,
          target = target, 
          value = value
      ))])
    fig.update_layout(title_text=str(Country)+' - '+str(Year)+' - Old', font_size=10)
    fig.show()
    # New version
    CSV_df = Import_csv(csv_path, csv_file, Options_plot)
    label = create_label(CSV_df)
    source, target, value, flow_color, node_color = create_flow(label, CSV_df, Country, Year)
    source, target, value, flow_color = clean_flow(source, target, value, flow_color) 
    plot_sankey(label, source, target, value, flow_color, node_color, Country, Year)
    
def Plotting_oneyear_sumcountries(csv_file, Year, Options_plot) : 
    # Old version
    results = gt.Container(files['OPTI'])
    df = results.data['VFLOW_Opti_C'].records
    df = df[df['Y'] == Year]
    df.reset_index(drop=True, inplace=True)
    countries = df['CCC'].unique().tolist()
    label2, source2, target2, value2 = [], [], [], []
    for count in countries :
        V_FLOW_C = Import_gams(files['OPTI'], 'VFLOW_Opti_C', 'CCC', count, 'Y', '2050')
        label, source, target, value = sankey_data(V_FLOW_C)
        label, source, target, value = sankey_fnode_delete(label, source, target, value, 'Money_buffer_T')
        for i in range (len(label)) :
            label_add = label[i]
            if label_add not in label2 :
                label2.append(label_add)
        for j in range(len(source)) :
            source_add = source[j]
            target_add = target[j]
            value_add = value[j]
            label_source = label[source_add]
            label_target = label[target_add]
            source2.append(label2.index(label_source))
            target2.append(label2.index(label_target))
            value2.append(value_add)
    source2, target2, value2 = sankey_clean_flow(source2, target2, value2)
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 70,
          thickness = 10,
          line = dict(color = "black", width = 0.5),
          label = label2
        ),
        link = dict(
          source = source2,
          target = target2, 
          value = value2
      ))])
    fig.update_layout(title_text='All Countries'+' - '+str(Year)+' - Old', font_size=10)
    fig.show()
    
    # New version
    results = gt.Container(files['OPTI'])
    df = results.data['VFLOW_Opti_C'].records
    df = df[df['Y'] == Year]
    df.reset_index(drop=True, inplace=True)
    countries = df['CCC'].unique().tolist()
    source2, target2, value2, flow_color2 = [], [], [], []
    CSV_df = Import_csv(csv_path, csv_file, Options_plot)
    label = create_label(CSV_df)
    for count in countries :
        source, target, value, flow_color, node_color = create_flow(label, CSV_df, count, Year)
        source, target, value, flow_color = clean_flow(source, target, value, flow_color) 
        for j in range(len(source)) :
            source_add = source[j]
            target_add = target[j]
            value_add = value[j]
            flow_color_add = flow_color[j]
            source2.append(source_add)
            target2.append(target_add)
            value2.append(value_add)
            flow_color2.append(flow_color_add)
    source2, target2, value2, flow_color2 = clean_flow(source2, target2, value2, flow_color2)
    plot_sankey(label, source2, target2, value2, flow_color2, node_color, 'All Countries', Year)


Options_plot = ['Fuel', 'Elec', 'DH']
Plotting_oneyear_onecountry(csv_file, 'NORWAY', '2050', Options_plot)
Plotting_oneyear_sumcountries(csv_file, '2050', Options_plot)


    