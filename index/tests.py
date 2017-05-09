from django.test import TestCase
import pickle
import miniDB
import parseSQL
import re

#https://docs.djangoproject.com/en/1.10/topics/testing/overview/

TEST_DB_NAME = "TESTING.pkl"
TEST_DB_WITH_STUDENT = "TESTING_STUDENT.pkl"
TEST_DB_WITH_BOOK_AUTHOR = "TESTING_BOOK_AUTHOR.pkl"

def save_db(database, db_name):
    # dump new db into a file
    output = open(db_name, 'wb')
    pickle.dump(database, output)

def load_db(db_name):
    # read DB from pkl file
    with open(db_name, 'rb') as f:
        return pickle.load(f)

# Create your tests here.
class TableTestCase(TestCase):
    # We can always start from clean Database if we don't save our Database
    # valie Table name character, A-Z, 0-9 and _
    def setUp(self):
        database = miniDB.Database()
        save_db(database, TEST_DB_NAME)

        database_with_student_table = miniDB.Database()
        sql = "CREATE TABLE STUDENT (\
            studentId int PRIMARY KEY,\
            name VARCHAR(15),\
            gender VARCHAR(1),\
            age int\
            )"
        passed, table, err_msg = database_with_student_table.exec_sql(sql)
        sql = "CREATE TABLE COURSE (\
            name VARCHAR(40) PRIMARY KEY,\
            id INT PRIMARY KEY\
            )"
        passed, table, err_msg = database_with_student_table.exec_sql(sql)
        save_db(database_with_student_table, TEST_DB_WITH_STUDENT)

# TABLE TESTS

    def test_table_creation(self):
        # test table creation 
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE STUDENT (\
            studentId int PRIMARY KEY,\
            name VARCHAR(15),\
            gender VARCHAR(1),\
            age int\
            )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [True])
        self.assertEqual(err_msg, [None])

    def test_table_creation_no_pk(self):
        # test table creation 
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE STUDENT (\
            studentId int,\
            name VARCHAR(15),\
            gender VARCHAR(1),\
            age int\
            )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [True])
        self.assertEqual(err_msg, [None])

    def test_table_creation_duplicate(self):
        # test table creation with already exists name
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE STUDENT (\
            studentId int PRIMARY KEY,\
            name VARCHAR(15),\
            gender VARCHAR(1),\
            age int\
            );"
        passed, table, err_msg = database.exec_sql(sql+sql)
        self.assertEqual(passed, [True, False])
        self.assertEqual(err_msg, [None, "Table with same name exists."])

    def test_table_creation2(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE VEHICLE (\
            licenseNumber VARCHAR(10),\
            brand VARCHAR(15),\
            model VARCHAR(15),\
            type VARCHAR(2),\
            engineSize int\
            );"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [True])
        self.assertEqual(err_msg, [None])
    
    def test_table_creation3(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE BOOK (\
        isbn VARCHAR(20) PRIMARY KEY,\
        title VARCHAR(20),\
        author VARCHAR(20),\
        pages int,\
        editorial VARCHAR(15)\
        )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [True])
        self.assertEqual(err_msg, [None])

    def test_table_creation_with_2pks(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE COURSE (\
            name VARCHAR(40) PRIMARY KEY,\
            id INT PRIMARY KEY\
            )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [True])
        self.assertEqual(err_msg, [None]) 

    def test_table_creation_with_missing_paranthesis(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE TEACHERS\
        FName VARCHAR,\
        LName VARCHAR(20)\
        )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [False])
        #self.assertEqual(err_msg, [None]) 

    def test_table_creation_with_unknown_type(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE TEACHERS (\
        FName VARCHAR(1),\
        LName DATE\
        )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [False])
        #self.assertEqual(err_msg, [None]) 

    def test_table_creation_with_extra_comma(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE TEACHERS (\
            FName VARCHAR(4),\
            LName VARCHAR(4),\
            )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [False])
        #self.assertEqual(err_msg, [None])

    def test_table_creation_with_duplicate_column_name(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE TEACHERS (\
            FName VARCHAR(4),\
            LName VARCHAR(4),\
            FName VARCHAR(4)\
            )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [False])
        self.assertEqual(err_msg, ["Columns contain duplicate name."])

    def test_table_creation_with_bounds_varchar_limit(self):
        database = load_db(TEST_DB_NAME)
        sql = "CREATE TABLE TEACHERS (\
            FName VARCHAR(4),\
            LName VARCHAR(50)\
            )"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [False])
        #self.assertEqual(err_msg, [None])

# INSERTION TESTS

    def test_insert_singles(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(10, 'John Smith', 'M', 22)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(11, 'Hsu You-Ting', 'F', 23)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

    def test_insert_too_many_values(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(11, 'Hsu You-Ting', 'F', 23, 'idk')"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed, [False])
        self.assertEqual(err_msg, ["Too many values are given"])

    def test_insert_multiple(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(12, 'John Cena', 'M', 45),\
        VALUES(14, 'Chuck Norris', 'M', 55)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

    def test_insert_duplicate_key(self):
        database = load_db(TEST_DB_WITH_STUDENT)

        sql = "INSERT INTO STUDENT \
        VALUES(10, 'John Smith', 'M', 22)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

        sql = "INSERT INTO STUDENT \
        VALUES(10, 'Huang Hao-Wei', 'M', 26)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertIn("Primary key pair", err_msg[0])
        self.assertIn("duplicate", err_msg[0])

    def test_insert_missing_comma(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(10 'Huang Hao-Wei', 'M', 26)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertIn("Unexpected white",err_msg[0])   

    def test_insert_data_mismatch(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(15, 'Mr. Bean', 'M', '45')"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertIn("is not int", err_msg[0] )
    
    def test_insert_string_length(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(16, 'Caitlyn Jenner', 'MF', 45)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertEqual(err_msg, ["Value MF exceed maximum length 1."])

    def test_insert_int_size(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(17, 'Infinity Man', 'M', 2147483650)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertIn("out of range", err_msg[0])

    def test_insert_int_size1(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(18, 'Max Int Man', 'M', 2147483647)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

    def test_insert_null_key(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(, 'Null Woman', 'W', 100)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertIn("unwanted token", err_msg[0])

    def test_insert_missing_paranthesis(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(19, 'Dr. Paranthesis', 'M', 67"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        # check if the error message contains FAIL: Expected ...
        self.assertIn("FAIL: Expected \")\"", err_msg[0])

    def test_insert_missing_attribute(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT \
        VALUES(20, 'Prof. No Age', 'M')"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

    def test_insert_missing_pk_attribute(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO STUDENT (gender, name, age)\
        VALUES('Prof. No ID', 'M', 21)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertIn("Empty value for primary key", err_msg[0])

    def test_insert_not_exist_table(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO NOSUCHTABLE \
        VALUES('Databases', 12345)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertEqual(err_msg, ["Table not exists."])

    def test_insert_key_combinations1(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO COURSE \
        VALUES('Databases', 12345)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        sql = "INSERT INTO COURSE \
        VALUES('Databases', 54321)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

    def test_insert_key_combinations2(self):
        database = load_db(TEST_DB_WITH_STUDENT)
        sql = "INSERT INTO COURSE \
        VALUES('Databases', 12345)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        sql = "INSERT INTO COURSE \
        VALUES('Databases', 12345)"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[False])
        self.assertIn("Primary key", err_msg[0])

class Stage2TestCase(TestCase):

    def setUp(self):
        database_with_book_author = miniDB.Database()
        sql = "CREATE TABLE Book (\
            bookId int PRIMARY KEY,\
            title VARCHAR(30),\
            pages int,\
            authorId int,\
            editorial varchar(30)\
            );\
            CREATE TABLE Author (\
            authorId int PRIMARY KEY,\
            name varchar(30),\
            nationality varchar(30)\
            )"
        passed, table, err_msg = database_with_book_author.exec_sql(sql)
        #save_db(database_with_book_author, TEST_DB_WITH_BOOK_AUTHOR)

        #database_with_book_author = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        fd = open('index/author.sql', 'r')
        sqlFile = fd.read()
        sql_str = sqlFile.encode('ascii','ignore')
        
        Uans = re.sub(r"\r\n"," ",sql_str)
        Uans = Uans.replace('\n', ' ')
        #print(Uans)
        #print("++++++++++++++")
        pattern = re.compile(";", re.IGNORECASE)
        st = pattern.sub(";\n", Uans)

        fd.close()
        passed, table, err_msg = database_with_book_author.exec_sql(st)
        fd = open('index/book2.sql', 'r')
        sqlFile = fd.read()
        sql_str = sqlFile.encode('ascii','ignore')
        
        Uans = re.sub(r"\r\n"," ",sql_str)
        Uans = Uans.replace('\n', ' ')
        #print(Uans)
        #print("++++++++++++++")
        pattern = re.compile(";", re.IGNORECASE)
        st = pattern.sub(";\n", Uans)

        fd.close()
        passed, table, err_msg = database_with_book_author.exec_sql(st)
        save_db(database_with_book_author, TEST_DB_WITH_BOOK_AUTHOR)

    def test_select1(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT \
                bookId,\
                title,\
                pages,\
                authorId,\
                editorial\
                FROM Book;"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 10)
        self.assertEqual(table[0].entities[5].values,[6, 'Romeo and Juliet', 300, 4, 'English Books'])
        #for obj in table.entities:
        #for table.entity:

    def test_selectAll(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                *\
                FROM Author;"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 10)
        self.assertEqual(table[0].entities[2].values,[3, 'Michael Crichton','USA'])
       

    def test_select_specific_title(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                title\
                FROM Book\
                WHERE\
                bookId = 1;"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 1)
        self.assertEqual(table[0].entities[0].values,['Bible'])
       
    def test_select_size_constraints(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                b.title\
                FROM Book AS b\
                WHERE\
                pages > 100\
                AND\
                editorial = 'Prentice Hall';"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 2)
        self.assertEqual(table[0].entities[1].values,['Study Guide'])
       
    def test_select_all_size_constraints(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                *\
                FROM Book\
                WHERE\
                authorId = 1\
                OR\
                pages < 200;"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 3)
        self.assertEqual(table[0].entities[2].values,[8,'Network Programming',79,5,'Prentice Hall'])

    def test_inner_join1(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                b.*\
                FROM\
                Book AS b,\
                Author AS a\
                WHERE\
                b.authorId = a.authorId\
                AND\
                a.name = 'Michael Crichton';"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 2)
        self.assertEqual(table[0].entities[1].values,[5,'Congo',500,3,'Bauhaus'])

    def test_inner_join2(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                bookId, title, pages, name\
                FROM\
                Book,\
                Author\
                WHERE\
                Book.authorId = Author.authorId;"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 10)
        self.assertEqual(table[0].entities[0].values,[1, 'Bible', 500, 'Jim Chen'])

    def test_inner_join3(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                a.name, title\
                FROM\
                Book,\
                Author AS a\
                WHERE\
                Book.authorId = a.authorId\
                AND\
                Book.pages > 200;"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 7)
        self.assertEqual(table[0].entities[0].values,['Jim Chen', 'Bible'])

    def test_inner_join4(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                a.name\
                FROM\
                Author AS a,\
                Book AS b\
                WHERE\
                a.authorId = b.authorId\
                AND\
                b.title = 'Star Wars';"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 1)
        self.assertEqual(table[0].entities[0].values,['George Lucas'])

    def test_inner_join5(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                a.name,\
                b.title\
                FROM\
                Author AS a,\
                Book AS b\
                WHERE\
                a.authorId = b.authorId\
                AND\
                a.nationality <> 'Taiwan';"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 7)
        self.assertEqual(table[0].entities[1].values,['John   Goodman', 'VPN Architectures'])

    def test_aggregation1(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                COUNT(*)\
                FROM\
                Book;"
        passed, table, err_msg = database.exec_sql(sql)   
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])

        self.assertEqual(len(table[0].entities), 1)
        self.assertEqual(table[0].entities[0].values[0],10)     

    def test_aggregation2(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                COUNT(editorial)\
                FROM\
                Book;"
        passed, table, err_msg = database.exec_sql(sql)     
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 1)
        self.assertEqual(table[0].entities[0].values[0],10)  

    def test_aggregation3(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                COUNT(*)\
                FROM\
                Author\
                WHERE\
                nationality = 'Taiwan';"
        passed, table, err_msg = database.exec_sql(sql)                
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 1)
        self.assertEqual(table[0].entities[0].values[0],2)  

    def test_aggregation4(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                SUM(pages)\
                FROM\
                Book\
                WHERE\
                authorId = 2;"
        passed, table, err_msg = database.exec_sql(sql)       
        self.assertEqual(passed,[True])
        self.assertEqual(err_msg, [None])
        self.assertEqual(len(table[0].entities), 1)
        self.assertEqual(table[0].entities[0].values[0],650)  

    def test_switched_column_table(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "select Author.*, Book.editorial from Author, Book where Book.authorId = Author.authorId"
        passed, table, err_msg = database.exec_sql(sql)
        self.assertEqual(passed,[True])

    def test_ambigousError(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                authorId\
                FROM\
                Author,\
                Book\
                WHERE\
                Author.authorId = Book.authorId\
                AND\
                Book.title = 'Star Wars';"
        passed, table, err_msg = database.exec_sql(sql)         
        self.assertEqual(passed,[False])
        self.assertIn("Ambiguous", err_msg[0])

    def test_type_mismatch(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                *\
                FROM\
                Author\
                WHERE\
                authorId = 'John';"
        passed, table, err_msg = database.exec_sql(sql)         
        self.assertEqual(passed,[False])
        self.assertIn("Type mismatch", err_msg[0])

    def test_comparision_mismatch(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT\
                Book.*\
                FROM\
                Book,\
                Author\
                WHERE\
                Book.authorId = Author.name;"
        passed, table, err_msg = database.exec_sql(sql) 
        self.assertEqual(passed,[False])
        self.assertIn("Type mismatch", err_msg[0]) 

    def test_logic_error(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "SELECT \
                a.name, b.title\
                FROM \
                Author AS b, Book AS a;"
        passed, table, err_msg = database.exec_sql(sql) 
        self.assertEqual(passed,[False])
        self.assertIn("No column", err_msg[0]) 

    def test_logic_alias_error(self):
        database = load_db(TEST_DB_WITH_BOOK_AUTHOR)
        sql = "select authorId , title from Author as a,  Book as a;"
        passed, table, err_msg = database.exec_sql(sql) 
        self.assertEqual(passed,[False])
        self.assertIn("Alias name", err_msg[0]) 