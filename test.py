import re
from flask import Flask, session, render_template, request, redirect
from flask.helpers import url_for
import pymongo
from bson.objectid import ObjectId
import datetime
import smtplib
from email.mime.text import MIMEText
client = pymongo.MongoClient("mongodb+srv://root:root@test.jkkxn.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.test
collections = db.users
book_page = db.book
out_book = db.out_book
announce = db.announcement

print(out_book.find({}, {"_id":0}).count)