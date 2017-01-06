from flask_restplus.reqparse import RequestParser

SeriesSchema = RequestParser()
SeriesSchema.add_argument('offset', type=int)
SeriesSchema.add_argument('limit', type=int)
