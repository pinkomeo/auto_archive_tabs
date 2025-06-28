import sublime
import sublime_plugin
import time
import os
import json
import shutil
from datetime import datetime, timedelta

class AutoArchiveTabsCommand(sublime_plugin.EventListener):
    def __init__(self):
        self.tab_times = {}
        self.timeout = 7200  # 30秒用于测试，正式使用改为 7200 (2小时)
        self.archive_dir = self.get_documents_archive_dir()
        self.ensure_archive_dir()
        self.cleanup_old_archives()
        
    def get_documents_archive_dir(self):
        """获取文稿目录下的 sublime_drafts 路径"""
        if os.name == 'nt':  # Windows
            documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        else:  # macOS/Linux
            documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        
        return os.path.join(documents_dir, 'sublime_drafts')
        
    def ensure_archive_dir(self):
        """确保存档目录存在"""
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
            print(f"Created archive directory: {self.archive_dir}")
    
    def cleanup_old_archives(self):
        """每月1号删除30天前的存档"""
        try:
            now = datetime.now()
            if now.day == 1:
                cutoff_date = now - timedelta(days=30)
                deleted_count = 0
                
                for item in os.listdir(self.archive_dir):
                    item_path = os.path.join(self.archive_dir, item)
                    if os.path.isdir(item_path) and len(item) == 10 and item.count('-') == 2:
                        try:
                            folder_date = datetime.strptime(item, '%Y-%m-%d')
                            if folder_date < cutoff_date:
                                shutil.rmtree(item_path)
                                deleted_count += 1
                                print(f"Deleted old archive folder: {item}")
                        except ValueError:
                            continue
                
                if deleted_count > 0:
                    sublime.status_message(f"Cleaned up {deleted_count} old archive folders")
        except Exception as e:
            print(f"Archive cleanup error: {e}")
    
    def is_temporary_tab(self, view):
        """判断是否是临时标签页（未保存的新文件）"""
        
        # 1. 如果有文件路径且文件存在，说明是已保存的文件 - 不处理
        if view.file_name() and os.path.exists(view.file_name()):
            return False
        
        # 2. 如果没有内容，跳过
        if view.size() == 0:
            return False
        
        # 3. 如果是 Sublime Text 的配置文件 - 不处理
        file_name = view.file_name() or view.name() or ""
        config_extensions = ['.sublime-settings', '.sublime-keymap', '.sublime-menu', 
                            '.sublime-commands', '.sublime-build', '.sublime-project',
                            '.sublime-workspace', '.sublime-theme', '.sublime-color-scheme']
        
        if any(file_name.endswith(ext) for ext in config_extensions):
            return False
        
        # 4. 如果文件名包含 Sublime Text 相关关键词 - 不处理
        sublime_keywords = ['sublime', 'package', 'preferences', 'settings', 'keymap', 'default']
        file_name_lower = file_name.lower()
        if any(keyword in file_name_lower for keyword in sublime_keywords):
            return False
        
        # 5. 如果是在 Packages 目录下的文件 - 不处理
        if view.file_name():
            packages_path = sublime.packages_path()
            if view.file_name().startswith(packages_path):
                return False
        
        # 6. 如果是项目文件（在工作区中）- 不处理
        if view.window() and view.window().project_data():
            project_folders = view.window().folders()
            if project_folders and view.file_name():
                for folder in project_folders:
                    if view.file_name().startswith(folder):
                        return False
        
        # 7. 如果文件已经保存过（即使现在有修改）- 不处理
        if view.file_name() and not 'untitled' in view.file_name().lower():
            return False
        
        # 8. 只有真正的临时文件才返回 True
        if not view.file_name() or 'untitled' in view.file_name().lower():
            return view.is_dirty()  # 只有有内容修改的才处理
        
        return False
    
    def on_activated(self, view):
        """记录标签页最后活跃时间"""
        if self.is_temporary_tab(view):
            self.tab_times[view.id()] = time.time()
            print(f"Tracking temporary tab: {view.name() or 'Untitled'}")
        
    def on_close(self, view):
        """清理已关闭标签的记录"""
        if view.id() in self.tab_times:
            del self.tab_times[view.id()]
    
    def on_modified(self, view):
        """文件被修改时更新活跃时间"""
        if self.is_temporary_tab(view):
            self.tab_times[view.id()] = time.time()
    
    def get_today_archive_dir(self):
        """获取今天的存档目录"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_dir = os.path.join(self.archive_dir, today)
        if not os.path.exists(today_dir):
            os.makedirs(today_dir)
            print(f"Created today's archive directory: {today_dir}")
        return today_dir
    
    def archive_content(self, view):
        """将内容保存到今天的存档目录"""
        content = view.substr(sublime.Region(0, view.size()))
        if not content.strip():  # 跳过空内容
            return None
            
        # 生成文件信息
        file_name = view.file_name() or view.name() or "Untitled"
        timestamp = datetime.now().strftime("%H-%M-%S")
        
        # 创建存档记录
        archive_record = {
            "original_file": file_name,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": len(content),
            "lines": content.count('\n') + 1,
            "syntax": view.settings().get('syntax', 'Plain Text'),
            "encoding": view.encoding()
        }
        
        # 保存到今天的存档目录
        today_dir = self.get_today_archive_dir()
        base_name = os.path.basename(file_name).replace('/', '_').replace('\\', '_')
        if not base_name or base_name == 'Untitled':
            base_name = "draft"
        
        archive_file = os.path.join(today_dir, f"{timestamp}_{base_name}.json")
        
        # 如果文件名重复，添加序号
        counter = 1
        original_archive_file = archive_file
        while os.path.exists(archive_file):
            name, ext = os.path.splitext(original_archive_file)
            archive_file = f"{name}_{counter}{ext}"
            counter += 1
        
        try:
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(archive_record, f, ensure_ascii=False, indent=2)
            print(f"Archived to: {archive_file}")
            return archive_file
        except Exception as e:
            print(f"Archive save error: {e}")
            return None
    
    def check_and_close_tabs(self):
        """检查并关闭长时间未使用的临时标签"""
        current_time = time.time()
        closed_count = 0
        
        print(f"Checking tabs... Currently tracking {len(self.tab_times)} temporary tabs")
        
        for window in sublime.windows():
            # 记住当前活跃的标签页
            current_active_view = window.active_view()
            views_to_close = []
            
            for view in window.views():
                if view.id() in self.tab_times:
                    inactive_time = current_time - self.tab_times[view.id()]
                    
                    print(f"Tab '{view.name() or 'Untitled'}' inactive for {inactive_time:.1f} seconds")
                    
                    if inactive_time > self.timeout:
                        # 确保仍然是临时标签
                        if self.is_temporary_tab(view):
                            views_to_close.append(view)
                            print(f"Will close tab: {view.name() or 'Untitled'}")
            
            # 关闭标签页
            for view in views_to_close:
                try:
                    # 先存档内容
                    archive_file = self.archive_content(view)
                    
                    # 清除修改标记，避免弹出保存对话框
                    if view.is_dirty():
                        view.set_scratch(True)
                    
                    # 静默关闭标签页，不改变焦点
                    view_index = window.get_view_index(view)
                    if view_index[0] != -1:
                        window.run_command("close_by_index", {"group": view_index[0], "index": view_index[1]})
                    else:
                        view.close()
                    
                    closed_count += 1
                    
                    if archive_file:
                        print(f"Tab archived and closed: {os.path.basename(archive_file)}")
                        
                except Exception as e:
                    print(f"Close tab error: {e}")
            
            # 如果当前活跃的标签页没有被关闭，恢复焦点
            if current_active_view and current_active_view not in views_to_close:
                try:
                    window.focus_view(current_active_view)
                except:
                    pass
        
        if closed_count > 0:
            sublime.status_message(f"Auto-closed {closed_count} temporary tabs")

class ShowTabArchiveCommand(sublime_plugin.WindowCommand):
    """显示存档的标签页"""
    
    def run(self):
        archive_dir = self.get_documents_archive_dir()
        
        if not os.path.exists(archive_dir):
            sublime.message_dialog("No archived tabs found.\nArchive directory: " + archive_dir)
            return
        
        # 获取所有日期目录
        date_dirs = []
        
        for item in os.listdir(archive_dir):
            item_path = os.path.join(archive_dir, item)
            if os.path.isdir(item_path) and len(item) == 10 and item.count('-') == 2:
                try:
                    date_obj = datetime.strptime(item, '%Y-%m-%d')
                    date_dirs.append((item, date_obj))
                except ValueError:
                    continue
        
        if not date_dirs:
            sublime.message_dialog("No archived tabs found.")
            return
        
        # 按日期排序（最新的在前）
        date_dirs.sort(key=lambda x: x[1], reverse=True)
        
        # 创建日期选择列表
        date_items = []
        for date_str, date_obj in date_dirs:
            formatted_date = date_obj.strftime("%Y-%m-%d (%A)")
            
            # 统计当天的存档数量
            day_dir = os.path.join(archive_dir, date_str)
            archive_count = len([f for f in os.listdir(day_dir) if f.endswith('.json')])
            
            date_items.append([
                formatted_date,
                f"{archive_count} archived tabs"
            ])
        
        def on_select_date(index):
            if index >= 0:
                selected_date = date_dirs[index][0]
                self.show_day_archives(selected_date)
        
        self.window.show_quick_panel(date_items, on_select_date)
    
    def get_documents_archive_dir(self):
        """获取文稿目录下的 sublime_drafts 路径"""
        if os.name == 'nt':  # Windows
            documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        else:  # macOS/Linux
            documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        
        return os.path.join(documents_dir, 'sublime_drafts')
    
    def show_day_archives(self, date_str):
        """显示某一天的存档"""
        archive_dir = self.get_documents_archive_dir()
        day_dir = os.path.join(archive_dir, date_str)
        
        # 读取当天所有存档文件
        archives = []
        for filename in os.listdir(day_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(day_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                        record['archive_file'] = filepath
                        record['filename'] = filename
                        archives.append(record)
                except Exception as e:
                    print(f"Read archive error: {e}")
                    continue
        
        if not archives:
            sublime.message_dialog("No archives found for this date.")
            return
        
        # 按时间排序（最新的在前）
        archives.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 创建选择列表
        items = []
        for record in archives:
            original_name = os.path.basename(record['original_file'])
            timestamp = record['timestamp'].split(' ')[1]  # 只显示时间部分
            size = record['size']
            lines = record.get('lines', 'Unknown')
            preview = record['content'][:60].replace('\n', ' ').replace('\r', '')
            
            items.append([
                f"{timestamp} - {original_name}",
                f"Size: {size} chars | Lines: {lines}",
                f"Preview: {preview}..." if len(record['content']) > 60 else f"Preview: {preview}"
            ])
        
        def on_select(index):
            if index >= 0:
                self.restore_archive(archives[index])
        
        self.window.show_quick_panel(items, on_select)
    
    def restore_archive(self, record):
        """恢复存档的内容"""
        try:
            view = self.window.new_file()
            view.run_command("insert", {"characters": record['content']})
            
            # 设置语法高亮
            if 'syntax' in record and record['syntax'] != 'Plain Text':
                view.set_syntax_file(record['syntax'])
            
            # 设置编码
            if 'encoding' in record and record['encoding']:
                view.set_encoding(record['encoding'])
            
            # 设置文件名
            original_name = os.path.basename(record['original_file'])
            timestamp = record['timestamp'].split(' ')[1].replace(':', '-')  # 时间部分
            view.set_name(f"Restored_{timestamp}_{original_name}")
            
            sublime.status_message(f"Restored: {original_name}")
        except Exception as e:
            sublime.error_message(f"Failed to restore archive: {e}")

class ClearTabArchiveCommand(sublime_plugin.WindowCommand):
    """清理存档"""
    
    def run(self):
        archive_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'sublime_drafts')
        
        if not os.path.exists(archive_dir):
            sublime.message_dialog("No archives to clear.")
            return
        
        # 询问确认
        if sublime.ok_cancel_dialog(f"Clear all archived tabs in:\n{archive_dir}\n\nThis cannot be undone."):
            try:
                shutil.rmtree(archive_dir)
                sublime.status_message("All tab archives cleared")
            except Exception as e:
                sublime.error_message(f"Failed to clear archives: {e}")

class OpenArchiveFolderCommand(sublime_plugin.WindowCommand):
    """在文件管理器中打开存档文件夹"""
    
    def run(self):
        archive_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'sublime_drafts')
        
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        # 根据操作系统打开文件夹
        if os.name == 'nt':  # Windows
            os.startfile(archive_dir)
        elif os.name == 'posix':  # macOS/Linux
            if sublime.platform() == 'osx':  # macOS
                os.system(f'open "{archive_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{archive_dir}"')

# 定时检查器
def plugin_loaded():
    def check_tabs():
        try:
            for listener in sublime_plugin.all_callbacks.get('on_activated', []):
                if isinstance(listener, AutoArchiveTabsCommand):
                    listener.check_and_close_tabs()
        except Exception as e:
            print(f"Check tabs error: {e}")
        
        # 每30秒检查一次（测试时），正式使用可以改为每分钟
        sublime.set_timeout(check_tabs, 60000)  # 30秒，正式使用改为 60000
    
    # 延迟启动，确保插件完全加载
    sublime.set_timeout(check_tabs, 5000)
    
    # 显示插件加载信息
    archive_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'sublime_drafts')
    print(f"Auto Archive Tabs plugin loaded. Archive directory: {archive_dir}")

def plugin_unloaded():
    """插件卸载时的清理"""
    print("Auto Archive Tabs plugin unloaded")
