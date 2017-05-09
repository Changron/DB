# db that stores everything
from parseSQL import *
import operator as Libop
import copy
from extendibleHashing import *

class Database:
    def __init__(self):
        self.tables = []
        # dictionary for fast look up from table_name to its order in the table
        self.tab_name2id = {}
    def exec_insert(self,sql):
        return input_insert(self, sql)
    def exec_sql(self, sql):
        """The fucntion to run sql
        Args:
            sql (String): The SQL we want to run.
        Returns:
            bool: The return value. True for valid, False otherwise.
            String: The error message. None if no error.
        """
        #Call string parsing
        return input_text(self, sql)
      
    def can_create(self, name, col_name, col_datatypes, col_constraints):
        """The fucntion to check whether the type or constraint is valid for table creation
        Args:
            name (String): The table name.
            col_name ([String]): The column names.
            col_datatypes ([String]): The column data types.
            col_constraints ([int]): The constraint value for each column.
        Returns:
            bool: The return value. True for valid, False otherwise.
            String: The error message. None if no error.
        """
        # Check that all three list have the same length
        if not len(col_name) == len(col_datatypes) == len(col_constraints):
            return False, "Internal Error: Length of column name and data type and constraints is not equal."
        
        # All column length are the same
        # Check that length of column is less than 10
        if len(col_name) >= 10:
            return False, "Number of column exceed 10."
          
        # Check that the DB doesn't contain more then 10 tables already
        if len(self.tables) >= 10:
            return False, "Table limit exceed."
        
        # Check that the DB doesn't constain same name table
        if self.get_table(name):
            return False, "Table with same name exists."

        # Check that the col_name are distinct
        if len(col_name) != len(list(set(col_name))):
            #return False, col_name
            return False, "Columns contain duplicate name."

        # Check that the column data types are either varchar or int
        for dtype in col_datatypes:
            if dtype not in Datatype.str2dt:
                return False, "Type " + dtype + " is not defined."
            
        # Check that the column constraints are < 40 for varchar
        for dtype, cons in zip(col_datatypes, col_constraints):
            if Datatype.str2dt[dtype] == Datatype.VARCHAR and cons > 40:
                return False, "Maximum length of varchar exceed 40."
        
        return True, None  
    
    # Create up to 10 individual tables
    def create_table(self, table_name, col_names, col_datatypes, col_constraints, keys=None):
        """The fucntion to create a new table. It will check if the given parameter is valid. 
        Args:
            table_name (String): The table name.
            col_names ([String]): The column names.
            col_datatypes ([String]): The column data types.
            col_constraints ([int]): The constraint value for each column.
            keys ([Bool]): To indicate if the column is primary key.
        Returns:
            bool: The return value. True for successful creation, False otherwise.
            String: The error message. None if no error.
        """
        passed, err_msg = self.can_create(table_name, col_names, col_datatypes, col_constraints)
        if passed:
            columns = []
            for cname, dtype, cons, key in zip(col_names, col_datatypes, col_constraints, keys):
                columns.append(Column(cname, Datatype.str2dt[dtype], cons, key))
            table = Table(table_name, columns)
            # register in fast look up table
            self.tab_name2id[table_name] = len(self.tables)
            # add newly created table into table list
            self.tables.append(table)
            return True, None
        else:
            return False, err_msg
    
    def get_all_table_names(self):
        return [t.name for t in self.tables]
  
    def get_table(self, name):
        # get table by id
        if type(name) == int:
            try:
                t = self.tables[name]
                return t
            except:
                return None

        # get table by name
        for t in self.tables:
            if t.name == name:
                return t
        return None
    
    def convert_table_names_to_tid(self, table_names):
        """
        Helper function that converts table name into table_name-id dict, 
        Table objects and alias-orderid dict.
        Args:
            table_names ([String]): Names of tables to query on.

        Returns:
            Bool: True for successful execution. False otherwise.
            {String:int}: Dictionary that maps table alias to table id.
            [Table]: Table objects for the corresponding name.
            {String:int}: Dictionary that maps table alias to SQL order.
            String: Error message.
        """
        # tables stores ('Tablealias':tableid)
        tables = {}
        tables_obj = []
        aliases = {}
        # use alias of table as key to get the object
        # if alias is not provided, use table name as key
        # tn for table name
        index = 0
        for alias, tn in table_names:
            #try to find table id in the fast look up table
            try:
                tid = self.tab_name2id[tn]
                if alias:
                    # try to see if the alias exist
                    try:
                        _ = tables[alias]
                        # if reached here, alias is used
                        return False, None, "Alias name" + alias + " is used."
                    except:
                        tables[alias] = tid
                        aliases[alias] = index
                else:
                    tables[tn] = tid
                    aliases[tn] = index
                tables_obj.append(self.get_table(tid))
            except:
                return False, None, "No table named " + tn + "." 
            index += 1
        output = (tables, tables_obj, aliases)
        return True, output, None

    def convert_column_names_to_cid(self, column_names, tables, aliases):
        """
        Helper function that converts column name into 
        orderid-columnid-aggrgation pairs and Column objects.
        Args:
            column_names ([String]): Names of columns to query on.
            tables ({String:int}): Dictionary that maps table alias to table id.
            aliases({String:int}): Dictionary that maps table alias to SQL order.

        Returns:
            Bool: True for successful execution. False otherwise.
            [(int,int,Aggregation)]: List of tuple that stores (table_orderid, columnid, Aggregation)
            [Column]: Column objects for the corresponding name.
            String: Error message.
        """
        # [(which table, column id, aggregation function)]
        # [(int, int, Aggregation)]
        # Note: which table is the sequence in the query, not the real table id
        # converted column information from column_names for future use
        column_infos = []
        # [Columns]
        # The column objects
        column_objs = []
        # [[None, '*', None]] for select * from table case.
        # cn for column name
        # aggr for aggregation function name
        for prefix, cn, aggr in column_names:
            if cn == '*':
                table_search_scope = None
                # with prefix, search only one table
                if tables.get(prefix) != None:
                    table_search_scope = [self.tables[tables[prefix]]]
                # no prefix, search all table
                else:
                    table_search_scope = [self.tables[tid] for key, tid in tables.iteritems() if key is not None]
                for searching_table in table_search_scope:
                    if prefix == None:
                        prefix = searching_table.name
                    for cid, col in enumerate(searching_table.columns):
                        # convert aggr into object
                        aggr_obj = None 
                        if aggr:
                            aggr_obj = Aggregation(aggr)
                        column_infos.append((aliases[prefix], cid, aggr_obj))
                        column_objs.append(col)
            else:
                col_info, col_obj, err_msg = self.get_column_by_names(prefix, cn, aggr, aliases, tables)
  
                if not err_msg:
                    column_infos.append(col_info)
                    column_objs.append(col_obj)
                else:
                    return False, None, err_msg

        output = (column_infos, column_objs)
        return True, output, None

    def get_column_by_names(self, prefix=None, cn=None, aggr=None, table_aliases=None, tables=None):
        """
        Helper function that converts column name into column id and Column objects.
        Args:
            prefix (String): Table name prefix of the column.
            cn (String): Column name to convert.
            aggr (String): Aggregation function to convert.
            table_aliases ({String:Int}): Dictionary of alias and index value of SQL sequence.
            tables ({String:Int}): Dictionary of table name and index value in DB.

        Returns:
            (Int, Int, Aggregation): (which table, column id, aggregation function)
                which table: index value of SQL sequence.
                column id: index value of the column in the table.
                aggregation function: the Aggregation objects.
            Column: The Column object.
            String: The error message. None if no error.
        """
        # prefix provided
        if prefix:
            # convert prefix into table id
            tid = None
            try:
                tid = tables[prefix]
            except:
                return None, None, "No table alias named " + prefix + "."
            t = self.get_table(tid)

            # convert col_name into column id
            cid = None
            try:
                cid = t.col_name2id[cn]
            except:
                return None, None, "No column named " + cn + "."

            # convert aggr into object
            aggr_obj = None 
            if aggr:
                aggr_obj = Aggregation(aggr)

            col_info = (table_aliases[prefix], cid, aggr_obj)
            col_obj = t.columns[cid]
            return col_info, col_obj, None
        
        # prefix not provided
        else:
            col_info = None
            col_obj = None
            i = 0
            if len(tables) > 1:
                for (t_alias, tid), (alias, index) in zip(tables.iteritems(), table_aliases.iteritems()):
                    t = self.get_table(tid)
                    if cn in t.col_name2id and t.name == alias:
                        i += 1
                if i > 1:
                    return None, None, "Ambiguous request"
            # look into all tables and see if there's column named cn
            for t_alias, tid in tables.iteritems():
                t = self.get_table(tid)
                try:
                    cid = t.col_name2id[cn]
                    # convert aggr into object
                    aggr_obj = None 
                    if aggr:
                        aggr_obj = Aggregation(aggr)
                    col_info = (table_aliases[t_alias], cid, aggr_obj)
                    col_obj = t.columns[cid]
                    break
                # table name not found in this table, go on next table
                except:
                    pass
                    
            # col not found
           
            if not col_obj:
                return None, None, "No column named " + cn + "."
            return col_info, col_obj, None

    def convert_predicate_names_to_obj(self, predicates, tables, aliases):
        """
        Helper function that converts predicate name into Predicate objects.
        Args:
            column_names ([String]): Names of columns to query on.
            tables ({String:int}): Dictionary that maps table alias to table id.
            aliases({String:int}): Dictionary that maps table alias to SQL order.

        Returns:
            Bool: True for successful execution. False otherwise.
            [Predicate]: List of Predicate objects.
            String: Error message.
        """
        preds = []
        for rule1, op, rule2 in predicates:
            rules = [None] * 2
            prefixs = [None] * 2
            cns = [None] * 2
            for idx, (prefix, cn, value) in enumerate([rule1, rule2]):
                # with table name and column name
                if cn:
                    col_info, col_obj, err_msg = self.get_column_by_names(prefix, cn, value, aliases, tables)
                    
                # with value
                else:
                    col_info = (None, None, value)

                if not err_msg:
                    rules[idx] = col_info
                    prefixs[idx] = prefix
                    cns[idx] = cn
                else:
                    return False, None, err_msg
            
            preds.append(Predicate(rules[0], op, rules[1], prefixs, cns))

        return True, preds, None

    def insert_filtered_entities(self, tables, tables_obj, column_infos, preds, operator, result):
        """
        Helper function that inserts entities that fulfills the predicates.
        Args:
            tables ({String:int}): Dictionary that maps table alias to table id.
            tables_obj ([Table]): List that contains the tables to query on.
            column_infos ([(Int, Int, Aggregation)]): List that contains infomation of selected column.
                (which table, column id, aggregation function)
                which table: index value of SQL sequence.
                column id: index value of the column in the table.
                aggregation function: the Aggregation objects.
            preds ([Predicate]): List of Predicate objects.
            operator (String): Operator between predicates. Used when more than two predicates.
            result (Table): Table to insert into.

        Returns:
            Bool: True for successful execution. False otherwise.
            None: None. For same return format.
            String: Error message.
        """
        # Hashing search
        Hash1 = False
        Hash2 = False
        flag = False
        # Check weather the select col is primary key
        
        try: 
            res1 = tables_obj[preds[0].rule1[0]].get_column(preds[0].rule1[1]).key
            if res1 :
                # key is primary
                keyVal = preds[0].rule1[2]
            fst_e = tables_obj.hashTable.get(self, keyVal)
            Hash1 = True
        except:
            print("1 predicates no primariy key")
        if len(tables) == 1 and Hash1:
            check, err_msg = self.predicate_check(preds, operator, fst_e, None)
            if check:
                # take requested column and append
                sub_entity = [None] * len(column_infos)
                for idx, (which_table, cid, aggr) in enumerate(column_infos):
                    sub_entity[idx] = fst_e.values[cid]
                result.insert_without_check(sub_entity)
             return True, None, None

        if len(tables) == 2:
            try: 
                res2 = tables_obj[preds[0].rule1[0]].get_column(preds[0].rule1[1]).key
                if res2 :
                    # key is primary
                    keyVal = preds[0].rule1[2]
                snd_e = tables_obj.hashTable.get(self, keyVal)
                Hash1 = True
            except:
                print("1 predicates no primariy key")
        
        if Hash1 and Hash2:
            check, err_msg = self.predicate_check(preds, operator, fst_e, snd_e)
            if check: 
                # take requested column and append
                sub_entity = [None] * len(column_infos)
                for idx, (which_table, cid, aggr) in enumerate(column_infos):
                    if which_table == 0:
                        sub_entity[idx] = fst_e.values[cid]
                    else:
                        sub_entity[idx] = snd_e.values[cid]
                    print(sub_entity[idx])
                result.insert_without_check(sub_entity)
            return True, None, None  

            if Hash1 and not Hash2:
                for snd_e in tables_obj[1].entities:
                    check, err_msg = self.predicate_check(preds, operator, fst_e, snd_e)
                    if check: 
                        # take requested column and append
                        sub_entity = [None] * len(column_infos)
                        for idx, (which_table, cid, aggr) in enumerate(column_infos):
                            if which_table == 0:
                                sub_entity[idx] = fst_e.values[cid]
                            else:
                                sub_entity[idx] = snd_e.values[cid]
                            print(sub_entity[idx])
                        result.insert_without_check(sub_entity)
                return True, None, None

            elif not Hash1 and Hash2:
                for fst_e in tables_obj[1].entities:
                    check, err_msg = self.predicate_check(preds, operator, fst_e, snd_e)
                    if check: 
                        # take requested column and append
                        sub_entity = [None] * len(column_infos)
                        for idx, (which_table, cid, aggr) in enumerate(column_infos):
                            if which_table == 0:
                                sub_entity[idx] = fst_e.values[cid]
                            else:
                                sub_entity[idx] = snd_e.values[cid]
                            print(sub_entity[idx])
                        result.insert_without_check(sub_entity)
                return True, None, None
        
        # key of table        
        if (not Hash1) and (not Hash2):
            for fst_e in tables_obj[0].entities:
                if len(tables) == 2:
                    for snd_e in tables_obj[1].entities:
                        check, err_msg = self.predicate_check(preds, operator, fst_e, snd_e)
                        if err_msg:
                            return False, None, err_msg
                        if check: 
                            # take requested column and append
                            sub_entity = [None] * len(column_infos)
                            for idx, (which_table, cid, aggr) in enumerate(column_infos):
                                if which_table == 0:
                                    sub_entity[idx] = fst_e.values[cid]
                                else:
                                    sub_entity[idx] = snd_e.values[cid]
                                print(sub_entity[idx])
                            result.insert_without_check(sub_entity)

                else:
                    check, err_msg = self.predicate_check(preds, operator, fst_e, None)
                    if err_msg:
                            return False, None, err_msg
                    if check:
                        # take requested column and append
                        sub_entity = [None] * len(column_infos)
                        for idx, (which_table, cid, aggr) in enumerate(column_infos):
                            sub_entity[idx] = fst_e.values[cid]
                        result.insert_without_check(sub_entity)

        return True, None, None

    def aggregate_table(self, column_infos, column_objs, result):
        """
        Helper function that aggregate the table selected.
        Args:
            column_infos ([(Int, Int, Aggregation)]): List that contains infomation of selected column.
                (which table, column id, aggregation function)
                which table: index value of SQL sequence.
                column id: index value of the column in the table.
                aggregation function: the Aggregation objects.
            column_objs ([Column]): List of Column.
            result (Table): Table to aggregate.

        Returns:
            Bool: True for successful execution. False otherwise.
            Table: Table aggregated. Not changed if no aggregation function to apply.
            String: Error message.
        """
        # check only the first column for the aggregation function
        col_id = 0
        
        col_info = column_infos[col_id]
        col_obj = column_objs[col_id]
        # if Aggregation in column_infos exist
        # do nothing if no Aggregation
        if col_info[2]:
            # container to save new columns
            aggr_cols = []
            aggr_entity = []
            # apply aggregation function
            # get a copy of column, and modify the name to aggr_name(col_name)
            aggr_col = copy.deepcopy(col_obj)
            # remove column constraint
            # e.g. Count(Name):
            # the constraint is VarcharConstraint at first
            # but the value becomes int after aggregation
            # remove or intconstraint()?!?!?!
            aggr_col.constraint = IntConstraint()
            # get the aggr function
            aggr_func = col_info[2]
            # apply aggregation function on the result table
        
            aggr_value, err_msg = aggr_func.aggregate(result, col_id)

            if err_msg:
                return False, None, err_msg
            else:
                # modify the column name
                aggr_col.name = aggr_func.func_name + "(" + aggr_col.name + ")"
                aggr_cols.append(aggr_col)
                aggr_entity.append(aggr_value)

            aggr_result = Table("SelectAggrQuery", aggr_cols)
            aggr_result.insert(aggr_entity)

            result = aggr_result

        return True, result, None

    def select(self, column_names, table_names, predicates=None, operator=None):
        """Select columns from tables where predicate fulfills. 
        All the inputs should be String, the function will convert strings into objects.
        None if the data is not available.
        Args:
            column_names ([(String, String, String)]): 
                The column we want to get data from.
                (Table prefix alias, Column name, Aggregation function)
                Table prefix alias: Prefix of the column. None if table name is not available.
                Column name: The column name user wants to select on.
                Aggregation function: Aggregation function we want to apply on the column.

            table_names ([(String, String)]): 
                The table to query on.
                (Table alias, Table name)
                Table alias: The alias of the table.
                Table name: The table name.
            
            predicates ([((String, String, String|Int), String, (String, String, String|Int))]): 
                The predicate of the select query.
                ((Table alias1, Column1, Value1), Operation, (Table alias2, Column2, Value2))
                Table alias1: The alias or table name on the left side.
                Column1: The column name on the left side.
                Value1: The value on the left side. Only evaluated when Table1 and Column1 are None.
                Operation: The operation to perform on two columns or values.
                Table alias2: The alias or table name on the right side.
                Column2: The column name on the right side.
                Value2: The value on the right side. Only evaluated when Table2 and Column2 are None.

            operator (String): 
                Operator between predicates. Used when more than two predicates.
                The value can be "AND" or "OR".

        Returns:
            bool: The return value. True for successful selection, False otherwise.
            Table: Table that includes requested column and rows fulfilling predicate. None if selection fails.
            String: The error message. None if no error.
            
        Todo: Sum() and Count() should be passed into miniDB as str and parse? 
              Or should it be parsed in parser and passed in miniDB as function?
        """

        ''' Convert table names to table id'''
        success, output, err_msg = self.convert_table_names_to_tid(table_names)
        if not success:
            return False, None, err_msg
        tables, tables_obj, aliases = output

        ''' Convert column names to column id'''
        success, output, err_msg = self.convert_column_names_to_cid(column_names, tables, aliases)
        if not success:
            return False, None, err_msg
        column_infos, column_objs = output

        ''' Convert predicate to predicate objects '''
        success, preds, err_msg = self.convert_predicate_names_to_obj(predicates, tables, aliases)
        if not success:
            return False, None, err_msg        

        ''' Form a new table to store all rows fulfill constraints '''
        # Table name should be changed?!
        result = Table("SelectQuery", column_objs)
        success, _, err_msg = self.insert_filtered_entities(tables, tables_obj, column_infos, preds, operator, result)
        if not success:
            return False, None, err_msg 

        ''' Create new table if aggregation exists '''
        success, result, err_msg = self.aggregate_table(column_infos, column_objs, result)
        if not success:
            return False, None, err_msg 
    
        return True, result, None 

    def predicate_check(self, predicates, operator, entity1, entity2):
        if not len(predicates):
            return True, None
        if operator == None:
            return predicates[0].evaluate_predicates(entity1, entity2)
        else:
            operator = operator.lower()
            bool1, err_msg = predicates[0].evaluate_predicates(entity1, entity2)
            if err_msg:
                return False, err_msg
            bool2, err_msg = predicates[1].evaluate_predicates(entity1, entity2)
            if err_msg:
                return False, err_msg
            return Operator.str2dt[operator](bool1, bool2), None

class Datatype():
    INT = 1
    VARCHAR = 2
    # mapping string to datatype
    str2dt = {'int':INT, 'varchar':VARCHAR}

class Operator():
    AND = Libop.and_
    OR = Libop.or_
    str2dt = {'and' : AND, 'or' : OR}
    
# each table
class Table:
    def __init__(self, name, columns):
        """The init fucntion of Table. It assumes that all columns are valid.
        Args:
            name (String): The table name.
            columns ([Column]): The Column objects .
        
        Todo: May need to create hidden column for non-pk table.
        """
        self.name = name
        self.columns = columns
        # data structure for entity may need to change 
        self.entities = []
        # dictionary for fast look up from col_name to its order in the table
        self.col_name2id = {}
        # hashtable initialize
        self.hashTable = EH()
        for i, c in enumerate(columns):
            self.col_name2id[c.name] = i
  
    def entity_is_vaild(self, entity):
        """The fucntion checks if the entity is fine to insert into the table.
        Args:
            entity (Entity): The entity we want to test.
        Returns:
            bool: The return value. True for valid, False otherwise.
            String: The error message. None if no error.
        
        Test:
            Check for empty key value
            Check if column values are valid
            Check that there are no keys with the same value
        
        Todo:
            Move Bool:key from Column to Table to save some time gererating key_id list
            
        """
        # Basic setup.
        # Get all order id that the corresponding column is marked as primary key
        key_id = []
        for i, c in enumerate(self.columns):
            if c.key:
                key_id.append((i,c))
        
        # Get all value that the corresponding column is marked as primary key
        entity_key_values = [v for (v, c) in zip(entity.values, self.columns) if c.key]
        
        
        # Check for empty key value
        for i, v in enumerate(entity_key_values):
            if not v:
                return False, "Empty value for primary key Column " + self.columns[i].name + "."
        
        
        # Check if column values are valid
        for v, c in zip(entity.values, self.columns):
            passed, err_msg = c.constraint.is_valid(v)
            if not passed:
                return False, err_msg
        
        
        # Check that there are no keys with the same value
        # Go through all entities, and check there are no same primary key
        # Can speed up by better Data Structure
        for e in self.entities:
            if not key_id:
                if (e.values[:] == entity.values[:]):
                    return False, "Duplicate data insertion"
            # Extract key column values of every entities, and compare with the one we want to test
            # If there's same combination, we say this entity is invalid
            if (entity_key_values == [e.values[i] for (i, c) in key_id]) and (key_id):
                return False, "Primary key pair (" + ','.join(str(v) for v in entity_key_values) + ") duplicate."
            
        # Pass all validation 
        return True, None

    def insert_without_check(self, values, col_names=None):
        """The function inserts a row into the table. Without checking anything. 
        Args:
            values ([int || String]): The value to insert.
            col_names ([String] || None): The column names. If this value is None, we will use default sequence.
        Returns:
            bool: The return value. True for successful insertion, False otherwise.
            String: The error message. None if no error.
        """
        # check if the col_name is in column
        # and convert the whole list to their order in the table
        col_ids = []
        if col_names:
            for n in col_names:
                if n not in self.col_name2id:
                    return False, "Column " + str(n) + " is not in Table " + self.name
                else:
                    # convert col_name to its order in the table and append to list
                    col_ids.append(self.col_name2id[n])

        # create Entitiy
        if col_names:
            entity = Entity(values, col_ids)
        else:
            entity = Entity(values)
        
        # insert entity
        self.entities.append(entity)
        return True, None 

    def insert(self, values, col_names=None):
        """The function inserts a row into the table. It will check if the given parameter is valid. 
        Args:
            values ([int || String]): The value to insert.
            col_names ([String] || None): The column names. If this value is None, we will use default sequence.
        Returns:
            bool: The return value. True for successful insertion, False otherwise.
            String: The error message. None if no error.
        """
        # check if the col_name is in column
        # and convert the whole list to their order in the table
        col_ids = []
        primary_key_val = None
        if col_names:
            for (val, col) in zip(values, col_names):
                if col not in self.col_name2id:
                    return False, "Column " + str(col) + " is not in Table " + self.name
                else:
                    # convert col_name to its order in the table and append to list
                    col_ids.append(self.col_name2id[col])
                    if self.get_column(col).key:
                        primary_key_val = val
        
        # check if len(values) is less than equal to len(columns)
        # should not accept too many value
        if len(values) > len(self.columns):
            return False, "Too many values are given"

        # create Entitiy
        if col_names:
            entity = Entity(values, col_ids)
        else:
            entity = Entity(values)

        # validate entity
        passed, err_msg = self.entity_is_vaild(entity)
        if not passed:
            return False, err_msg
        
        # insert entity
        self.entities.append(entity)

        # Insert Hash Table
        if primary_key_val:
            self.hashTable.put(primary_key_val, entity)

        return True, None  

    # Getting Column for the given name
    def get_column(self, name):
        for c in self.columns:
            if c.name == name:
                return c
        return None

class Column:
    def __init__(self, name, datatype, constraint_val, key):
        """The fucntion to create a column. It assumes that all parameter are valid. 
        Args:
            name (String): The column name.
            datatype (int): The column data types id, transformed by str2dt.
            constraint_val (int): The constraint value for each column.
            key (Bool): To indicate if the column is a primary key.
        """
        self.name = name
        # defines which type of data the column should accept
        self.datatype = datatype
        # Defines boundaries for the data
        # Create Constraint object
        if datatype == Datatype.INT:
            self.constraint = IntConstraint()
        elif datatype == Datatype.VARCHAR:
            self.constraint = VarcharConstraint(constraint_val)
        # Sets bool whether a column contains a key
        self.key = key
    
# each row
class Entity:
    def __init__(self, values, col_id=None):
        """The init fucntion to create an Entity. It assumes that all parameter are valid. 
        The order of the values in the Entity is sorted by col_id. 
        Use default sequence if col_id is None.
        Args:
            values ([String|int]): The value for the corresponding column.
            col_id ([int] | None): The order of the corresponding value. 
        """
        self.values = [None] * 10
        if col_id:
            for cid, v in zip(col_id, values):
                self.values[cid] = v
        else:
            self.values = values

class IntConstraint:
    def __init__(self):
        pass
    
    @staticmethod
    def is_valid(value):
        """The fucntion checks that value is an int within -2,147,483,648 to 2,147,483,647 
        Args:
            values (Any): The value to test.
        Returns:
            bool: The return value. True for valid, False otherwise.
            String: The error message. None if no error.
        """
        if not isinstance(value, int):
            return False, "Value " + str(value) + " is not int."
        if value < -2147483648 or value > 2147483647:
            return False, "Value " + str(value) + " out of range."
        return True, None

class VarcharConstraint:
    def __init__(self, max_len):
        """The init fucntion to create a VarcharConstraint. It assumes that max_len <= 40. 
        Args:
            max_len (int): The maximum length of a varchar.
        """
        self.max_len = max_len
        pass
    
    def is_valid(self, value):
        """The fucntion checks that length of varchar is within maximum length of a varchar.
        Args:
            values (Any): The value to test.
        Returns:
            bool: The return value. True for valid, False otherwise.
            String: The error message. None if no error.
        """
        if not isinstance(value, basestring):
            return False, "Value " + str(value) + " is not varchar."
        if len(value) > self.max_len:
            return False, "Value " + str(value) + " exceed maximum length " + str(self.max_len) + "."
        return True, None

class Aggregation:
    def __init__(self, func_name):
        """The init function of Aggregation. Set the function to apply on later.
        Args:
            func_name (String): The aggregation to apply. 
        """
        # map functions from String to functions
        funcs = {
            'sum': self.summation,
            'count': self.count,
        }
        self.func = funcs[func_name]
        self.func_name = func_name

    def aggregate(self, table, column_id):
        """To apply the function on table. 
        Args:
            table (Table): The table to apply aggregation function.
            column_id (Int | '*'): The column to apply aggregation function.
        Returns:
            Int: The return value after applying the aggregation function. None if error.
            String: The error message. None if no error.
        """
        return self.func(table, column_id)

    def summation(self, table, column_id):
        sum_of_col = None
        # sum can only apply on int column
        # not ok to apply sum on all columns
        if column_id == '*':
            return None, "Can not apply Sum() on '*'"
        # sum up rows with non-None value of that column 
        # None is not added
        else:
            # cannot apply sum on varchar column
            # use some int to test if valid for this column
            some_int = 34
            valid, err_msg = table.columns[column_id].constraint.is_valid(some_int)
            if not valid:
                return None, "Can not apply Sum() on '" + table.columns[column_id].name + "'"

            sum_of_col = sum([ent.values[column_id] for ent in table.entities])

        return sum_of_col, None

    def count(self, table, column_id):
        count_of_col = None
        # count row
        if column_id == '*':
            count_of_col = len(table.entities)
        # count rows with non-None value of that column 
        else:
            #count_of_col = len([e.values[column_id] for e in table.entities if e.values[column_id]])
            count_of_col = len([e.values[column_id] for e in table.entities])

            #for ent in table.entities[column_id]:
        return count_of_col, None


class Predicate:
    def __init__(self, rule1, op, rule2, table_names, column_names):
        """The init function of Predicate. rule contains value or table and column name. 
           op is the operation to perform on two rules.
        Args:
            rule1 (int, int, String|int):
                (Table id, column id, value)
                First Column or Value of the predicates
            op (String): The operation to perform.
            rule2 (int, int, String|int):
                (Table id, column id, value)
                Second Column or Value of the predicates
        Returns:
            bool: The return value. True for valid, False otherwise.
            String: The error message. None if no error.
        """
        self.rule1 = rule1
        self.rule2 = rule2
        self.op = op
        self.table_names = table_names
        self.column_names = column_names

    def rule_format(self, num):
        rule = self.rule1
        if num == 2:
            rule = self.rule2
        num -= 1
        if self.table_names[num] != None and self.column_names[num] != None:
            return self.table_names[num] + '.' + self.column_names[num]
        elif self.column_names[num] != None:
            return self.column_names[num]
        else:
            return str(rule[2])

    def evaluate_predicates(self, entity1, entity2):
        val1 = self.convert(entity1, entity2, self.rule1)
        val2 = self.convert(entity1, entity2, self.rule2)
        funcs = {
            '=' : self.equal,
            '>' : self.greater_than,
            '<' : self.less_than,
            '<>' : self.not_equal
        }
        if val2 is None:
            return val1, None
        if type(val1) != type(val2):
            return False, "Type mismatch for " + self.rule_format(1) + " and " + self.rule_format(2)
        return funcs[self.op](val1, val2)

    # convert entity to single value
    def convert(self, entity1, entity2, rule):
        # table id, column id, value
        tid, cid, value = rule
        if tid is None and cid is None:
            return value
        else:
            if tid == 0 and entity1 != None:
                return entity1.values[cid]
            else:
                return entity2.values[cid]

    def equal(self, val1, val2):
        if type(val1) != type(val2):
           return False, "Type mismatch for " + self.rule_format(1) + " and " + self.rule_format(2)
        return val1 == val2, None

    def greater_than(self, val1, val2):
        if isinstance(val1, basestring) or isinstance(val2, basestring):
            return False, "Cannot apply > on " + self.rule_format(1) + " and " + self.rule_format(2)
        return val1 > val2, None

    def less_than(self, val1, val2):
        if isinstance(val1, basestring) or isinstance(val2, basestring):
            return False, "Cannot apply < on " + self.rule_format(1) + " and " + self.rule_format(2)
        return val1 < val2, None

    def not_equal(self, val1, val2):
        if type(val1) != type(val2):
           return False, "Type mismatch for " + self.rule_format(1) + " and " + self.rule_format(2)
        return val1 != val2, None

"""
Temporary functions that insert fake data into views
Data visualization -- retrieve data only
"""
def get_all_table_names(database):
    table_names = ['Round Table','Square table','Triangle Table']
    return table_names

def get_table(table_name, database):
    title = ['title1','title2']
    content = [['row1 content1','row1 content2'],['row2 content1','row2 content2']]
    return title, content