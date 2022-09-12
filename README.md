# Buildmaster for Buildbot
This is a buildmaster project.

# Install
Python version: 3.8.10  
Buildbot version: 3.5.0  
Twisted version: 22.4.0 

# Usage
This project is used to build a buildmaster.  
The most important file is master.cfg.
It contains all configuration information about buildmaster.

master.cfg: It loads the master configuration by reading configuration information from the database. 

myWebUI: Use the flask framework for web development. The html files are contained in the templates folder.

sql_buildbot.py: It contains the designed table object.

# Web UI
<img src="https://github.com/ChungChyi/Buildbot_web_config/blob/main/img_web_config/op_menu.jpg" width="200"  alt="操作菜单"/><br/>
<img src="https://github.com/ChungChyi/Buildbot_web_config/blob/main/img_web_config/create_builder.jpg" width="200"  alt="创建Builder页面"/><br/>

![images](img_web_config/op_menu.jpg)

![images](img_web_config/create_builder.jpg)
