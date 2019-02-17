#!/usr/bin/Python
# -*- coding:utf-8 -*-
import sys

import threading
import cgi
import itchat
from Db import DbHandler
import queue
from Utils import TIMEFORMAT
import time,datetime
from HttpHandler import MakeHttpHandler
from http.server import HTTPServer
#import web

global db 
db = DbHandler()

cv = threading.Condition()
taskQueueLock = threading.Lock()
taskQueue = queue.Queue()


def WebEntry(port = 80):
   print('Web thread:%s' % threading.current_thread().getName())
   serverAddress = ('', port)
   HttpHandler = MakeHttpHandler(db, cv)
   server = HTTPServer(serverAddress, HttpHandler)
   server.serve_forever()
   
def WeChatEntry():
   print('WeChat thread:%s' % threading.current_thread().getName())
   itchat.run(debug=True)
   return

def GetTaskTitleByCode(code):
   return db.GetTaskTitleByCode(code)

def RemoveTaskByCode(code):
   ret = db.RemoveTaskByCode(code)
   return ret

@itchat.msg_register([itchat.content.TEXT])
def WeChatReceiveHandler(msg):
   # user is in the User list, then look through the database
   # And see if the data is completed.
   # If yes, update the database.
   # Else, call the Microsoft xiaobing's API
   user = msg.User.RemarkName
   content = msg.content
   #print('>>>',content)
   code = content.strip()
   entries = db.ListMembers()
   Whitelist = [entry['remarkName'] for entry in entries]
   if user not in Whitelist:
      return
   taskTitle = GetTaskTitleByCode(code)
   if not taskTitle:
      return
   toUserName = msg.FromUserName
   itchat.send(u'[测试]任务({}...)已经完成，谢谢!'.format(taskTitle[0:30]),toUserName=toUserName)
   # TODO: check the result
   RemoveTaskByCode(code)

def GetToUserName(remarkName):
   #Get toUserName by remarkName
   user = itchat.search_friends(remarkName=remarkName)
   print('remarkName: %s user:%s' % (remarkName,user))
   return user[0] if user else None

def IsDebug():
   return True

def UpdateTaskNextAlert(entry):
   clock = entry['clock']
   alert = entry['nextAlert']
   old = datetime.datetime.strptime(alert, TIMEFORMAT)
   if not IsDebug():
      delta =  datetime.timedelta(hours=int(clock))
   else:
      delta =  datetime.timedelta(seconds=int(clock))
   nextAlert = old + delta
   entry['nextAlert'] = datetime.datetime.strftime(nextAlert,TIMEFORMAT)
   db.UpdateTask(entry, 'Update')

def SendReminder():
   #taskQueueLock.acqure()
   while not taskQueue.empty():
      entry = taskQueue.get()
      taskOwnerId = entry['taskOwnerId']
      remarkName = db.GetRemarkNameById(taskOwnerId)
      #print(remarkName)
      taskName = entry['taskName']
      code = entry['code']
      clock = entry['clock']
      code = code.strip()
      toUser = GetToUserName(remarkName)
      msg = u'[测试]{}，{}，请尽快完成。如果已经完成，请回复任务完成码：{}. 在完成之前，将每{}小时提醒一次，敬请谅解。'.format(remarkName, taskName, code, clock)
      if toUser:
         if IsDebug():
            print('User %s' % toUser)
         toUser.send_msg(msg)

def PutEntryToRun(entries):
   #taskQueueLock.acqure()
   for entry in entries:
      #print(entry)
      taskQueue.put(entry)
   #taskQueue.release()
   SendReminder()

def Scheduler():
   print('Scheduler thread:%s' % threading.current_thread().getName())
   while True:
		# Read through the todo table and pick up the earlist
		# entry to wakup.
      entries = db.ListTasks()
      print(entries)
      RunableEntries = []
      earliestTime = datetime.datetime.max
      earliestTime = earliestTime.strftime(TIMEFORMAT)
      earliestTime = time.strptime(earliestTime, TIMEFORMAT)
      now = datetime.datetime.now()
      now = now.strftime(TIMEFORMAT)
      now = time.strptime(now, TIMEFORMAT)
      #print(earliestTime, now)
      #print('Start run >>>>')
      for entry in entries:
         #entry = list(entry)
         #print(entry['nextAlert'])

         nextAlert = time.strptime(entry['nextAlert'],TIMEFORMAT)
         print('<<<<',nextAlert, now)
         if nextAlert <= now:
            #print('***',entry, now)
            RunableEntries.append(entry)
            UpdateTaskNextAlert(entry)
            nextAlert = time.strptime(entry['nextAlert'], TIMEFORMAT)

         if nextAlert < earliestTime:
            earliestTime = nextAlert
      if len(RunableEntries) != 0:
         print('Start to put', RunableEntries)
         PutEntryToRun(RunableEntries)
         intervalSeconds = time.mktime(earliestTime) - time.mktime(now)
      else:
         intervalSeconds = None
      cv.acquire()
      cv.wait(timeout=intervalSeconds)
      cv.release()

def PrepareDatabase():
   # If the database is empty, create one.
   # Prepare all the user lists.
   pass

def Main():
   # Thread to handle the add event.
   PrepareDatabase()
   itchat.auto_login(hotReload=True, enableCmdQR=2)
   threads = []
   thread = threading.Thread(target=WebEntry, args=([8090]))
   threads.append(thread)
   thread = threading.Thread(target=WeChatEntry)
   threads.append(thread)
   thread = threading.Thread(target=Scheduler)
   threads.append(thread)
   for t in threads:
      t.start()
   for t in threads:
      t.join()

if __name__ == '__main__':
   Main()
