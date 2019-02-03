#!/usr/bin/Python
# -*- coding:utf-8 -*-
import sqlite3
import random
import string
import datetime, time
from Utils import TIMEFORMAT

CREATE_TABLE_TASKS = "create table if not exists TASKS (id INTEGER PRIMARY KEY AUTOINCREMENT, taskName varchar(160), taskOwnerId integer,site varchar(100) , code varchar(8) UNIQUE, clock integer default(3), nextAlert text,  isValid integer default(1))"
CREATE_TABLE_MEMBERS = "create table if not exists MEMBERS (id integer primary key AUTOINCREMENT, remarkName varchar(100), mobile varchar(20), userId varchar(50) UNIQUE, isExist integer default(1))"
class DbHandler:
   def __init__(self):
      conn = sqlite3.connect('./sqlite.db',check_same_thread=False)
      conn.row_factory = sqlite3.Row
      self.conn = conn
      self.cursor = self.conn.cursor()
      self.cursor.execute(CREATE_TABLE_TASKS)
      self.cursor.execute(CREATE_TABLE_MEMBERS)
      self.conn.commit()

   def GetMemberId(self, remarkName):
      sql = 'select id from MEMBERS where remarkName="{}"'.format(remarkName)
      ret = self.cursor.execute(sql)
      self.conn.commit()
      return ret.fetchone()[0]

   def GetRemarkNameById(self, taskOwnerId):
      sql = 'select remarkName from MEMBERS where id="{}"'.format(taskOwnerId)
      ret = self.cursor.execute(sql)
      self.conn.commit()
      return ret.fetchone()[0]

   def GetTaskTitleByCode(self, code):
      print(code)
      sql = 'select * from TASKS where code ="{}"'.format(code)
      ret = self.cursor.execute(sql)
      self.conn.commit()
      if not ret:
         return None
      return ret.fetchone()[0]
      #return ret

   #TODO: enhance. Could integrate with UpdateTask
   def RemoveTaskByCode(self, code):
      sql = 'update TASKS set isValid = 0 where code = "{}"'.format(code)
      ret = self.cursor.execute(sql)
      self.conn.commit()
      return ret.fetchone()[0]

   def UpdateTask(self, entry, operation):
      sql = None
      if operation == 'ADD':
         taskName = entry['taskName']
         #remarkName = entry['remarkName']
         site = entry['site']
         clock = int(entry['clock'])
         taskOwnerId = entry['taskOwnerId']
         #taskOwnerId = self.GetMemberId(remarkName)
         if not taskOwnerId:
            return False, '微信备注名无效，请检查'
         isValid = 1
         endTime = datetime.datetime.now() #+ datetime.timedelta(hours=clock)
         nextAlert = endTime.strftime(TIMEFORMAT)

         code = ''.join(random.sample(string.ascii_uppercase + string.digits, 8))
         sql = 'INSERT INTO TASKS (taskName, taskOwnerId, site, clock, code, nextAlert, isValid) values("{}",{},"{}",{},"{}","{}",{})'\
               .format(taskName, taskOwnerId, site, clock, code, nextAlert, isValid)
         print(sql)
      if operation == 'Remove':
         taskOwner = entry['owner']
         code = entry['code']
         sql = 'delete from TASKS where code = {}'.format(code)
      if operation == 'Update':
         taskName = entry['taskName']
         taskOwnerId = entry['taskOwnerId']
         clock = int(entry['clock'])
         nextAlert = entry['nextAlert']
         isValid = entry['isValid']
         code = entry['code']
         sql = 'UPDATE TASKS SET taskName = "{}", taskOwnerid = "{}",clock = "{}", nextAlert="{}", isValid="{}" where code = "{}"'\
            .format(taskName, taskOwnerId, clock, nextAlert, isValid, code)
      if not sql:
         return
      self.cursor.execute(sql)
      self.conn.commit()
      return True, 'Success'

   def UpdateUser(self, entry, operation):
      sql = None
      if operation == 'ADD':
         remarkName = entry['remarkName']
         userId = entry['userId']
         mobile = entry['mobile']
         isExist = entry['isExist']
         sql = 'INSERT INTO MEMBERS (remarkName, userId, mobile, isExist) VALUES ("{}","{}","{}","{}")'.format(remarkName, userId, mobile, isExist) 
      '''
      if operation == 'Remove':
         sql = 
      if operation == 'Update':
         sql = 
      if not sql:
         return
      self.cursor.execute()
      '''
      self.cursor.execute(sql)
      self.conn.commit()


   def ListTasks(self):
      sql = 'select * from TASKS where isValid = 1'
      ret = self.cursor.execute(sql)
      dictrows = [dict(row) for row in ret]
      return dictrows

   def ListMembers(self):
      sql = 'select * from MEMBERS'
      ret = self.cursor.execute(sql)
      dictrows = [dict(row) for row in ret]
      return dictrows


