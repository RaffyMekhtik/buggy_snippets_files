def process_bookmark(hide='n', start_page=1, end_page=0):
    try:
        total_list = list()
        print(f"My Member Id = {__br__._myId}")
        if hide != 'o':
            print("Importing Bookmarks...")
            total_list.extend(get_bookmarks(False, start_page, end_page, __br__._myId))
        if hide != 'n':
            print("Importing Private Bookmarks...")
            total_list.extend(get_bookmarks(True, start_page, end_page, __br__._myId))
        print(f"Result: {str(len(total_list))} items.")
        i = 0
        current_member = 1
        for item in total_list:
            print("%d/%d\t%f %%" % (i, len(total_list), 100.0 * i / float(len(total_list))))
            i += 1
            prefix = "[{0} of {1}]".format(current_member, len(total_list))
            process_member(item.memberId, item.path, title_prefix=prefix)
            current_member = current_member + 1

        if len(total_list) > 0:
            print("%d/%d\t%f %%" % (i, len(total_list), 100.0 * i / float(len(total_list))))
        else:
            print("Cannot find any followed member.")
    except KeyboardInterrupt:
        raise
    except BaseException:
        PixivHelper.print_and_log('error', 'Error at process_bookmark(): {0}'.format(sys.exc_info()))
        raise