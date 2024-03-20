import nrrd
from operator import itemgetter
import pandas as pd


filename = "data\Drydisk07.6.nrrd"
#dataframe for knotdata
data = {  
        "KNOT NO.": [],
        "Knot ID in database": [],
        "Knot Diam": [],
        "Azimuth": [],
        "Knot type": [],
        "R1": [],
        "L1 a": [],
        "L1 b": [],
        "D1": [],
        "L2": [],
        "L3": [],
        "L4": [],
        "L5": [],
        "Count 1": []
}

header = nrrd.read_header(filename)    
# print (header)
# knottable = pd.DataFrame(header) 
# knottable = itemgetter(*data.keys())(header)
knottable = {key: header[key] for key in data.keys()}
print (knottable)
# for i in enumerate(knottable):
# print (i)