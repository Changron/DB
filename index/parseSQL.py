# simpleSQL.py
#
# simple  using the parsing library to do simple-minded SQL parsing
# could be extended to include where clauses etc.
#
#

from miniDB import *
import shlex
import time
import sys
import re
import unicodedata
from ppUpdate import *

f = open("output.txt","w")
ParserElement.enablePackrat()



def input_insert(DB, txt):
	def_insert(DB,txt)
def input_text(DB,sqlText):
	#Eliminate all newline
	#Text = unicodedata.normalize('NFKD', title).encode('ascii','ignore')
	Uans = re.sub(r"\r\n"," ",sqlText)
	#Generate the SQL command respectively
	pattern = re.compile("insert", re.IGNORECASE)
	st = pattern.sub("\ninsert", Uans)
	pattern1 = re.compile("create", re.IGNORECASE)
	st = pattern1.sub("\ncreate", st)
	pattern2 = re.compile("select", re.IGNORECASE)
	st = pattern2.sub("\nselect", st)
	#Make them into list

	sqlList = [s.strip() for s in st.splitlines()]
	
	#Call the specific function
	success = []
	errMsg = []
	tables = []
	for obj in sqlList:		
		if str(obj) == "":
			continue
		act = obj.split(' ', 1)[0]
		
		sucTemp = "" 
		errTemp = ""
		table = None
		if act.lower()=="create":			
			sucTemp ,errTemp = def_create(DB,obj)
		elif act.lower()=="insert":
			sucTemp ,errTemp = def_insert(DB,obj)
		elif act.lower()=="select":
			sucTemp , table, errTemp = def_select(DB,obj)
			
		success.append(sucTemp)
		errMsg.append(errTemp)
		tables.append(table)

	return success, tables, errMsg


def def_create(DB,text):
	
	createStmt = Forward()
	CREATE = Keyword("create", caseless = True)
	TABLE = Keyword("table",caseless = True)
	PRIMARY = Keyword("PRIMARY KEY", caseless = True)
	INT = Keyword("int", caseless = True)
	VARCHAR = Keyword("varchar", caseless = True)
	#here ident is for table name
	ident	= Word( alphas, alphanums + "_$").setName("identifier")

	#for brackets
	createStmt = Forward()
	

	
	#createExpression << Combine(CREATE + TABLE + ident) + ZeroOrMore()
	varW = Word(alphas,alphanums+"_$") +  Word(alphas,alphanums+"_$") +Combine("("+Word(nums)+")") + Optional(PRIMARY)
	varI =  Word(alphas,alphanums+"_$") + Word(alphas,alphanums+"_$")  +  Optional(PRIMARY)
	tableRval = Group(varW | varI)
	
	#tableCondition = 
	'''
	varW = Combine(VARCHAR + "("+Word(nums)+")")
	tableValueCondition = Group(
		( Word(alphas,alphanums+"_$") + varW + Optional(PRIMARY)) |
		( Word(alphas,alphanums+"_$") + INT + Optional(PRIMARY) )
		)
	'''
	#tableValueExpression = Forward()
	#tableValueExpression << tableValueCondition + ZeroOrMore(tableValueExpression) 
	
	#define the grammar
	createStmt  << ( Group(CREATE + TABLE ) + 
					ident.setResultsName("tables") + 
					 "(" + delimitedList(tableRval).setResultsName("values") + ")" )
	'''
	createStmt  << ( Group(CREATE + TABLE ) + 
					ident.setResultsName("tables") + 
					 "(" + delimitedList(tableValueCondition).setResultsName("values") + ")" )
	'''
	# define Oracle comment format, and ignore them
	simpleSQL = createStmt
	oracleSqlComment = "--" + restOfLine
	simpleSQL.ignore( oracleSqlComment )
	success ,tokens = simpleSQL.runTests(text)
	if(success):
		doubleCheck, flag = process_input_create(DB,tokens)
		return doubleCheck, flag
	else:
		return success, tokens

def def_insert(DB,text):
	#ParserElement.enablePackrat()
	insertStmt = Forward()
	INSERT = Keyword("insert", caseless = True)
	INTO = Keyword("into",caseless = True)
	VALUES = Keyword("values", caseless = True)
	
	string_literal = quotedString("'")
	columnRval = Word(alphas,alphanums+"_$") | quotedString | Word(nums)

	ident	= Word(alphas, alphanums + "_$").setName("identifier")

	valueCondition = delimitedList( columnRval )
		
	#for brackets
	insertStmt = Forward()
	

	#define the grammar
	insertStmt  << ( Group(INSERT + INTO)  + 
					ident.setResultsName("tables")+
					Optional( "(" + (delimitedList(valueCondition).setResultsName("col")| (CharsNotIn(")")- ~Word(printables).setName("<unknown>") )) + ")") +
					VALUES +
					"(" + (delimitedList(valueCondition).setResultsName("val") | (CharsNotIn(")")- ~Word(printables).setName("<unknown>") )) + ")"
					)

	# define Oracle comment format, and ignore them
	simpleSQL = insertStmt
	oracleSqlComment = "--" + restOfLine
	simpleSQL.ignore( oracleSqlComment )
	
	

	start = time.time()
	success, tokens = simpleSQL.runTests(text)
	end = time.time()
	f.write(str(end-start)+"\n")
	#print(end-start)
	if(success):
		return process_input_insert(DB,tokens)
	else:
		return success, tokens
def def_select(DB, text):
	
	LPAR,RPAR,COMMA = map(Suppress,"(),")
	select_stmt = Forward().setName("select statement")

	# keywords
	(COUNT, SUM, OR, UNION, ALL, AND, INTERSECT, EXCEPT, COLLATE, ASC, DESC, ON, USING, NATURAL, INNER, 
	CROSS, LEFT, OUTER, JOIN, AS, INDEXED, NOT, SELECT, DISTINCT, FROM, WHERE, GROUP, BY,
	HAVING, ORDER, BY, LIMIT, OFFSET) =  map(CaselessKeyword, """COUNT, SUM, OR, UNION, ALL, AND, INTERSECT, 
	EXCEPT, COLLATE, ASC, DESC, ON, USING, NATURAL, INNER, CROSS, LEFT, OUTER, JOIN, AS, INDEXED, NOT, SELECT, 
	DISTINCT, FROM, WHERE, GROUP, BY, HAVING, ORDER, BY, LIMIT, OFFSET""".replace(",","").split())
	(CAST, ISNULL, NOTNULL, NULL, IS, BETWEEN, ELSE, END, CASE, WHEN, THEN, EXISTS,
	COLLATE, IN, LIKE, GLOB, REGEXP, MATCH, ESCAPE, CURRENT_TIME, CURRENT_DATE, 
	CURRENT_TIMESTAMP) = map(CaselessKeyword, """CAST, ISNULL, NOTNULL, NULL, IS, BETWEEN, ELSE, 
	END, CASE, WHEN, THEN, EXISTS, COLLATE, IN, LIKE, GLOB, REGEXP, MATCH, ESCAPE, 
	CURRENT_TIME, CURRENT_DATE, CURRENT_TIMESTAMP""".replace(",","").split())
	keyword = MatchFirst((COUNT, SUM,OR, UNION, ALL, INTERSECT, EXCEPT, COLLATE, ASC, DESC, ON, USING, NATURAL, INNER, 
	CROSS, LEFT, OUTER, JOIN, AS, INDEXED, NOT, SELECT, DISTINCT, FROM, WHERE, GROUP, BY,
	HAVING, ORDER, BY, LIMIT, OFFSET, CAST, ISNULL, NOTNULL, NULL, IS, BETWEEN, ELSE, END, CASE, WHEN, THEN, EXISTS,
	COLLATE, IN, LIKE, GLOB, REGEXP, MATCH, ESCAPE, CURRENT_TIME, CURRENT_DATE, 
	CURRENT_TIMESTAMP))
	
	identifier = ~keyword + Word(alphas, alphanums+"_")
	collation_name = identifier.copy()
	column_name = identifier.copy()
	column_alias = identifier.copy()
	table_name = identifier.copy()
	table_alias = identifier.copy()
	index_name = identifier.copy()
	function_name = identifier.copy()
	parameter_name = identifier.copy()
	database_name = identifier.copy()

	# expression
	expr = Forward().setName("expression")

	integer = Regex(r"[+-]?\d+")
	numeric_literal = Regex(r"\d+(\.\d*)?([eE][+-]?\d+)?")
	string_literal = QuotedString("'")
	blob_literal = Combine(oneOf("x X") + "'" + Word(hexnums) + "'")
	literal_value = ( numeric_literal | string_literal | blob_literal |
		NULL | CURRENT_TIME | CURRENT_DATE | CURRENT_TIMESTAMP )
	bind_parameter = (
		Word("?",nums) |
		Combine(oneOf(": @ $") + parameter_name)
		)
	type_name = oneOf("TEXT REAL INTEGER BLOB NULL")

	expr_term = (
		CAST + LPAR + expr + AS + type_name + RPAR |
		EXISTS + LPAR + select_stmt + RPAR |
		function_name + LPAR + Optional(delimitedList(expr)) + RPAR |
		literal_value |
		bind_parameter |
		identifier
		)

	UNARY,BINARY,TERNARY=1,2,3
	expr << operatorPrecedence(expr_term,
		[
		(oneOf('- + ~') | NOT, UNARY, opAssoc.LEFT),
		('||', BINARY, opAssoc.LEFT),
		(oneOf('* / %'), BINARY, opAssoc.LEFT),
		(oneOf('+ -'), BINARY, opAssoc.LEFT),
		(oneOf('<< >> & |'), BINARY, opAssoc.LEFT),
		(oneOf('< <= > >='), BINARY, opAssoc.LEFT),
		(oneOf('= == != <>') | IS | IN | LIKE | GLOB | MATCH | REGEXP, BINARY, opAssoc.LEFT),
		('||', BINARY, opAssoc.LEFT),
		((BETWEEN,AND), TERNARY, opAssoc.LEFT),
		])

	compound_operator = (UNION + Optional(ALL) | INTERSECT | EXCEPT)

	ordering_term = expr + Optional(COLLATE + collation_name) + Optional(ASC | DESC)

	join_constraint = Optional(ON + expr | USING + LPAR + Group(delimitedList(column_name)) + RPAR)

	join_op = COMMA | (Optional(NATURAL) + Optional(INNER | CROSS | LEFT + OUTER | LEFT | OUTER) + JOIN)

	join_source = Forward()
	select_table =  Group(Group(database_name("database") + "." + table_name("table"))+ Optional(Optional(AS) + table_alias("table_alias")))  | Group(table_name("table")  + Optional(Optional(AS) + table_alias("table_alias")))   

	#here ident is for table name
	ident   = Word( alphas, alphanums + "_$")

	result_column =  Group(table_name + "."+ ident).setResultsName("col") | Group("*").setResultsName("col") | Group(table_name + "." + "*").setResultsName("col") | Group(expr + Optional(Optional(AS) + column_alias)).setResultsName("col") 
	whereRvalprev = Group(Word(alphas,alphanums+"_$" ) + Optional("." +Word(alphas,alphanums+"_$" )))
	whereRvalforw = Group(Word(alphas,alphanums+"_$" ) + Optional("." +Word(alphas,alphanums+"_$" ))) | Group(quotedString) | Group(Word(nums))
	whereRval = whereRvalprev + Optional("=" + whereRvalforw | ">" + whereRvalforw|"<" + whereRvalforw|"<>" + whereRvalforw)
	counSumRval =  Group(table_name + "."+ ident) | "*" | Group(table_name + "." + "*") |  Group(table_name)
	counSum = Group(SUM + "("+ counSumRval.setResultsName("agre_value") + ")").setResultsName("agre_expr") | Group(COUNT + "("+ counSumRval.setResultsName("agre_value") + ")").setResultsName("agre_expr")

	select_core = (SELECT + Optional(DISTINCT | ALL) + Group(delimitedList(result_column|counSum))("columns") +
					Optional(FROM + Group(delimitedList(select_table))("tables")) +
					Optional(WHERE + whereRval.setResultsName("where_expr") ) +
					Optional(AND + whereRval.setResultsName("and_expr")) + 
					Optional(OR + whereRval.setResultsName("or_expr")) +
					Optional(GROUP + BY + Group(delimitedList(ordering_term)("group_by_terms")) + 
							Optional(HAVING + expr("having_expr"))))

	select_stmt << (select_core + ZeroOrMore(compound_operator + select_core) +
					Optional(ORDER + BY + Group(delimitedList(ordering_term))("order_by_terms")) +
					Optional(LIMIT + (integer + OFFSET + integer | integer + COMMA + integer)))
	# define Oracle comment format, and ignore them
	simpleSQL = select_stmt
	oracleSqlComment = "--" + restOfLine
	simpleSQL.ignore( oracleSqlComment )
	
	success, tokens = simpleSQL.runTests(text)
	
	if(success):
		return process_input_select(DB,tokens)
	else:
		return success, tokens, None
def process_where_expression(arrayContent):
	if len(arrayContent) == 1:
		if(len(arrayContent[0])==3 and arrayContent[0][1]=='.'):
			return [arrayContent[0][1], arrayContent[0][2],None], None, [None, None, None ]
		else:
			return [None, arrayContent[0][0],None], None, [None, None, None ]
	elif len(arrayContent) == 3:
		pre1 = None
		pre2 = None
		value1 = None
		forw1 = None
		forw2 = None
		value2 = None
		word1 = arrayContent[0]
		word2 = arrayContent[2]

		
		
		#word1 type will be table.column , no value

		if len(word1) == 3:
			if word1[1]=='.':
				pre1 = word1[0]
				forw1 = word1[2]
			else:
				forw1 = word1
		else:
			try:
				# int value: 123
				value1 = int(word1[0])
			except:
				# string value:"abc" 
				if word1[0][0] == '"' or word1[0][0] == "'":
					value1 = word1[0][1:-1]
				# colun , no value
				else:
					forw1 = word1[0]

	
		if len(word2) == 3:
			if word2[1] == '.':
				pre2 = word2[0]
				forw2 = word2[2]
			else:
				forw2 = word2
		else:
			try:
				value2 = int(word2[0])
			except:
				if word2[0][0] == '"' or word2[0][0] == "'":
					value2 = word2[0][1:-1]
				else:
					forw2 = word2[0]
		

		return [[pre1, forw1,value1], arrayContent[1], [pre2, forw2, value2 ]]
	else:
		return "Error: two words after where expression"

def process_input_select(DB, tokens):
	col_names = []
	tables = []
	table_alias = []
	table_names=[]
	where_expr = []
	predicates = []
	columns = []
	operator = None
	
	for i in range(len(tokens)):
		tables = tokens[i]["tables"]
		col_names = tokens[i]["columns"]

	
		
		for k in col_names:
			if(k[0]=="COUNT" or k[0]=="SUM"):
				if len(k[2])==3:
					if k[2][1]=='.':
						columns.append([k[2][0], k[2][2], k[0].lower()])
						
					else:
						
						columns.append([None, k[2][0], k[0].lower()])
				else:
					
					columns.append([None, k[2][0], k[0].lower()])
			else:
				if len(k) == 3:
					if k[1] == ".":
						columns.append([k[0], k[2], None])
					else:
						columns.append([None, k[0], None])	
				else:
					columns.append([None, k[0], None])
		
		
		for k in tables:
			table = k["table"][0]
			try:
				table_alias = k["table_alias"][0]
				table_names.append([table_alias, table])
			except:
				table_names.append([None, table])		
		#Where expression
		try:
			where_expr = tokens[i]["where_expr"]
			
			ans = process_where_expression(where_expr)
			predicates.append(ans)
			
		except:
			pass
			

		try:
			and_expr = tokens[i]["and_expr"]
			operator = "and"
			ans = process_where_expression(and_expr)
			predicates.append(ans)
			
		except:
			pass
			
		try: 
			or_expr = tokens[i]["or_expr"]
			operator = "or"
			ans = process_where_expression(or_expr)
			predicates.append(ans)
			
		except:
			pass
			
		return DB.select(columns, table_names, predicates, operator)
		


		
def process_input_create(DB,tokens):
	keys = []
	col_names = []
	col_datatypes = []
	col_constraints = []
	
	for i in range(len(tokens)):
		try:
			tables = tokens[i]["tables"]
			values = tokens[i]["values"]
		except:
			return False, "FAT: Illegal value type or table name"
		for k in values:
			length = len(k)
			col = k[0]
			typeOri = k[1]
			key = False
			con = None
			if typeOri.lower() == "varchar":
				try:
					con = k[2][k[2].find("(")+1:typeOri.find(")")]	
					con = int(con)
				except:
					return False, "FATL: the correct type of varchar :'varchar(int)'"
				if length == 4:
					key = True
			
				#with primary key, the primary key string should have been checked during parsing
			if typeOri.lower() =="int" and length == 3:
				key = True
			elif length > 4 or length < 2 :
				print("values error")
			
			col_names.append(col)
			col_datatypes.append(typeOri.lower())
			col_constraints.append(con)
			keys.append(key)
		return DB.create_table(tables, col_names, col_datatypes, col_constraints, keys)
		
def process_input_insert(DB,tokens):
	for i in range(len(tokens)):		
		tables = tokens[i]["tables"]
		values = tokens[i]["val"]
		for k in range(len(values)):
			try:				
				values[k] = int(values[k])				
			except:				
				values[k] = values[k].replace("'","").replace('"', '')	
		try:
			cols = tokens[i]["col"]					
		except:
			cols = None			
		tableObj = DB.get_table(tables)
		if tableObj:
			return tableObj.insert(values, cols)
		else:
			return False, "Table not exists."	
		
