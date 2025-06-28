# 背景
在日常工作过程中，我经常会打开sublime text当做我的草稿本。比如处理文本、对比内容、进行正则替换等操作。
这些临时文本内容往往只是中间过程或者短期使用，所以我希望sublime可以自动帮我关闭这些窗口，但需要的时候也可以查看之前处理过的内容
传统的做法是手动关闭这些临时untitled的文件，然后确定每个可以关闭之后点击close。
我的标签页逐渐越来越多，或者直接关闭后找不到之前的内容。
为了解决这个痛点，我vibe coding了这个Sublime Text自动存档插件。

# 功能
1、未保存的新文件2小时后自动关闭，关闭的时候不弹框、不影响当前的焦点
2、存档按照天分类保存到~/Documents/sublime_drafts/YYYY-MM-DD/目录
3、可以查看存档，恢复内容，每月1号删除30天前的存档
4、在菜单栏、命令面板和右键菜单都集成进去

# 安装

* 文件下载地址：
https://github.com/pinkomeo/auto_archive_tabs

* 把4个文件放在这个目录下面，然后重启sublime：
/Users/[你的用户名]/Library/Application Support/Sublime Text/Packages/User/

* 可以修改的部分：
1、12行self.timeout是多久没使用的tab就关闭的意思，这里7200代表两个小时。
2、414行的set_timeout里面的60000，代表60秒检查一次。

# 截图
* 右键菜单
![p0](https://github.com/user-attachments/assets/59430eb8-c209-48ef-9b6c-1006e5520678)

* 假设你新建了一个临时的
![p1](https://github.com/user-attachments/assets/000ee709-8e6d-4da5-9016-4581749553e5)

* 查看每一天的情况
![p2](https://github.com/user-attachments/assets/892ee694-9305-4181-9c87-8f66923004f2)

*查看某一天的文件有哪些
![p3](https://github.com/user-attachments/assets/ba61dac1-d0c4-4f0f-8723-64be0fb9c598)

* 点击那个文件恢复之后
![p4](https://github.com/user-attachments/assets/f06a3171-0d7e-4294-822e-718fc99ea8be)

* 文件夹里面的结构
![p5](https://github.com/user-attachments/assets/82091647-f541-4810-a641-4aa37babf85f)





