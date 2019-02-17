from http.server import BaseHTTPRequestHandler
import cgi
from urllib.parse import urlparse, parse_qs
import threading
#import web
#from Controller import db,cv
CSS_CONTENT = '''
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
'''
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
        def _CreateTransitPage(self, data, waitSeconds = 0, forwordingPage = './index.html', ):
            print(data, len(data))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            if forwordingPage:
                self.send_header("refresh", '{};URL="{}"'.format(waitSeconds, forwordingPage))
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
            self.db.UpdateMember(entry, 'ADD')
            self._CreateTransitPage("成员添加成功，将跳转到首页...", 3, './index.html')

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
            self._CreateTransitPage("任务添加成功，将跳转到首页...", 3, './index.html')

        def do_POST(self):
            if self.path.endswith('add_member.submit'):
                self._AddMemberHandler()

            if self.path.endswith('add_task.submit'):
                self._AddTaskHandler()


        def do_GET(self):
            print(self)
            html = None
            data = None

            path = urlparse(self.path).path
            query = urlparse(self.path).query
            if path == '/' or path.endswith('index.html'):
                html = './Pages/index.html'
                with open(html) as f:
                    data = f.read()
            if path.endswith('add_member.do'):
                data = ADD_MEMBER_CONTENT
            if path.endswith('add_task.do'):
                data = self.GenerateAddTaskContent(self.db.ListMembers())
            if path.endswith('list_members.do'):
                data = self.GenerateListMembers(self.db.ListMembers())
            if path.endswith('list_tasks.do'):
                data = self.GenerateListTasks(self.db.ListTasks())
            if path.endswith('remove_task.do'):
                components = parse_qs(query)
                print('Get query:', components)
                entry = {}
                entry['code'] = components['code'][0]
                self.db.UpdateTask(entry,'DEL')
                data = self.GenerateListTasks(self.db.ListTasks())
            if path.endswith('remove_member.do'):
                components = parse_qs(query)
                print('Get query:', components)
                entry = {}
                entry['id'] = components['id'][0]
                self.db.UpdateMember(entry,'DEL')
                data = self.GenerateListMembers(self.db.ListMembers())

            if not data:
                return
            print(data)
            self._CreatePage(data)

            return

        def GenerateListTasks(self, entries):
            LIST_TASKS = '''<body>''' + CSS_CONTENT
            LIST_TASKS += '''         
            <br><left><input type="submit" onclick='javascript:history.go(-1);' value="返回"></left>
            <right><input type="submit" onclick='location.href="./index.html"' value="首页"></right>
            </br>
            <table>
            <TH></TH>
            '''
            i = 1

            for entry in entries:
                LIST_TASKS += "<TR> <td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><a href='remove_task.do?code={}'>删除</a></td></TR>".format(i, entry['taskName'][0:80],
                                                                              self.db.GetRemarkNameById(entry['taskOwnerId']),
                                                                              entry['site'],
                                                                              entry['code'],
                                                                              entry['code'])
                i += 1
            LIST_TASKS += '''
            </TABLE></body>
            '''

            return LIST_TASKS

        def GenerateListMembers(self, entries):
            LIST_TASKS = '''<body>
             <br><input type="submit" onclick='javascript:history.go(-1);' value="返回">
             <right><input type="submit" onclick='location.href="./index.html"' value="首页"></right>
             </br>
             <table>
             <TH></TH>
             '''
            i = 1
            for entry in entries:
                LIST_TASKS += "<TR> <td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><a href='remove_member.do?id={}'>删除</a></td></TR>".format(i,
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

        # Input: ListMembers
        def GenerateAddTaskContent(self, entries):

            if len(entries) == 0:
               self._CreateTransitPage('成员列表为空，请先添加...', 3, './index.html')
               return
            print(entries)
            ADD_TASK_CONTENT = """
            <body>
            <script type="text/javascript">
            function myCheck()
            {
               for(var i=0;i<document.addTask.elements.length-1;i++)
               {
                  if(document.addTask.elements[i].value=="")
                  {
                     alert(document.addMember.elements[i].name + "不能为空");
                     document.addTask.elements[i].focus();
                     return false;
                  }
               }
               return true;
              
            }
            </script>
            <br><input type="submit" onclick='javascript:history.go(-1);' value="返回">
            <right><input type="submit" onclick='location.href="./index.html"' value="首页"></right></br>
            <form name = 'addTask' method = 'post' action="add_task.submit" onSubmit="return myCheck()">
            任务概述(80字以内):<br>
            <input type="text" name="taskName" value="" size=100%>
            <br>经办人:<br>
            <select name="taskOwnerId">"""
            for entry in entries:
                ADD_TASK_CONTENT += '<option value="{}">{}</option>'.format(entry['id'], entry['remarkName'])
            ADD_TASK_CONTENT += """
            </select>
            <br>维护地点:<br>
            <input type="text" name="site" value="" size=100%>
            <br>通知频率（计时单位：小时)<br>
            <input type="number" name="clock" value="">
            <br>
            <input type="submit" value="Submit">
            </form>
            </body>
            <foot></foot>
            """
            return ADD_TASK_CONTENT

    return HttpHandler


ADD_MEMBER_CONTENT='''<body>
<script type="text/javascript">
            function myCheck()
            {
               for(var i=0;i<document.addMember.elements.length-1;i++)
               {
                  if(document.addMember.elements[i].value=="")
                  {
                     alert(document.addMember.elements[i].name + "不能为空");
                     document.addMember.elements[i].focus();
                     return false;
                  }
               }
               return true;
              
            }
            </script>
<br><input type="submit" onclick='javascript:history.go(-1);' value="返回">
<right><input type="submit" onclick='location.href="./index.html"' value="首页"></right></br>
<form name='addMember' method = 'post' action="add_member.submit" onSubmit='return myCheck()'>
备注名:<br>
<input type="text" name="remarkName" value="">
<br>
微信用户ID:<br>
<input type="text" name="userId" value="">
<br>
手机号:<br>
<input type="text" name="mobile" value="">
<br><br>
<input type="submit" value="Submit">
</form> 
</body>
<foot></foot>
'''
