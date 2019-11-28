from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
import base64
import pytesseract
from PIL import Image
import dateutil.parser as dparser
from itertools import islice
import re

pattern = re.compile('[\W_]+')

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('payload')

def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

dates = {}

class extract_date(Resource):
    def get(self):
        # use parser and find the user's query
        args = parser.parse_args()
        img_64 = args['payload'].encode()
        if(img_64 not in dates.keys()):
            return {'message': "Image not in database"}
        return {'date':dates[img_64]}
    def post(self):
        args = parser.parse_args()
        img_64 = args['payload'].encode()
        image_64_decode = base64.decodestring(img_64) 
        image_result = open('img_decode.jpg', 'wb') # create a writable image and write the decoding result 
        image_result.write(image_64_decode)
        
        text = pytesseract.image_to_string(Image.open('img_decode.jpg'))
        text = pattern.sub('-', text)
        texts = text.split("-")
        
        date = []
        s = []
        for value in window(texts,3):
            item = ' '.join(value)
            try:
                date.append(dparser.parse(item).strftime('%Y-%m-%d'))
                s.append(item)
            except:
                continue
        if(date == []):
            dates[img_64] = "null"
        else:
            dates[img_64] = date[0]
        return {'date' : dates[img_64]}

api.add_resource(extract_date, '/')

if __name__ == '__main__':
    app.run(debug=True)
