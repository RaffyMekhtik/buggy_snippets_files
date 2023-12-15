def run(request):
    """View the manifest."""
    try:
        directory = settings.BASE_DIR  # BASE DIR
        md5 = request.GET['md5']  # MD5
        typ = request.GET['type']  # APK or SOURCE
        binary = request.GET['bin']
        match = re.match('^[0-9a-f]{32}$', md5)
        if match and (typ in ['eclipse', 'studio', 'apk']) and (binary in ['1', '0']):
            app_dir = os.path.join(
                settings.UPLD_DIR, md5 + '/')  # APP DIRECTORY
            tools_dir = os.path.join(directory, 'StaticAnalyzer/tools/')  # TOOLS DIR
            if binary == '1':
                is_binary = True
            elif binary == '0':
                is_binary = False
            app_path = os.path.join(app_dir, md5 + ".apk")
            manifest = read_manifest(app_dir, app_path, tools_dir, typ, is_binary)
            context = {
                'title': 'AndroidManifest.xml',
                'file': 'AndroidManifest.xml',
                'dat': manifest
            }
            template = "static_analysis/view_mani.html"
            return render(request, template, context)
    except:
        PrintException("Viewing AndroidManifest.xml")
        return print_n_send_error_response(request, "Error Viewing AndroidManifest.xml")