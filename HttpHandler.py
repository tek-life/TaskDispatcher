from http.server import BaseHTTPRequestHandler
import cgi
#import web
#from Controller import db,cv


def MakeHttpHandler(db, cv):
    class HttpHandler(BaseHTTPRequestHandler):
        def __init__(self,*argc, **argv):
            self.db = db
            self.cv = cv
            super().__init__(*argc, **argv)

        def _CreatePage(self, data):
            print(data, len(data))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            # self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(bytes(data, encoding='utf-8'))

        def _Wrapper(self, data):
            return bytes(data, encoding='utf-8')

        def _AddMemberHandler(self):
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
            entry = {}

            entry['remarkName'] = form['remarkName'].value
            entry['userId'] = form['userId'].value
            entry['mobile'] = form['mobile'].value
            entry['isExist'] = 1
            self.db.UpdateUser(entry, 'ADD')

        def _AddTaskHandler(self):
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
            entry = {}
            print(form)
            entry['taskName'] = form['taskName'].value
            entry['taskOwnerId'] = form['taskOwnerId'].value
            entry['site'] = form['site'].value
            entry['clock'] = form['clock'].value
            self.db.UpdateTask(entry, 'ADD')
            self.cv.acquire()
            self.cv.notify()
            self.cv.release()

        def do_POST(self):
            if self.path.endswith('add_member.submit'):
                self._AddMemberHandler()
            if self.path.endswith('add_task.submit'):
                self._AddTaskHandler()

            self._CreatePage("Add successfully!")

        def do_GET(self):
            html = None
            data = None
            if self.path == '/' or self.path.endswith('index.html'):
                html = './Pages/index.html'
                with open(html) as f:
                    data = f.read()
            if self.path.endswith('add_member.do'):
                data = ADD_MEMBER_CONTENT
            if self.path.endswith('add_task.do'):
                data = GenerateAddTaskContent(self.db.ListMembers())
            if self.path.endswith('list_members.do'):
                data = self.GenerateListMembers(self.db.ListMembers())
            if self.path.endswith('list_tasks.do'):
                data = self.GenerateListTasks(self.db.ListTasks())
            if not data:
                return
            print(data)
            self._CreatePage(data)
            return

        def GenerateListTasks(self, entries):
            LIST_TASKS = '''<body>
            <br><input type="submit" onclick='javascript:history.go(-1);' value="返回"></br>
            <table>
            <TH></TH>
            '''
            i = 1

            for entry in entries:
                LIST_TASKS += "<TR> <td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><a href='removeTask.do?id={}'>删除</a></td></TR>".format(i, entry['taskName'][0:80],
                                                                              self.db.GetRemarkNameById(entry['taskOwnerId']),
                                                                              entry['site'],
                                                                              entry['id'])
                i += 1
            LIST_TASKS += '''
            </TABLE></body>
            '''

            return LIST_TASKS

        def GenerateListMembers(self, entries):
            LIST_TASKS = '''<body>
             <br><input type="submit" onclick='javascript:history.go(-1);' value="返回"></br>
             <table>
             <TH></TH>
             '''
            i = 1
            for entry in entries:
                LIST_TASKS += "<TR> <td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><a href='removeTask.do?id={}'>删除</a></td></TR>".format(i,
                                                                                              entry['remarkName'][0:80],
                                                                                              entry['userId'],
                                                                                              entry['mobile'],
                                                                                              entry['isExist'],
                                                                                              entry['id'])
                i += 1
            LIST_TASKS += '''
             </TABLE></body>
             '''
            return LIST_TASKS
    return HttpHandler


ADD_MEMBER_CONTENT='''<body>
<br><input type="submit" onclick='javascript:history.go(-1);' value="返回"></br>
<form method = 'post' action="add_member.submit">
备注名:<br>
<input type="text" name="remarkName" value="备注名">
<br>
微信ID:<br>
<input type="text" name="userId" value="微信ID">
<br>
手机号:<br>
<input type="text" name="mobile" value="13001234567">
<br><br>
<input type="submit" value="Submit">
</form> 
</body>
<foot></foot>
'''
#Input: ListMembers
def GenerateAddTaskContent(entries):
    print(entries)
    ADD_TASK_CONTENT ="""
    <body>
    <br><input type="submit" onclick='javascript:history.go(-1);' value="返回"></br>
    <form method = 'post' action="add_task.submit">
    任务概述:<br>
    <input type="text" name="taskName" value="任务简述(80字以内)" size=100%>
    <br>经办人:<br>
    <select name="taskOwnerId">"""
    for entry in entries:
        ADD_TASK_CONTENT += '<option value="{}">{}</option>'.format(entry['id'], entry['remarkName'])
    ADD_TASK_CONTENT += """
    </select>
    <br>维护地点:<br>
    <input type="text" name="site" value="地址:" size=100%>
    <br>通知频率<br>
    <input type="number" name="clock" value="计时单位(小时)">
    <br>
    <input type="submit" value="Submit">
    </form>
    </body>
    <foot></foot>
    """
    return ADD_TASK_CONTENT
