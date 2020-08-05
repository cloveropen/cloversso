#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

import psycopg2
from api.config.config import DevelopmentConfig, ProductionConfig, TestingConfig

if os.environ.get('WORK_ENV') == 'PROD':
    app_config = ProductionConfig
elif os.environ.get('WORK_ENV') == 'TEST':
    app_config = TestingConfig
else:
    app_config = DevelopmentConfig

params = app_config.DB_CONN_CONFIG

# 测试数据库连接是否正常
def test_link():
    try:
        # connect to the PostgresQL database
        conn = psycopg2.connect(**params)
        # create a new cursor object
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute("SELECT * FROM clover_md.dict_hsp order by hsp_code")
        rs = cur.fetchall()
        # commit the changes to the database
        conn.commit()
        # close the communication with the PostgresQL database
        cur.close()
        if len(rs) < 1:
            print('error:hsp record not found')
            return -2
        print('db link success')
        return 0
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return -1
    finally:
        if conn is not None:
            conn.close()

# 插入删除更改数据
def upd_db(tsql):
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(tsql)
        conn.commit()
        cur.close()
        return 0
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return -1
    finally:
        if conn is not None:
            conn.close()

# 查询数据
def select_db(tsql):
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        tjsql = 'select array_to_json(array_agg(row_to_json(t))) from ( '+tsql+' ) AS t'
        cur.execute(tjsql)
        rows = cur.fetchall()
        str_array = ",".join(map(str, rows))

        print("str_array=",str_array)
        conn.commit()

        return str_array
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return -1
    finally:
        if conn is not None:
            cur.close()
            conn.close()

# 查询选定条件的最大主键
def sch_seq(tsql):
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(tsql)
        record = cur.fetchone()
        conn.commit()
        tseq = int(''.join(map(str, record)))
        return tseq
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return -1
    finally:
        if conn is not None:
            cur.close()
            conn.close()