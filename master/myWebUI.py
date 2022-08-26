import os
import signal
import time
from flask import Flask,request,url_for,redirect,flash
from flask import render_template
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sql_buildbot import *
from sqlalchemy.sql import func

# 连接mysql数据库。
engine = create_engine("mysql+pymysql://root:jkljkl147@localhost:3306/sql_buildbot_config",encoding="utf-8")
DBSession = sessionmaker(bind=engine)

# basedir是master运行的目录。buildbotURL是buildbot的网页地址。
basedir = 'D:\\buildbot-test\\master\\master'
buildbotURL = "http://laptop-3agq5vtq:8010"


MyMenu = Flask('menu', root_path=os.path.dirname(__file__))
mybuildapp = Flask('build', root_path=os.path.dirname(__file__))

# this allows to work on the template without having to restart Buildbot.
MyMenu.config['SECRET_KEY'] = 'dev'
MyMenu.config['TEMPLATES_AUTO_RELOAD'] = True
mybuildapp.config['TEMPLATES_AUTO_RELOAD'] = True

# Operation menu interface.
@MyMenu.route("/index.html", methods=['GET','POST'])
def main():
    if request.method == 'GET':
        req = request
        return render_template('menu.html', req=req)


# Search for the specified build.
@MyMenu.route("/index.html/search", methods=['GET','POST'])
def buildsearch():
    if request.method == 'GET':
        req = request
        addr = url_for('main')
        reqUrl = request.url
        buildPOST = MyMenu.buildbot_api.dataGet("/builders/2/builds/40")
        master1 = MyMenu.buildbot_api.dataGet("/masters/1")

        return render_template('searchBuildPage.html', addr=addr, req=req, buildPOST=buildPOST,
        master1=master1)

    if request.method == 'POST':
    # Get master, builder, build information collection.
        reqUrl = request.url
        masters = MyMenu.buildbot_api.dataGet("/masters")
        builders = MyMenu.buildbot_api.dataGet("/builders")
        builds = MyMenu.buildbot_api.dataGet("/builds", limit=1000)

    # Get input data from the form.
        buildername = request.form.get('buildername')
        buildnumber = request.form.get('buildid')
    # Determine whether the input data exists and find the corresponding builderid.
        ExistBuilder = 0
        ExistBuild = 0
        for builder in builders:
            if builder['name'] == buildername:
                builderid = builder['builderid']
                ExistBuilder = 1
                break

        if ExistBuilder == 0:
            flash('该建构器名字不存在！')
            return redirect(reqUrl)

        for build in builds:
            if build['number'] == int(buildnumber) and build['builderid'] == int(builderid):
                builderid = build['builderid']
                ExistBuild = 1
                break
        if ExistBuild == 0:
            flash('该构建编号在构建器中不存在！')
            return redirect(reqUrl)

        return redirect('http://laptop-3agq5vtq:8010/#'+'/builders/'+str(builderid)+'/builds/'+str(buildnumber))


# Create a builder。
@MyMenu.route("/index.html/createbuilder", methods=['GET','POST'])
def buildercreate():
    if request.method == 'GET':
        req = request
        # reqUrl = request.url
        changesources = MyMenu.buildbot_api.dataGet("/masters/1/changesources")
        schedulers = MyMenu.buildbot_api.dataGet("/schedulers")
        workers = MyMenu.buildbot_api.dataGet("/workers")
        return render_template('createBuilderPage.html', changesources=changesources, schedulers=schedulers,
                               workers=workers,buildbotURL=buildbotURL)

    if request.method == 'POST':

        reqUrl = request.url

        name = request.form.get('buildername')
        workersList = request.form.get('workername').split(',')
        repourl = request.form.get('source')
        shellcommand = request.form.get('command')
        schedulersList = request.form.get('schedulers')
        priority = request.form.get('priority')

        print(name, workersList, repourl, shellcommand, schedulersList,priority,type(priority))

        builders = MyMenu.buildbot_api.dataGet("/builders")
        for builder in builders:
            if builder['name'] == name:
                flash('该建构器名字已经存在，请重新输入！')
                return redirect(reqUrl)

        workers = MyMenu.buildbot_api.dataGet("/workers")
        exist_workerList = []
        for worker in workers:
            exist_workerList.append(worker['name'])
        for curworker in workersList:
            if curworker not in exist_workerList:
                flash('输入存在unknown worker，请先新建worker')
                return redirect(reqUrl)

        session = DBSession()
        item_builder = Builders(builder_name=name)

        workers = session.query(Workers).filter(Workers.worker_name.in_(workersList)).all()
        item_builder.workers = workers

        if len(schedulersList) != 0:
            schedulersList = schedulersList.split(',')
            schedulers = session.query(Schedulers).filter(Schedulers.scheduler_name.in_(schedulersList)).all()
            item_builder.schedulers = schedulers


        session.add(item_builder)

        if priority == 'Default':
            item_priority = PrioritizeBuilders(builder_name=name)
            session.add(item_priority)
        else:
            pr = session.query(func.min(PrioritizeBuilders.priority_num)).scalar()
            item_priority = PrioritizeBuilders(builder_name=name,priority_num=pr-1)
            session.add(item_priority)

        if len(repourl) != 0:
            item_f = Factory(builder_name=name, repourl=repourl)
            session.add(item_f)
            if len(shellcommand) !=0 :
                shellcommand = shellcommand.split(',')
                for i in range(len(shellcommand)):
                    shellcommand[i] = shellcommand[i].replace(' ', ',')
                idf = session.query(Factory).filter_by(builder_name=name).first().id
                for i in range(len(shellcommand)):
                    item = Command(idf, shellcommand[i])
                    session.add(item)

        session.commit()
        session.close()

        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)

# delete a builder。
@MyMenu.route("/index.html/deletebuilder", methods=['GET','POST'])
def builderdelete():
    if request.method == 'GET':

        return render_template('deleteBuilderPage.html')

    if request.method == 'POST':

        buildername = request.form.get('buildername')

        session = DBSession()
        ber = session.query(Builders).filter_by(builder_name=buildername).first()
        session.delete(ber)

        session.commit()
        session.close()

        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)

# Find a builder。
@MyMenu.route("/index.html/readbuilder", methods=['GET','POST'])
def builderread():
    if request.method == 'GET':
        session = DBSession()
        builders = session.query(Builders).all()
        builersData = []
        for i in range(len(builders)):
            name = builders[i].builder_name


            cur_builder = builders[i]
            workerNames = list(worker.worker_name for worker in cur_builder.workers)
            workerNames = ','.join(workerNames)

            schedulerNames = list(scheduler.scheduler_name for scheduler in cur_builder.schedulers)
            schedulerNames = ','.join(schedulerNames)

            repourl = builders[i].factory[0].repourl

            comds = builders[i].factory[0].commands
            comdsList = list(comd.command for comd in comds)
            command = '&'.join(comdsList)


            num = builders[i].priority[0].priority_num

            cur = [name, workerNames, repourl, command, num, schedulerNames]

            builersData.append(cur)

        session.close()
        return render_template('readBuilderPage.html',buildersData=builersData )

# Update a builder。

@MyMenu.route("/index.html/updatebuilder", methods=['GET','POST'])
def builderupdate():
    if request.method == 'GET':
        session = DBSession()
        builders = session.query(Builders).all()
        running_builderNames = list(builder.builder_name for builder in builders)

        session.close()



        return render_template('updateBuilderPage.html', running_builderNames=running_builderNames)

    if request.method == 'POST':

        reqUrl = request.url

        name = request.form.get('buildername')
        workersList = request.form.get('workername')
        repourl = request.form.get('source')
        shellcommand = request.form.get('command')
        schedulersList = request.form.get('schedulers')
        priority = request.form.get('priority')

        print(name, workersList, repourl, shellcommand, schedulersList,priority,type(priority))

        if name == None:
            flash('请指定builder！')
            return redirect(reqUrl)
        elif len(workersList+repourl+shellcommand+schedulersList+priority) == 0:
            flash('没有提交任何变动！')
            return redirect(reqUrl)

        session = DBSession()

        builder = session.query(Builders).filter_by(builder_name=name).first()


        if len(workersList) != 0:
            workersList = workersList.split(',')

            workers = MyMenu.buildbot_api.dataGet("/workers")
            exist_workerList = []
            for worker in workers:
                exist_workerList.append(worker['name'])
            for curworker in workersList:
                if curworker not in exist_workerList:
                    print(curworker,exist_workerList)
                    flash('输入存在unknown worker，请先新建worker')
                    return redirect(reqUrl)

            workers = session.query(Workers).filter(Workers.worker_name.in_(workersList)).all()
            builder.workers = workers



        if len(schedulersList) != 0:
            schedulersList = schedulersList.split(',')
            schedulers = session.query(Schedulers).filter(Schedulers.scheduler_name.in_(schedulersList)).all()
            builder.schedulers = schedulers




        if len(priority) != 0:
            priority = int(priority)
            session.query(PrioritizeBuilders).filter(PrioritizeBuilders.builder_name == name).update(
                {PrioritizeBuilders.priority_num:priority})


        if len(repourl) != 0:
            session.query(Factory).filter(Factory.builder_name == name).update(
                {Factory.repourl:repourl})


        if len(shellcommand) !=0 :
            shellcommand = shellcommand.split(',')
            for i in range(len(shellcommand)):
                shellcommand[i] = shellcommand[i].replace(' ', ',')
            idf = session.query(Factory).filter_by(builder_name=name).first().id
            ToDelcommand = session.query(Command).filter_by(factory_id=idf).all()
            for ToDel in ToDelcommand:
                session.delete(ToDel)
            for i in range(len(shellcommand)):
                item = Command(idf, shellcommand[i])
                session.add(item)


        session.commit()
        session.close()

        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)

# Create a worker
@MyMenu.route("/index.html/createworker", methods=['GET','POST'])
def workercreate():
    if request.method == 'GET':
        req = request
        # reqUrl = request.url
        changesources = MyMenu.buildbot_api.dataGet("/masters/1/changesources")
        schedulers = MyMenu.buildbot_api.dataGet("/schedulers")
        workers = MyMenu.buildbot_api.dataGet("/workers")
        return render_template('createWorkerPage.html', changesources=changesources, schedulers=schedulers,
                               workers=workers,buildbotURL=buildbotURL)

    if request.method == 'POST':
        reqUrl = request.url
        workername = request.form.get('workername')
        workerpw = request.form.get('workerpw')

        workers = MyMenu.buildbot_api.dataGet("/workers")
        for worker in workers:
            if worker['name'] == workername:
                flash('该工人名字已经存在！')
                return redirect(reqUrl)
        if len(workerpw) < 3:
            flash('要求密码长度不小于3！')
            return redirect(reqUrl)

        session = DBSession()
        item = Workers(worker_name = workername, password = workerpw)
        session.add(item)
        session.commit()
        session.close()

        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)

# Update for title and titleURL of Buildbot
@MyMenu.route("/index.html/updatetitle", methods=['GET','POST'])
def titleupdate():
    if request.method == 'GET':

        return render_template('updateTitlePage.html')

    if request.method == 'POST':
        newtitle = request.form.get('title')
        newtitleURL = request.form.get('titleURL')

        if len(newtitle) == 0 and len(newtitleURL) == 0:
            return redirect(buildbotURL)
        if len(newtitle) != 0:
            session = DBSession()
            session.query(GlobalConfig).filter(GlobalConfig.name == 'title').update({GlobalConfig.value:newtitle})
            session.commit()
            session.close()
        if len(newtitleURL) != 0:
            session = DBSession()
            session.query(GlobalConfig).filter(GlobalConfig.name == 'titleURL').update({GlobalConfig.value:newtitleURL})
            session.commit()
            session.close()


        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)

# Add a change source
@MyMenu.route("/index.html/CreateChangeSource", methods=['GET','POST'])
def ChangeSourceCreate():
    if request.method == 'GET':

        return render_template('createChangeSourcePage.html')

    if request.method == 'POST':
        repourl = request.form.get('repourl')
        branches = request.form.get('branches')
        #输入多个branch应该用，隔开。如：branchA,branchB

        pollInterval = int(request.form.get('pollInterval'))
        session = DBSession()
        item = ChangeSource(repourl, branches, poll_interval=pollInterval)
        session.add(item)
        session.commit()
        session.close()

        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)

# Add a scheduler
@MyMenu.route("/index.html/CreateScheduler", methods=['GET','POST'])
def SchedulerCreate():
    if request.method == 'GET':
        return render_template('createSchedulerPage.html')

    if request.method == 'POST':
        reqUrl = request.url
        scheduler_name = request.form.get('name')
        builder_names = request.form.get('buildernames')


        session = DBSession()

        if request.form.get('submit') == 'CreateSingleBranch':
            scheduler_type = 'SingleBranchScheduler'
            item1 = Schedulers(scheduler_type=scheduler_type, scheduler_name=scheduler_name)
            branch = request.form.get('branch')
            treeStableTimer = int(request.form.get('treeStableTimer'))
            item2 = SingleBranch(branch=branch, tree_stable_time=treeStableTimer, scheduler_name=scheduler_name)


        elif request.form.get('submit') == 'CreatePeriodic':
            scheduler_type = 'Periodic'
            item1 = Schedulers(scheduler_type=scheduler_type, scheduler_name=scheduler_name)
            periodicBuildTimer = int(request.form.get('periodicBuildTimer'))
            item2 = Periodic(scheduler_name=scheduler_name, periodic_build_timer=periodicBuildTimer)


        elif request.form.get('submit') == 'CreateForce':
            scheduler_type = 'ForceScheduler'
            item1 = Schedulers(scheduler_type=scheduler_type, scheduler_name=scheduler_name)
            item2 = Force(scheduler_name=scheduler_name)

        else:
            flash('所需调度器类型不存在。')
            return redirect(reqUrl)

        # sheduler can be created without buildernames

        if len(builder_names) == 0:
            session.add(item1)
            session.add(item2)
        else:
            builders = session.query(Builders).all()
            running_builderNames = list(builder.builder_name for builder in builders)
            builder_names = builder_names.split(',')
            for builder in builder_names:
                if builder not in running_builderNames:
                    flash('builder中存在未被配置的对象。')
            sche_to_builders = session.query(Builders).filter(Builders.builder_name.in_(builder_names)).all()
            item1.builders = sche_to_builders
            session.add(item1)
            session.add(item2)

        session.commit()
        session.close()

        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)

# Update for BuilderPriority
@MyMenu.route("/index.html/BuilderPriority", methods=['GET','POST'])
def BuilderPriority():
    if request.method == 'GET':
        # builders = MyMenu.buildbot_api.dataGet("/builders")
        session = DBSession()
        builders = session.query(Builders).all()
        buildersList = []
        for i in range(len(builders)):
            buildersList.append(builders[i].builder_name)

        session.close()

        return render_template('setBuilderPriorityPage.html',builders=buildersList)

    if request.method == 'POST':

        session = DBSession()
        builders = session.query(Builders).all()

        for i in range(len(builders)):
            buildername = builders[i].builder_name
            num = request.form.get(buildername)
            if len(num)!=0:
                num = int(num)
                session.query(PrioritizeBuilders).filter(PrioritizeBuilders.builder_name == buildername).update(
                    {PrioritizeBuilders.priority_num:num})
        session.commit()
        session.close()

        signal.raise_signal(signal.SIGINT)
        time.sleep(2)
        return redirect(buildbotURL)
# To show BuilderList
@mybuildapp.route("/index.html", methods=['GET','POST'])
def buildmain():
        masters = mybuildapp.buildbot_api.dataGet("/masters")
        builders = mybuildapp.buildbot_api.dataGet("/builders")
        builds = mybuildapp.buildbot_api.dataGet("/builds", limit=1000)

        return render_template('myBuilderList.html', builders=builders, builds=builds,masters=masters,)