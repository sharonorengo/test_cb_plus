import argparse
import pandas as pd
import numpy as np
import re


def build_assortment_df(data_ref_table):
  """
  Return a dataset containing only product references that have non null stock quantity 

  Keyword arguments: 

  data_ref_table -- dataframe containing all the referecens of the retailer with at least on column named "Stock en quantité" and on column name "reference_id" 

  """
  assortment = data_ref_table[data_ref_table["Stock en quantité"] != 0 ] ## A vérifier si pas >0 uniquement
  assortment = assortment.rename(columns={'EAN': 'reference_id'})
  return assortment


def merge_data_by_ref(data_initialized_ref, data_ref_table):
  """
  Return a merged dataset on column 'reference_id' 

  Keyword arguments: 

  data_initialized_ref -- dataframe containing all the referecens initialized in the app 
  data_ref_table -- dataframe containing all the references of the shop
  """

  df_initialised_merged = pd.merge(data_initialized_ref, data_ref_table, on = 'reference_id', how = 'left')

  return  df_initialised_merged


def add_column_define_status_initialisation(assortment, df_initialised_merged ):
  """
  Add a column to the assortment dataset to record  the status of the initialisation (if the reference is initialzed or not)

  Keyword arguments: 

  assortment -- dataframe containing all the references of the assortment of the shop
  df_initialised_merged -- dataframe containing all the referecens initialized in the app 
  """

  assortment['Etat_initialisation'] = False
  assortment.reset_index(drop = True, inplace = True)
  reference_prod_initialise = df_initialised_merged.reference_id

  for i in range(assortment.shape[0]): 
    if assortment.reference_id[i] in np.asarray(reference_prod_initialise):
      assortment.at[i, 'Etat_initialisation'] = True

  return assortment


def add_column_define_status_prod_initialise(assortment_non_initialise, df_initialised_merged ): 
  
  """
  Add a column to the dataset that only contains reference og the assortment that are not initialized
  dataset to record  the status of the initialisation (if the reference is initialzed or not)

  Keyword arguments: 

  assortment_non_initialise -- dataframe containing all the references of the assortment of the shop
  df_initialised_merged -- dataframe containing all the referecens initialized in the app 
  
  """

  assortment_non_initialise['Famille_produit_initialise'] = False
  list_group_famille_initialised = df_initialised_merged['Code Famille '].unique()

  list_group_famille_initialised = list_group_famille_initialised[~np.isnan(list_group_famille_initialised)]


  assortment_non_initialise.reset_index(drop = True, inplace = True)

  for i in range(len(assortment_non_initialise['Famille_produit_initialise'])):
    if assortment_non_initialise['Code Famille '][i].astype('float64') in list_group_famille_initialised:
      assortment_non_initialise.at[i, 'Famille_produit_initialise'] = 'True'

  return assortment_non_initialise

def preprocessing(data_initialized_ref , data_ref_table ):
  """
  Return a dataset containing a few changes in the data
  Keyword arguments: 

  data_initialized_ref -- dataframe containing all the references initialized in the app 
  data_ref_table -- dataframe containing all the references of the retailer 
  """
  df_initialised = pd.read_csv(data_initialized_ref,sep=',\"', engine = 'python').replace('"', '',regex=True)
  df_initialised.columns = df_initialised.columns.str.strip('"')
  df_initialised.iloc[1440,2] = 3700000000000 

  df_initialised['reference_id'] = pd.to_numeric(df_initialised['reference_id'])


  df_references = pd.read_excel(data_ref_table)
  df_references = df_references.rename(columns={'EAN': 'reference_id'})


  return df_initialised, df_references



def nb_element_in_each_family(data, name):

  data_prop = data[['Code Famille ', 'Code Sous-Famille ', 'reference_id']]

  data_prop = data_prop.groupby(['Code Famille ', 'Code Sous-Famille ']).nunique()

  data_prop = data_prop.rename(columns = {'reference_id': 'total_element_'+ name})

  return data_prop


def calculate_proportion(dataset, new_column_name):
    data_prop = dataset.fillna(0)
    data_prop[new_column_name] = data_prop.total_element_init / dataset.total_element_assort
    return data_prop

def get_proportion(dataset, threshold):
  data_high_proportion = dataset.loc[dataset['proportion'] > threshold]
  data_high_proportion['codes'] = data_high_proportion.index

  return data_high_proportion

def get_list_family_codes(dataset):
  ref_good_proportion = dataset.codes
  ref_good_proportion = str(ref_good_proportion)

  pattern = '\(\d{4}.\d, \d\)'

  ref_good_proportion = re.findall(pattern, ref_good_proportion)

  return ref_good_proportion


def define_codes_family(dataset):
  dataset.reset_index(drop = True, inplace = True)
  dataset['codes'] = str("")
  
  for i in range(dataset.shape[0]):
    text = '('+ str(dataset['Code Famille '][i].astype('float64'))+', '+str(dataset['Code Sous-Famille '][i]) +')'
    dataset.at[i, 'codes'] = text

  return dataset

def final_ref(dataset, ref_prop):
  result = dataset.loc[dataset['codes'].isin(np.asarray(ref_prop))]
  return result


def Main():
  parser = argparse.ArgumentParser()
  
  # Define command line arguments with default values
  parser.add_argument('initialized', help='Input file name for initialized references',  nargs='?',  default="references_initialized_in_shop.csv", type = str )  
  parser.add_argument('ref', help='Input file name for the reference table of the shop',  nargs='?',  default="retailer_extract_vLB.xls", type = str)
  args = parser.parse_args()

  # Use the different function to find the result
  df_initialised, df_references = preprocessing(args.initialized, args.ref)

  # Dataframe that contains references of the assortment
  assortment = build_assortment_df(df_references)

  # Dataframe that contains intialiased values merged with columns of the references tables to get different values such as ....
  df_initialised_merged = merge_data_by_ref(df_initialised, df_references)

  # Add column to assortment to define if the reference has been initialised in the app
  assortment = add_column_define_status_initialisation(assortment, df_initialised_merged )

  # Keep only reference that are not initialized yet
  assortment_non_initialise = assortment[assortment["Etat_initialisation"] != True ]

  # Add column to non initialsed references to define if the family code of the references is part of the family codes that has been initialsed and thus 
  # that need to be suggested to be initiased by the algorithm
  assortment_non_initialise = add_column_define_status_prod_initialise(assortment_non_initialise, df_initialised_merged )

  # Results containing only the reference non initialised and for which the family code is meaningful and need to be suggested for initialisation
  ref_same_group_family_as_in_assort = assortment_non_initialise[assortment_non_initialise["Famille_produit_initialise"] == True ]

  # Calculate the proportions
  data_tot_assort = nb_element_in_each_family(assortment, 'assort')
  data_tot_init = nb_element_in_each_family(df_initialised_merged, 'init')
  data_tot_merge = data_tot_assort.merge(data_tot_init, how='outer', left_index=True, right_index=True)
  data_prop = calculate_proportion(data_tot_merge, 'proportion')

  # Get table containing only references with high proprotion
  data_high_proportion = get_proportion(data_prop, 0.3)
  
  # Get list of family group of the references higly represented 
  list_family_good_proportion = get_list_family_codes(data_high_proportion)
  data_with_family_code = define_codes_family(ref_same_group_family_as_in_assort)

  # Final result of references to suggest for initialization to the uses
  final_reference = final_ref(ref_same_group_family_as_in_assort, list_family_good_proportion)

  # Save result in a csv file
  final_reference.to_csv('recommendation_for_initialization.csv', sep=',', encoding='utf-8')


  # Return the result in the shell command
  print( "Here are some product references that could be interesting for you to initialize in the app to track expiry dates :"+str(final_reference['Article Libellé Long']))
  print( "You can find in the current folder a csv file, named 'recommendation_for_initialisation.csv' that contains more details about these references.")

  
if __name__ == '__main__':
  Main()
