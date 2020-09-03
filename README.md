# test_cb_plus

## Description
You can find in the repository a py file that contains all the code necessary for the first part. You can also find the dataset used to run the script. 
I renamed the files by replacing blank space by '_': 'references_initialized_in_shop.csv' and 'retailer_extract_vLB.xls'. 

## Install and run 
1. Create a virtual environment
2. Open the virtual environment
3. Use de pipefile to install all the dependencies
4. Run `python run.py ` 

File names are added as default arguments but you can also choose the add them as arguments in the command line as follow :

`python run.py references_initialized_in_shop.csv retailer_extract_vLB.xls `  


## Results
The references suggested for initialized are display on the shell and are also saved in a csv file, named 'recommendation_for_initialization.csv',  on the current directory. 
