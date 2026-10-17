import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply_new

RM, FD = "sec-recentmanager", "sec-filechooser-filedialog"

INPAGE = [
    dict(id="rd22-rm-1", page=RM, pos=0,
         stem="下面这样登记一个最近使用的文件，最少需要提供什么信息？",
         code="""
auto recent_manager = Gtk::RecentManager::get_default();
recent_manager->add_item(uri);""",
         right="只要一个 URI，元数据是可选的",
         wrong=["必须再提供一个 RecentManager::Data，否则登记失败",
                "文件路径和 MIME 类型，二者缺一不可，才能登记成功",
                "应用程序名和启动命令行，用来在列表里显示这个文件"],
         why="最简单的情况下，向最近文档列表添加文件只需要提供 URI。要登记元数据（app_name、display_name、mime_type、groups、is_private 等）时，才向 add_item() 传一个 RecentManager::Data 参数。",
         ref="RecentManager：最简单的 add_item(uri)；带元数据时传 RecentManager::Data"),
    dict(id="rd22-rm-2", page=RM, pos=2,
         stem="get_default() 得到的 RecentManager，它背后的最近使用文件列表属于谁？",
         code="""
auto recent_manager = Gtk::RecentManager::get_default();""",
         right="每个用户一份，不是每个程序一份",
         wrong=["每个应用程序各一份，互相看不到对方登记的文件",
                "每个窗口各一份，窗口关闭时随之清空",
                "整台机器共用一份，所有用户都能读写同一个列表"],
         why="RecentManager 相当于最近使用文件的数据库：每个用户只有一份最近使用文件列表。可以新建一个 RecentManager，但多数情况下直接用 get_default() 得到的默认实例即可。因此别的程序登记的文件，在这个用户的所有程序里都能看到。",
         ref="RecentManager：每个用户一份最近使用文件列表，通常用 get_default() 的默认实例"),
    dict(id="rd22-rm-3", page=RM, pos=3,
         stem="URI 不在最近使用文件列表里时，lookup_item() 会怎样？",
         code="""
Glib::RefPtr<Gtk::RecentInfo> info;
try
{
  info = recent_manager->lookup_item(uri);
}
catch(const Gtk::RecentManagerError& ex)
{
  std::cerr << "RecentManagerError: " << ex.what() << std::endl;
}
if (info)
{
  // item was found
}""",
         right="抛出 RecentManagerError，info 保持为空",
         wrong=["返回空的 RefPtr，不抛异常，所以不需要 try/catch",
                "返回一个内容为空的 RecentInfo，要再检查它的各个字段",
                "自动把这个 URI 登记进列表，然后返回新建的 RecentInfo"],
         why="按 URI 查找指定项用 lookup_item()，成功时返回 RecentInfo。如果指定的 URI 不在列表里，lookup_item() 会抛出 RecentManagerError 异常，所以示例用 try/catch 包住它，并在之后用 if (info) 判断是否找到。",
         ref="RecentManager：lookup_item() 找不到时抛出 RecentManagerError"),
    dict(id="rd22-rm-4", page=RM, pos=1,
         stem="一个最近使用的文件，默认最长会在列表里保留多久？",
         right="30 天，由 gtk-recent-files-max-age 设置控制",
         wrong=["7 天，且每次打开文件时重新计时",
                "永久保留，必须调用 purge_items() 才会清掉",
                "到程序退出为止，下次启动时列表自动清空"],
         why="最近使用文件列表中各项的最大年龄可以用 Gtk::Settings::property_gtk_recent_files_max_age() 设置，默认值是 30 天。要清掉列表要用 remove_item()（一个一个删）或 purge_items()（一次清空）。",
         ref="RecentManager：最大年龄由 property_gtk_recent_files_max_age() 设置，默认 30 天"),
    dict(id="rd22-fd-1", page=FD, pos=3,
         stem="FileChooserDialog、FileChooserWidget 这一系列类，在本章里是什么状态？",
         right="自 gtkmm 4.10 起已弃用，由 FileDialog 取代",
         wrong=["仍是推荐写法，FileDialog 只是它们的一个别名",
                "只有 FileChooserWidget 弃用了，FileChooserDialog 照常使用",
                "已在 gtkmm 4.0 里删除，用到它们的代码都无法编译"],
         why="FileChooser 是一个接口，由显示文件列表的部件实现（FileChooserWidget、FileChooserDialog、FileChooserNative）。它和实现它的类自 gtkmm 4.10 起已弃用，已被同样自 4.10 起可用的 FileDialog 取代；没有定义 GTKMM_DISABLE_DEPRECATED 时仍可使用。",
         ref="FileChooser 与 FileDialog：FileChooser 及其实现类自 4.10 弃用，由 FileDialog 取代"),
    dict(id="rd22-fd-2", page=FD, pos=0,
         stem="下面两行分别是按什么条件过滤文件？",
         code="""
filter->add_pattern("*.txt");
filter->add_mime_type("image/png");""",
         right="第一行按文件名模式，第二行按 MIME 类型",
         wrong=["第一行按 MIME 类型，第二行按文件名模式",
                "两行都按文件扩展名，只是写法不同而已",
                "第一行按文件大小，第二行按最近使用的时间"],
         why="FileFilter 可以按文件名过滤（add_pattern()）或按 MIME 类型过滤（add_mime_type()）。设置好过滤器之后，对旧的 FileChooser 系列要用 FileChooser::add_filter() 把过滤器应用到选择器部件上。",
         ref="FileChooser 与 FileDialog：FileFilter 按名称 add_pattern() 或 MIME 类型 add_mime_type() 过滤"),
    dict(id="rd22-fd-3", page=FD, pos=2,
         stem="第一次运行使用最近文件框架的程序，在文件对话框里选中侧边栏的“Recent”，列表是空的，最可能的原因是？",
         right="还没有任何程序登记过最近使用的文件",
         wrong=["对话框损坏了，必须先调用 purge_items() 才能恢复",
                "FileDialog 不支持最近使用文件，必须改用 RecentManager",
                "侧边栏的 Recent 只显示本程序登记的文件，别的程序不算"],
         why="如果这是你第一次使用最近文件框架，对话框可能一开始是空的；否则它应该显示其他程序登记的最近使用文件列表（列表是每个用户一份，而不是每个程序一份）。",
         ref="FileChooser 与 FileDialog 示例：第一次使用时列表可能为空，否则显示其他程序登记的文件"),
]

CHECKPOINT = [
    dict(id="rd22-cp-1", pos=1, locator="官方节页 sec-recentmanager",
         stem="执行下面三个调用，对磁盘上的实际文件有什么影响？",
         code="""
recent_manager->move_item(old_uri, new_uri);
recent_manager->remove_item(uri);
recent_manager->purge_items();""",
         right="没有影响，它们只修改最近使用文件列表",
         wrong=["move_item() 会把磁盘上的文件移到 new_uri 去",
                "remove_item() 与 purge_items() 会同时删掉磁盘上的文件",
                "三个调用都会改动文件，purge_items() 还会清空文件内容"],
         why="move_item()、remove_item() 和 purge_items() 对 URI 指向的实际文件没有任何影响，只修改最近使用文件列表：move_item() 更新项的位置，remove_item() 一次删一项，purge_items() 一次清空整个列表。",
         ref="综合 RecentManager：move_item、remove_item、purge_items 只改列表不改文件"),
    dict(id="rd22-cp-2", pos=0, locator="官方节页 sec-recentmanager",
         stem="要列出所有最近使用的文件，下面这行的返回值是什么？",
         code="""
auto info_list = recent_manager->get_items();""",
         right="一个 std::vector，装着所有最近使用文件的 RecentInfo",
         wrong=["一个 Glib::ustring，是用换行连起来的所有 URI",
                "单个 RecentInfo，里面保存着最近使用的那一个文件",
                "一个 RecentManager::Data，描述整个列表的元数据"],
         why="想获取全部最近使用的项目而不是按 URI 查某一个时，用 get_items()，它的返回值是包含所有最近使用文件的 std::vector；其中每一项是一个 RecentInfo，里面有该文件的全部元数据。",
         ref="综合 RecentManager：get_items() 返回所有最近使用文件的 std::vector"),
]

KP = dict(id="gtkmm.recentdocs.quizset", title="最近使用的文档测验集", difficulty=2, mastery_goal="required")

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply_new("chapter-recent-documents", KP, inpage, cp)
        print("written")
