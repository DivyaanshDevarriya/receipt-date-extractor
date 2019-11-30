from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
import base64
import pytesseract
from PIL import Image
import dateutil.parser as dparser
from itertools import islice
import re

pattern = re.compile('[\W_]+') # filter to keep only alphanumeric characters in a string

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('payload')

# function to read n(=3) strings together using sliding window
def window(seq, n=3):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

dates = {} # create dictionary to store dates from given img_64 content

class extract_date(Resource):
    def get(self):
        # use parser and find the user's query
        args = parser.parse_args()
        if(args['payload'] == None): # if no img_64 content provided then return message "No image provided"
            return {'message':'No image provided'}
        img_64 = args['payload'].encode()
        if(img_64 not in dates.keys()):# if given img_64 content is not in te dictionary than return message "Image not in database"
            return {'message': "Image not in database"}
        return {'date':dates[img_64]}# else return the date from the dictionary
    
    def post(self):
        args = parser.parse_args()
        img_64 = args['payload'].encode() # convert string img_64 content to bytes img_64 content
        image_64_decode = base64.decodestring(img_64) 
        image_result = open('img_decode.jpg', 'wb') # create a writable image and write the decoding result 
        image_result.write(image_64_decode)
        
        text = pytesseract.image_to_string(Image.open('img_decode.jpg')) # read text data on receipt
        text = pattern.sub('-', text) # replace all non-alphanumeric with '-'
        texts = text.split("-") # split the text using '-'
        
        date = []
        #s = []
        for value in window(texts,3): # read 3 strings together in the given list texts like texts[0], text[1] and texts[2] then texts[1] texts[2] texts[3]...
            item = ' '.join(value)
            try:
                #append date in the list date in the format YYYY-mm-dd
                date.append(dparser.parse(item).strftime('%Y-%m-%d')) # dparser parses the given string to return date if the string contains a date
                #s.append(item)
            except:
                continue
        if(date == []):
            dates[img_64] = "null" # if no date found in the entire text from receipt than store null
        else:
            #idea is that the first element in the list date contains the actual date in the receipt
            if(int(date[0].split("-")[0])<2000 or int(date[0].split("-")[0])>2019): #if year < 2000 or year > 2019 then check for second item in date
                if(len(date)!=1):
                    dates[img_64] = date[1] # if only one element is in the list date than store that element as date for given img_64 content
                else:
                    dates[img_64] = date[0]# else store first element of list date as date for given img_64 content
            else:
                dates[img_64] = date[0]# store first element in list date as date for given img_64 content
        return {'date' : dates[img_64]} 

api.add_resource(extract_date, '/')

if __name__ == '__main__':
    app.run(debug=True)
