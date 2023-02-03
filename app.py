import re
from typing import AsyncGenerator
from flask import Flask, session, render_template, request, redirect, flash
from flask.helpers import url_for
from flask.templating import render_template_string
import pymongo
from bson.objectid import ObjectId
import datetime
import smtplib
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
import os
import certifi
client = pymongo.MongoClient("mongodb+srv://root:root@test.jkkxn.mongodb.net/myFirstDatabase?retryWrites=true&w=majority", tlsCAFile=certifi.where())
db = client.test
collections = db.users
book_page = db.book
out_book = db.out_book
announce = db.announcement

app = Flask(__name__)
app.secret_key = "hello"
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

def remind_return():
    print("提醒函數")
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login('a2251296@gmail.com', "hfrndhwfbwjnzgfp")
    count = {}
    for i in out_book.find({}, {"_id":0}):
        print((datetime.datetime.today()-datetime.datetime.strptime(i["come_date"],'%Y%m%d')).days)
        if ((datetime.datetime.today()-datetime.datetime.strptime(i["come_date"],'%Y%m%d')).days == 7 or 
            (datetime.datetime.today()-datetime.datetime.strptime(i["come_date"],'%Y%m%d')).days == 3):
            content = f"書籍編號：{i['book_number']}\n書籍名稱：{i['book_name']}\n到期日：{i['come_date']}\n"
            if (i["student_number"] not in count):
                count[i["student_number"]] = f"書籍編號：{i['book_number']}\n書籍名稱：{i['book_name']}\n到期日：{i['come_date']}\n--------------------------------------------------------------------------------\n"
            else:
                count[i["student_number"]] += f"書籍編號：{i['book_number']}\n書籍名稱：{i['book_name']}\n到期日：{i['come_date']}\n--------------------------------------------------------------------------------\n"
    for i in count:
        content = ""
        if (count[i][:2] == "書籍"):
            content = "您好，您所借閱的書籍即將到期，請注意歸還日期，以免逾期，謝謝您的合作\n----------------------------------------------------------------------------\n"+count[i]
            content_mime = MIMEText(content, "plain", "utf-8")
            content_mime["Subject"] = "借閱書籍到期通知"
            msg = content_mime.as_string()
            smtpObj.sendmail('a2251296@gmail.com', collections.find_one({"student_number":i})["email"], msg)
    smtpObj.quit()

def login_function(student_number, password):
        student = collections.find_one({"student_number":student_number, "password":password})
        if (student != None and student["student_number"] == student_number and student["password"] == password):
            session["student_number"] = student["student_number"]
            session["student_name"] = student["student_name"]
            session["password"] = student["password"]
            session["book_count"] = student["book_count"]
            session["payment"] = student["payment"]
            session["email"] = student["email"]
            session["level"] = student["level"]
            return True
        else:
            return False

def search_function(search):
    session["first_result"] = []
    result = []
    count = []
    borrow_count = {}
    calculator = {}
    for i in book_page.find():
        if (search in i["book_name"] and search != ""):
            if (i["book_name"] in calculator):
                calculator[i["book_name"]] += 1
            else:
                calculator[i["book_name"]] = 1
            if (i["status"] == 1 or i["booking"] != ""):
                if (i["book_name"] in borrow_count):
                    borrow_count[i["book_name"]] += 1
                else:
                    borrow_count[i["book_name"]] = 1
            if (i["book_name"] not in count):
                count.append(i['book_name'])
                result.append([i["picture"], i["book_name"], i["publisher"], i["author"], i["info"]])
    check = [x for x in borrow_count]
    if (result != []):
        for i in result:
            i.append(calculator[i[1]])
            if (i[1] in check):
                if (len(borrow_count) != 0):
                    i.append(borrow_count[i[1]])
                else:
                    i.append(0)
            else:
                i.append(0)
        session["first_result"] = result
        return True
    else:
        return False
    
def check_book_count():
    if (collections.find_one({"student_number":session["student_number"]})["book_count"] < 10):
        return True
    else:
        return False

def check_payment():
    pay = collections.find_one({"student_number":session["student_number"]})["payment"] == 0
    check_book = out_book.find({"student_number":session["student_number"]})
    check = True
    print(pay)
    if (check_book.count() != 0):
        for i in check_book:
            if ((datetime.datetime.today()-datetime.datetime.strptime(i["come_date"],'%Y%m%d')).days > 1 and i["come"] == 0):
                check = False
    if (check and pay):
        print(1)
        return True
    else:
        print(12)
        return False


def calpayment(days):
    return days * 5

def return_book():
    session["book_count"] -= 1
    collections.update({"student_number":session["student_number"]}, {"$inc":{"book_count":-1}})
    book_page.update({"book_number":request.args.get("return")}, {"$set":{"status":0}})
    out_book.update({"book_number":request.args.get("return")}, {"$set":{"come":1, "return_date":datetime.datetime.strftime(datetime.date.today(),"%Y%m%d")}})
    rebook = out_book.find_one({"book_number":request.args.get("return")})
    if ((datetime.datetime.today()-datetime.datetime.strptime(rebook["come_date"],'%Y%m%d')).days  > 1):
        collections.update({"student_number":session["student_number"]}, {"$inc":{"payment":calpayment((datetime.datetime.today()-datetime.datetime.strptime(rebook["come_date"],'%Y%m%d')).days)}})
        session["payment"] = collections.find_one({"student_number":session["student_number"]})["payment"]
        return calpayment((datetime.datetime.today()-datetime.datetime.strptime(rebook["come_date"],'%Y%m%d')).days)
    else:
        return True


def detail_book(choose):
    session["result"] = []
    book = book_page.find({"book_name":choose})
    out = out_book.find({"book_name":choose})
    count = {}
    if (book):
        for i in out:
            count[i["book_number"]] = i["come_date"]
        for i in book:
            status = ""
            if (i["status"] == 0):
                status = "未借出"
            else:
                status = count[i["book_number"]]
            session["result"].append([i["book_number"], i["book_name"], i["publisher"], i["author"],i["ISBN"] , status, "可預約" if (i["booking"] == "") else "已被預約", i["info"]])

def booking():
    book = book_page.find_one({"book_number":request.args.get("booking")})
    if (check_book_count() and check_payment() and 
        book["booking"] == "" and book ["booking"] != session["student_number"]):
        book_page.update({"book_number":request.args.get("booking")}, {"$set":{"booking":session["student_number"]}})
        return True
    else:
        return False



def borrow_book():
    user = out_book.find({"student_number":session["student_number"]})
    if(user.count() != 0):
        for i in user:
            if ((datetime.datetime.today()-datetime.datetime.strptime(i["come_date"],'%Y%m%d')).days > 1 and i["come"] == 0):
                return False
    book = book_page.find_one({"book_number":request.args.get("borrow")})
    if (session["book_count"] < 10 and check_payment() and book["booking"] == ""):
        out_book.insert({"student_number":session["student_number"], "book_number":request.args.get("borrow"),
                        "book_name":book["book_name"], "out_date":datetime.datetime.today().strftime('%Y%m%d'),
                        "come_date":(datetime.datetime.today()+datetime.timedelta(days=14)).strftime('%Y%m%d'),
                        "renew":0, "come":0})
        book_page.update({"book_number":request.args.get("borrow")}, {"$set":{"status":1}})
        collections.update({"student_number":session["student_number"]},{"$inc" : {"book_count" : 1}})
        collections.update({"student_number":session["student_number"]}, {"$inc":{"history":1}})
        session["book_count"] = collections.find_one({"student_number":session["student_number"]})["book_count"]
        return True
    elif (session["book_count"] >= 10 and book["booking"] != ""):
        return False

@app.route("/", methods=["POST", "GET"])
def login():
    return render_template("login.html")

@app.route("/homepage", methods=["POST", "GET"])
def homepage():
    session["history"] = list(collections.find({}, {"_id":0}).sort("history"))
    if (request.method=="POST"):
        if(login_function(request.form["student_number"], request.form["password"])):
            session["new_book"] = list(book_page.find({}, {"_id":0}).sort("check_in_date",-1))
            session["old_book"] = list(book_page.find({}, {"_id":0}).sort("check_in_date", 1))
            session["announce"] = list(announce.find({}, {"_id":0, "content":0}).sort("update_date",-1))
            if (session["level"] == 1):
                return "<script>alert('登入成功');location.href='/homepage';</script>"
            else:
                return "<script>alert('管理員你好');location.href='/homepage';</script>"
        else:
            return "<script>alert('登入失敗');location.href='/';</script>"
    return render_template("homepage_t.html")

@app.route("/user", methods=["POST", "GET"])
def user():
    book = out_book.find({"student_number":session["student_number"], "come":0}, {"_id":0})
    booking = book_page.find({"booking":session["student_number"]}, {"_id":0, "check_in_date":0, "student_number":0, "booking":0, "info":0, "status":0})
    if (request.method=="GET"):
        if (request.args.get("return")):
            re = return_book()
            if (re == True):
                return "<script>alert('歸還成功');location.href='/user';</script>"
            else:
                return "<script>alert('應繳罰金："+ str(re) +"');location.href='/user';</script>"
        elif(request.args.get("cancel")):
            book_page.update({"book_number":request.args.get("cancel")}, {"$set":{"booking":""}})
            return "<script>alert('取消成功');location.href='/user';</script>"
        elif(request.args.get("renew")):
            renew_book = out_book.find_one({"book_number":request.args.get("renew")})
            time = (datetime.datetime.strptime(renew_book["come_date"],'%Y%m%d')+datetime.timedelta(days=14)).strftime('%Y%m%d')
            out_book.update({"book_number":request.args.get("renew")}, {"$set":{"renew":1, "come_date":time}})
            return "<script>alert('續借成功');location.href='/user';</script>"
    return render_template("user.html", user_book = book, booking = booking)

@app.route("/searchpage", methods=["POST", "GET"])
def searchpage():
    return render_template("searchpage_t.html")

@app.route("/result", methods=["POST", "GET"])
def result():
    if (request.method=="POST"):
        if (search_function(request.form["search"])):
            session["search"] = request.form["search"]
            return "<script>alert('共有"+str(len(session["first_result"]))+"筆結果');location.href='/result';</script>"
        else:
            return "<script>alert('查無結果，請重新查詢');location.href='/searchpage';</script>"
    return render_template("result_t.html")

@app.route("/detail/<book>", methods=["POST", "GET"])
def detail(book):
    detail_book(book)
    if (request.method=="GET"):
        if (request.args.get("booking")):
            if (booking()):
                search_function(session["search"])
                return "<script>alert('預約成功');location.href='/detail/"+book+"';</script>"
            else:
                return "<script>alert('預約失敗');location.href='/detail/"+book+"';</script>"
        if (request.args.get("borrow")):
            if (borrow_book()):
                search_function(session["search"])
                return "<script>alert('借閱成功');location.href='/detail/"+book+"';</script>"
            else:
                return "<script>alert('借閱失敗');location.href='/detail/"+book+"';</script>"
    return render_template("bookintro.html", book=book)

@app.route("/manage_book", methods=["POST", "GET"])
def manage():
    if (request.method=="GET"):
        if (request.args.get("delete")):
            book_page.delete_one({"book_number":request.args.get("delete")})
            os.remove(r"C:\Users\a2251\Desktop\system_work\static\\"+request.args.get("delete")[:5]+".jpg")
            return "<script>alert('刪除成功');location.href='/manage_book';</script>"
    return render_template("manage_book.html", books=book_page.find({}, {"_id":0}))

@app.route("/insert_page", methods=["POST", "GET"])
def insert_page():
    if (request.method=="POST"):
        if (request.form["book_name"] and request.form["category"] and request.form["author"] and request.form["publisher"] and request.form["ISBN"]):
            book_number = ""
            book = list(book_page.find({"book_name":{"$regex":request.form["book_name"]}}, {"_id":0}).sort("book_number",-1)) #書籍已存在
            if (book != []):
                count = len(book)+1
                book_number = book[0]["book_number"][:5]+str(count)
            else:
                category_book = list(book_page.find({"book_number":{"$regex":request.form["category"]}}, {"_id":0}).sort("book_number",-1))
                if (category_book != []):
                    temp = str(int(category_book[0]["book_number"][1:5])+1)
                    book_number = request.form["category"]+"0"*(4-len(temp))+temp+"1"
                else:
                    book_number = request.form["category"]+"00011"
            book_page.insert_one({"book_name":request.form["book_name"], "ISBN":request.form["ISBN"], "publisher":request.form["publisher"]
                                , "author":request.form["author"], "check_in_date":datetime.datetime.today().strftime('%Y%m%d'), "status":0, "booking":""
                                , "picture":"/static/"+book_number[:5], "book_number":book_number, "info":request.form["info"]})
            filename = request.files.get("picture").filename
            request.files.get("picture").save(r"C:\Users\a2251\Desktop\system_work\static\\"+book_number[:5]+".jpg")
            return "<script>alert('新增成功');location.href='/insert_page';</script>"
                    
    return render_template("insert_page.html")

@app.route("/manage_user", methods=["POST", "GET"])
def manage_user():
    user = collections.find({}, {"_id":0})
    if (request.method=="GET"):
        if(request.args.get("change")):
            session["change"] = request.args.get("change")
            change=collections.find({"student_number":request.args.get("change")}, {"_id":0, "payment":0, "book_count":0, "level":0, "history":0})
            return render_template("user_change.html", user=change)
    elif (request.method=="POST"):
        temp = collections.find_one({"student_number":session["change"]}, {"_id":0})
        collections.update({"student_number":session["change"]}, {"$set":{
            "student_name":request.form["student_name"] if (request.form["student_name"] != "") else temp["student_name"],
            "password":request.form["password"] if (request.form["password"] != "") else temp["password"],
            "email":request.form["email"] if (request.form["email"] != "") else temp["email"]
        }})
        after_change = collections.find_one({"student_number":session["change"]})
        session["password"] = after_change["password"]
        session["email"] = after_change["email"]
        if (session["level"] == 0):
            return "<script>alert('修改成功');location.href='/manage_user';</script>"
        else:
            return "<script>alert('修改成功');location.href='/user';</script>"
    return render_template("manage_user.html",users=user)

@app.route("/user_out_book/<student_number>", methods=["POST", "GET"])
def user_out_book(student_number):
    book_user = list(out_book.find({"student_number":student_number, "come":0}, {"_id":0}))
    if (book_user == []):
        return "<script>alert('此用戶尚未借書');location.href='/manage_user';</script>"
    return render_template("user_out_book.html", student_book=book_user)

@app.route("/announcement", methods=["POST", "GET"])
def announcement():
    announcement = list(announce.find())
    if (request.method=="GET"):
        if(request.args.get("delete")):
            announce.delete_one({"title":request.args.get("delete")})
            session['announce'] = list(announce.find({}, {"_id":0, "content":0}).sort("update_date",-1))
            return "<script>alert('刪除成功');location.href='/announcement';</script>"
    return render_template("announcement.html", announcement=announcement)

@app.route("/update_announce", methods=["POST", "GET"]) 
def update_announce():
    if (request.method=="POST"):
        announce.insert_one({"update_date":datetime.datetime.today().strftime('%Y%m%d'), "title":request.form["title"], "content":request.form["content"]})
        session['announce'] = list(announce.find({}, {"_id":0, "content":0}).sort("update_date",-1))
        return "<script>alert('新增成功');location.href='/update_announce';</script>"
    return render_template("update_announce.html")

@app.route("/view_announce/<title>", methods=["POST", "GET"])
def view_announce(title):
    announcement = announce.find_one({"title":title}, {"_id":0})
    if (request.method=="POST"):
        if (request.form["content"]):
            announce.update({"title":title}, {"$set":{"content":request.form["content"]}})
            return "<script>alert('修改成功');location.href='/view_announce/"+title +"';</script>"
    return render_template("view_announce.html", announce=announcement)

if (__name__ == "__main__"):
    remind_return()
    app.run(debug=True)