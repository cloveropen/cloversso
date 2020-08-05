#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import sys
import traceback

from flask import Blueprint
from flask import request
from api.utils.responses import response_with
from api.utils import responses as resp
from api.config.config import DevelopmentConfig, ProductionConfig, TestingConfig
import requests as rq
import api.utils.database as db

login_routes = Blueprint("login_routes", __name__)

if os.environ.get('WORK_ENV') == 'PROD':
    app_config = ProductionConfig
elif os.environ.get('WORK_ENV') == 'TEST':
    app_config = TestingConfig
else:
    app_config = DevelopmentConfig


# 获取TGT(Ticket Granting Ticket)
# 入参:
# {
#     "username":"8888",
#     "password":"eastwill",
#     "service":"https://clover.app-hos.com"
# }
# 出参:
# {
#  "tgt": "TGT-9-EEQuCcFmwHZMUPluzQYRlsybCexoFkg2gKsLysyXUmVX3OdX2Bye8-hecs-x-xlarge-2-linux-20200618093719",
#  "code": "success"
# }
@login_routes.route('/gettgt', methods=['POST'])
def get_tgt():
    try:
        tdata_in_tgt = request.get_data()
        json_data = json.loads(tdata_in_tgt.decode("utf-8"))
        topcode = json_data.get('username')
        tpasswd = json_data.get('password')

        tcas_url = app_config.CAS_URL
        tcas_url = tcas_url + '/cas/v1/tickets'
        tsrv_url = app_config.SERVICE_URL
        print('tcas_url=', tcas_url)
        tgt = req_tgt(tcas_url, topcode, tpasswd, tsrv_url)
        print('tgt=', tgt)
        # 写入数据库(如果存在opcode就更新)
        save_db_tgt(topcode, tsrv_url, tgt)

        return response_with(resp.SUCCESS_201, value={'tgt': tgt})
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        return response_with(resp.INVALID_INPUT_422, value={'error': error})


# 用TGT获取ST
# 入参
# {
#     "tgt":"TGT-1-yDn9yLMY8MpvVDMdQsYxHvJRFCaZkZ6GRbQBVtcP-S2CmQunhyk-hecs-x-xlarge-2-linux-20200618093719",
#     "username":"8888",
#     "service":"https://clover.app-hos.com"
# }
# 出参
# {
#  "code": "success",
#  "st": "ST-1-9nr2LtgqiItzDIggPZzu4-c0jPc-hecs-x-xlarge-2-linux-20200618093719"
# }
@login_routes.route('/getst', methods=['POST'])
def get_st():
    st = ''
    try:
        tdata_inst = request.get_data()
        json_data = json.loads(tdata_inst.decode("utf-8"))
        topcode = json_data.get('username')
        tgt = json_data.get('tgt')
        tcas_url = app_config.CAS_URL
        # tcas_url = tcas_url + '/cas/v1/tickets/' + tgt
        tsrv_url = app_config.SERVICE_URL

        st = reg_st(tcas_url, tgt, tsrv_url)
        # 写入数据库(如果存在opcode就更新)
        save_db_st(topcode, tsrv_url, tgt, st)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        return response_with(resp.SERVER_ERROR_404, value={'error': error})

    return response_with(resp.SUCCESS_200, value={'st': st})


# 获取ST一步完成(合并获取TGT+ST)
# 入参:
# {
#     "username":"8888",
#     "password":"eastwill",
#     "service":"https://clover.app-hos.com"
# }
# 出参:
# 出参
# {
#  "code": "success",
#  "st": "ST-1-9nr2LtgqiItzDIggPZzu4-c0jPc-hecs-x-xlarge-2-linux-20200618093719"
# }
@login_routes.route('/getstall', methods=['POST'])
def get_stall():
    st = ''
    try:
        tdata_in_all = request.get_data()
        json_data = json.loads(tdata_in_all.decode("utf-8"))
        topcode = json_data.get('username')
        tpasswd = json_data.get('password')

        tcas_url = app_config.CAS_URL
        tcas_url = tcas_url + '/cas/v1/tickets'
        tsrv_url = app_config.SERVICE_URL

        # 1 获取tgt
        tgt = req_tgt(tcas_url, topcode, tpasswd, tsrv_url)
        # 写入tgt数据库(如果存在opcode就更新)
        save_db_tgt(topcode, tsrv_url, tgt)
        # 2 获取st
        tcas_url = app_config.CAS_URL
        st = reg_st(tcas_url, tgt, tsrv_url)
        # 写入st数据库(如果存在opcode就更新)
        save_db_st(topcode, tsrv_url, tgt, st)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        return response_with(resp.SERVER_ERROR_404, value={'error': error})

    return response_with(resp.SUCCESS_200, value={'st': st})


# 查询TGT状态
# 入参:
# {
#     "tgt":"TGT-1-yDn9yLMY8MpvVDMdQsYxHvJRFCaZkZ6GRbQBVtcP-S2CmQunhyk-hecs-x-xlarge-2-linux-20200618093719"
# }
# 出参: 如果成功返回TGT，如果没有找到返回
# {
#   "code": "success",
#   "tgt": "Ticket could not be found"
# }
@login_routes.route('/sch_tgt_status', methods=['POST'])
def sch_tgt_status():
    tdata_input = request.get_data()
    json_data = json.loads(tdata_input.decode("utf-8"))
    tgt = json_data.get('tgt')
    tcas_url = app_config.CAS_URL
    tcas_url = tcas_url + '/cas/v1/tickets/' + tgt
    try:
        rep = rq.get(tcas_url)
        trep_str = rep.text
        print('查询TGT状态返回', rep.status_code, rep.text)
        return response_with(resp.SUCCESS_200, value={'tgt': trep_str})
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        return response_with(resp.SERVER_ERROR_500, value={'tgt': error})


# 验证ST票据
# 入参
# {
#     "st":"TGT-1-yDn9yLMY8MpvVDMdQsYxHvJRFCaZkZ6GRbQBVtcP-S2CmQunhyk-hecs-x-xlarge-2-linux-20200618093719",
#     "service":"https://clover.app-hos.com"
# }
# 出参
# 成功返回
# {
#   "code": "success",
#   "tgt": "<cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>\n    <cas:authenticationSuccess>\n        <cas:user>8888</cas:user>\n        <cas:attributes>\n            <cas:credentialType>UsernamePasswordCredential</cas:credentialType>\n            <cas:isFromNewLogin>true</cas:isFromNewLogin>\n            <cas:authenticationDate>2020-08-05T07:10:09.134002Z</cas:authenticationDate>\n            <cas:authenticationMethod>QueryDatabaseAuthenticationHandler</cas:authenticationMethod>\n            <cas:successfulAuthenticationHandlers>QueryDatabaseAuthenticationHandler</cas:successfulAuthenticationHandlers>\n            <cas:longTermAuthenticationRequestTokenUsed>false</cas:longTermAuthenticationRequestTokenUsed>\n            </cas:attributes>\n    </cas:authenticationSuccess>\n</cas:serviceResponse>\n"
# }
# 失败返回
# {
#   "code": "success",
#   "tgt": "<cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>\n    <cas:authenticationFailure code=\"INVALID_TICKET\">Ticket &#39;ST-52-7n8yxGHp0cEx8M5uUVbTfbPDt00-hecs-x-xlarge-2-linux-20200618093719&#39; not recognized</cas:authenticationFailure>\n</cas:serviceResponse>\n"
# }
@login_routes.route('/validate_st', methods=['POST'])
def validate_st():
    tdata_input = request.get_data()
    json_data = json.loads(tdata_input.decode("utf-8"))
    tst = json_data.get('st')
    tsrv_url = json_data.get('service')
    tcas_url = app_config.CAS_URL
    tcas_url = tcas_url + '/cas/p3/serviceValidate?service=' + tsrv_url + '&ticket=' + tst
    try:
        rep = rq.get(tcas_url)
        trep_str = rep.text
        print('验证ST票据返回', rep.status_code, rep.text)
        return response_with(resp.SUCCESS_200, value={'tgt': trep_str})
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        return response_with(resp.SERVER_ERROR_500, value={'st': error})

# 销毁TGT票据
# 入参:
# {
#     "tgt":"TGT-1-yDn9yLMY8MpvVDMdQsYxHvJRFCaZkZ6GRbQBVtcP-S2CmQunhyk-hecs-x-xlarge-2-linux-20200618093719",
#     "username":"9999"
# }
# 出参: 如果成功返回空，如果失败返回error,成功返回
# {
#  "code": "success",
#  "tgt": ""
# }
@login_routes.route('/del_tgt', methods=['POST'])
def del_tgt():
    tdata_input = request.get_data()
    json_data = json.loads(tdata_input.decode("utf-8"))
    tgt = json_data.get('tgt')
    topcode = json_data.get('username')
    tcas_url = app_config.CAS_URL
    tcas_url = tcas_url + '/cas/v1/tickets/' + tgt
    try:
        rep = rq.delete(tcas_url)
        trep_str = rep.text
        print('销毁TGT票据返回', rep.status_code, rep.text)
        # 删除数据表中的票据记录
        tsql = "DELETE FROM clover_md.kd99_ticket_tgt WHERE opcode='" + topcode + "' and tgt = '"+ tgt + "'"
        db.upd_db(tsql)
        tsql = "DELETE FROM clover_md.kd99_ticket_st WHERE opcode='" + topcode + "' and tgt = '"+ tgt + "'"
        db.upd_db(tsql)
        return response_with(resp.SUCCESS_200, value={'tgt': trep_str})
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        return response_with(resp.SERVER_ERROR_500, value={'error': error})

# 请求TGT
def req_tgt(tcas_url, topcode, tpasswd, tsrv_url):
    data_str = 'username=' + topcode + '&password=' + tpasswd + '&service=' + tsrv_url
    theaders = {
        'Content-Type': 'Application/x-www-form-urlencoded;charset:utf-8;'
    }
    # 发送CAS服务器提交认证
    try:
        rep = rq.post(tcas_url, data=data_str, headers=theaders)
        trep_str = rep.text
        print('获取tgt返回', rep.status_code)
        if rep.status_code != 201:
            return rep.text
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        return error

    tbnumb = trep_str.find("tickets", 0, len(trep_str))
    trep_str = trep_str[tbnumb + 8:]
    tenumb = trep_str.find('"', 0, len(trep_str))
    tgt = trep_str[0:tenumb]
    return tgt


# 请求ST
def reg_st(tcas_url, tgt, tsrv_url):
    st = ''
    tcas_url = tcas_url + '/cas/v1/tickets/' + tgt
    data_str = {'service': tsrv_url}
    tcont_len = get_content_length(data_str)

    theaders = {
        "Host": "clover.app-hos.com",
        "Accept": "*/*",
        "Content-Length": str(tcont_len),
        'Content-Type': 'application/x-www-form-urlencoded',
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "PostmanRuntime/7.26.2"
    }
    # 发送CAS服务器提交认证
    try:
        rep = rq.post(tcas_url, data=data_str, headers=theaders)
        print('获取ST返回状态码:', rep.status_code)
        if rep.status_code != 200:
            return rep.text
    except:
        st = rep.text
    st = rep.text
    return st


# tgt 写入数据库
def save_db_tgt(topcode='', tsrv_url='', tgt=''):
    tsql = "SELECT coalesce(max(seq),0) FROM clover_md.kd99_ticket_tgt where opcode='" + topcode + "'"
    print('tsql=', tsql)
    tseq = db.sch_seq(tsql)
    print('tseq = ', tseq)
    if tseq > 0:
        tsql = "UPDATE clover_md.kd99_ticket_tgt SET srv_url='" + tsrv_url + "', tgt='" + tgt + "', valid_time= now()+interval '28800s', create_time=now()	WHERE seq =" + str(
            tseq) + " and opcode = '" + topcode + "'"
    else:
        tsql = "INSERT INTO clover_md.kd99_ticket_tgt(seq, opcode, hsp_code, srv_url, tgt, valid_time, create_time)"
        tsql = tsql + "VALUES (nextval('clover_md.seq_kd99_ticket_tgt'), '" + topcode + "', '', '" + tsrv_url + "', '" + tgt + "', now()+interval '28800s', now())"
    print('tsql=', tsql)
    db.upd_db(tsql)


# st 写入数据库
def save_db_st(topcode='', tsrv_url='', tgt='', st=''):
    print('topcode=',topcode)
    tsql = "SELECT coalesce(max(seq),0) FROM clover_md.kd99_ticket_st where opcode='" + topcode + "'"
    print('save_db_st tsql=', tsql)
    tseq = db.sch_seq(tsql)
    print('tseq = ', tseq)
    if tseq > 0:
        tsql = "UPDATE clover_md.kd99_ticket_st SET srv_url ='" + tsrv_url + "', tgt ='" + tgt + "',st ='" + st + "', valid_time =now()+interval '28800s', create_time=now()"
        tsql = tsql + "WHERE seq =" + str(tseq) + " and opcode = '" + topcode + "'"
    else:
        tsql = "INSERT INTO clover_md.kd99_ticket_st(seq, opcode, hsp_code, srv_url, tgt, st, valid_time, valid_num, create_time)"
        tsql = tsql + "VALUES (nextval('clover_md.seq_kd99_ticket_st'), '" + topcode + "', '', '" + tsrv_url + "', '" + tgt + "', '" + st + "', now()+interval '28800s',10, now())"

    print('tsql=', tsql)
    db.upd_db(tsql)


# 计算headers的content-length
def get_content_length(data):
    length = len(data.keys()) * 2 - 1
    total = ''.join(list(data.keys()) + list(data.values()))
    length += len(total)
    return length
