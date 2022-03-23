import pyodbc
import logging
from typing import List
from utils.config import AZURE_DB_CONNECTION_STRING


def query(query: str) -> List[tuple]:

    cnxn = pyodbc.connect(AZURE_DB_CONNECTION_STRING)
    cursor = cnxn.cursor()

    cursor.execute(query)

    result = cursor.fetchall()
    cnxn.close()

    return result

def insert(table: str, record: str) -> None:

    cnxn = pyodbc.connect(AZURE_DB_CONNECTION_STRING)
    cursor = cnxn.cursor()

    statement = f"INSERT INTO [{table}] VALUES ({record})"

    try:
        cursor.execute(statement)
        cursor.commit()
    except Exception as e:
        logging.critical(e)
        logging.critical(statement)

    cnxn.close()

def insert_or_update(table: str, key: List[str], record: dict) -> None:

    record = clean_text(record)

    with pyodbc.connect(AZURE_DB_CONNECTION_STRING) as cnxn:
        cursor = cnxn.cursor()
        statement = f"""\
begin tran
   UPDATE {table}
   SET {', '.join([f"[{column}] = '{value}'" for column, value in record.items()])}
   where {' and '.join(f"[{key}] = '{record[key]}'" for key in key)}

   if @@rowcount = 0
   begin
      INSERT INTO {table} ({', '.join([f"[{column}]" for column in record.keys()])}) 
      VALUES ({', '.join([f"'{value}'" for value in record.values()])})
   end
commit tran
""".replace("\n", " ")

        try:
            cursor.execute(statement)
        except:
            logging.warn(statement)

def insert_many(table: str, columns: tuple, records: list[tuple]) -> None:

    cnxn = pyodbc.connect(AZURE_DB_CONNECTION_STRING)
    cursor = cnxn.cursor()

    cursor.fast_executemany = True

    sql_statement = f"INSERT INTO {table} ([{'], ['.join(columns)}]) VALUES ({'?, '.join(['' for _ in range(len(columns))]) + '?'})"
    cursor.executemany(sql_statement, records)
    cursor.commit()

    cnxn.close()

def update(table: str, key_column: str, key_value: str, record: List[tuple]) -> None:

    cnxn = pyodbc.connect(AZURE_DB_CONNECTION_STRING)
    cursor = cnxn.cursor()

    statement = f"""
UPDATE {table}
SET {', '.join([f"[{column}] = '{value}'" for column, value in record])}
WHERE [{key_column}] = '{key_value}'
    """

    cursor.execute(statement)
    cursor.commit()

    cnxn.close()

def clean_text(record: dict) -> dict:
    for key, value in record.items():
        if isinstance(value, str):
            record[key] = value.replace("'", "''")
    return record