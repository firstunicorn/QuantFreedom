1) When creating any test files, add this files to quantfreedom\enums\__init__.py like this:

from quantfreedom.enums.YOUR_NAME_OF_FILE import *


2) Make sure VENV shows up after terminal command jupyter --paths

3) make sure VENV shows up after you run this in cell:

# importing module
import sys


# printing all paths
sys.path

4) Make sure you are using CMD terminal and NOT PowerShell for installing VNV

5) Background color in Plotly Dash changing in tests\assets\custom.css

6) Setup VENV:
python -m venv qfFree
then:
qfFree\Scripts\activate
then:
ipython kernel install --user --name=qfFree


7) For installing talib - download https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
(latest version for your Python version)
then:
put it to your VENV folder and 
then:
pip install TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
---
where instead of TA_Lib-0.4.24-cp310-cp310-win_amd64.whl - YOUR NAME OF DOWNLOADED FILE

8) Use format  '/YOUR_FOLDER_NAME_OF_VENV/QuantFreedom/tests/data/30min.csv' for CSV file

9) To make sync all changes and push it to Github, open Source Control and then Fetch everything, then -> Remotes -> unfold Origin, right click on  Dev, than Merge Branch in to Current branch... 



Adding in __init__.py any folders with my own functions 
# Most important classes
from quantfreedom.nax_qf import *