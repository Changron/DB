from django.shortcuts import render
from django.conf import settings
import unicodedata
import pickle
import miniDB
import sql
import re

# Create your views here.
def index(request):
    return render(request,'index/index.html')

def sql_view(request):
    # to store input sql, make sure we receive the right input
    sql_str = "Input SQL will be shown here"

    if request.method == 'GET':
        data = {'sql':sql_str}
        return render(request,'index/sql.html', data)
    elif request.method == 'POST':
        sql_unicode = ""
        if request.FILES.get('filesql'):
            sqlfile = request.FILES.get('filesql')
            sql_unicode = sqlfile.read()
            
        elif request.POST.get('sql'):
            sql_unicode = request.POST['sql']

        # read DB from pkl file
        database = load_db()

        # apply sql to the database
        # (Bool,String) to indicate status of execution and error message
        sql_str = sql_unicode.encode('ascii','ignore')
        
        Uans = re.sub(r"\r\n"," ",sql_str)
        Uans = Uans.replace('\n', ' ')
        
        pattern = re.compile(";", re.IGNORECASE)
        st = pattern.sub(";\n", Uans)
        database.exec_sql_insert(st)
        sqlList = [s.strip() for s in st.splitlines()]
        #print(sqlList)

        
        success, tables, err_msgs = [], [], []
        for small_sql in sqlList:
            s, t, err = database.exec_sql(small_sql)
            success.extend(s)
            tables.extend(t)
            err_msgs.extend(err)

        #print(tables)
        # additional message to indicate the execution is successful or not
        panel_msgs = []
        for s in success:
            if s:
                panel_msg = "success"
            else:
                panel_msg = "error"
            panel_msgs.append(panel_msg)

        save_db(database)

        data = {'sql':sql_str,
                'info':zip(success, panel_msgs, sqlList, err_msgs, tables),
                }

        return render(request,'index/sql.html', data)

def table_view(request,table_name=None):
    # the db we want to view
    database = load_db()
    # retreive all table names
    table_names = database.get_all_table_names()
    # if user doesn't specify which table to view, choose the first one as default
    if table_name == None:
        try:
            table_name = table_names[0]
        except:
            return render(request,'index/table.html')
    
    table = database.get_table(table_name)
    
    data = {'table_names':table_names,
            'table_name':table_name,
            'columns':table.columns,
            'content':[row.values for row in table.entities]
            }
    return render(request,'index/table.html', data)

def init_db(request):
    if request.method == 'GET':
        return render(request,'index/init.html')
    elif request.method == 'POST':
        database = miniDB.Database()
        save_db(database)

        # fake
        data = {'success':True}
        return render(request,'index/init.html', data)

def save_db(database):
    # dump new db into a file
    output = open(settings.DB_NAME, 'wb')
    pickle.dump(database, output)

def load_db():
    # read DB from pkl file
    with open(settings.DB_NAME, 'rb') as f:
        return pickle.load(f)
