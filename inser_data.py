import re
from flask import Flask, session, render_template, request, redirect
from flask.helpers import url_for
import pymongo
from bson.objectid import ObjectId
import datetime
client = pymongo.MongoClient("mongodb+srv://root:root@test.jkkxn.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.test
collections = db.book

count = True
keys = ["number", "book_name", "ISBN", "publisher", "author", "category", "check_in_date", "status", "picture"]

while count:
    number = input("請輸入書籍編號：")
    book_name = input("請輸入書名：")
    isbn = input("請輸入ISBN：")
    publisher = input("請輸入出版社：")
    author = input("請輸入作者：")
    check_in = input("請輸入入館日期：")
    info = input("請輸入簡介")

    collections.insert_one(
        {
            "book_name":book_name,
            "ISBN":isbn,
            "publisher":publisher,
            "author":author,
            "check_in_date":check_in,
            "status":0,
            "booking":0,
            "picture":"/static/" + number[:5],
            "book_number":number,
            "info":info
        }
    )
    count = input("是否繼續?(y/n)")
    if (count == "n" or count == "N"):
        count = False