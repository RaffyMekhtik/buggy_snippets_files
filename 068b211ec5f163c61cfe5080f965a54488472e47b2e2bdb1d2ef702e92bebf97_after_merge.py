def get_extensions():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    extensions_dir = os.path.join(this_dir, 'torchvision', 'csrc')

    main_file = glob.glob(os.path.join(extensions_dir, '*.cpp')) + glob.glob(os.path.join(extensions_dir, 'ops',
                                                                                          '*.cpp'))
    source_cpu = glob.glob(os.path.join(extensions_dir, 'ops', 'autograd', '*.cpp')) + glob.glob(
        os.path.join(extensions_dir, 'ops', 'cpu', '*.cpp'))

    is_rocm_pytorch = False
    if torch.__version__ >= '1.5':
        from torch.utils.cpp_extension import ROCM_HOME
        is_rocm_pytorch = True if ((torch.version.hip is not None) and (ROCM_HOME is not None)) else False

    if is_rocm_pytorch:
        hipify_python.hipify(
            project_directory=this_dir,
            output_directory=this_dir,
            includes="torchvision/csrc/ops/cuda/*",
            show_detailed=True,
            is_pytorch_extension=True,
        )
        source_cuda = glob.glob(os.path.join(extensions_dir, 'ops', 'hip', '*.hip'))
        # Copy over additional files
        for file in glob.glob(r"torchvision/csrc/ops/cuda/*.h"):
            shutil.copy(file, "torchvision/csrc/ops/hip")

    else:
        source_cuda = glob.glob(os.path.join(extensions_dir, 'ops', 'cuda', '*.cu'))

    source_cuda += glob.glob(os.path.join(extensions_dir, 'ops', 'autocast', '*.cpp'))

    sources = main_file + source_cpu
    extension = CppExtension

    compile_cpp_tests = os.getenv('WITH_CPP_MODELS_TEST', '0') == '1'
    if compile_cpp_tests:
        test_dir = os.path.join(this_dir, 'test')
        models_dir = os.path.join(this_dir, 'torchvision', 'csrc', 'models')
        test_file = glob.glob(os.path.join(test_dir, '*.cpp'))
        source_models = glob.glob(os.path.join(models_dir, '*.cpp'))

        test_file = [os.path.join(test_dir, s) for s in test_file]
        source_models = [os.path.join(models_dir, s) for s in source_models]
        tests = test_file + source_models
        tests_include_dirs = [test_dir, models_dir]

    define_macros = []

    extra_compile_args = {'cxx': []}
    if (torch.cuda.is_available() and ((CUDA_HOME is not None) or is_rocm_pytorch)) \
            or os.getenv('FORCE_CUDA', '0') == '1':
        extension = CUDAExtension
        sources += source_cuda
        if not is_rocm_pytorch:
            define_macros += [('WITH_CUDA', None)]
            nvcc_flags = os.getenv('NVCC_FLAGS', '')
            if nvcc_flags == '':
                nvcc_flags = []
            else:
                nvcc_flags = nvcc_flags.split(' ')
        else:
            define_macros += [('WITH_HIP', None)]
            nvcc_flags = []
        extra_compile_args["nvcc"] = nvcc_flags

    if sys.platform == 'win32':
        define_macros += [('torchvision_EXPORTS', None)]

        extra_compile_args['cxx'].append('/MP')

    debug_mode = os.getenv('DEBUG', '0') == '1'
    if debug_mode:
        print("Compile in debug mode")
        extra_compile_args['cxx'].append("-g")
        extra_compile_args['cxx'].append("-O0")
        if "nvcc" in extra_compile_args:
            # we have to remove "-OX" and "-g" flag if exists and append
            nvcc_flags = extra_compile_args["nvcc"]
            extra_compile_args["nvcc"] = [
                f for f in nvcc_flags if not ("-O" in f or "-g" in f)
            ]
            extra_compile_args["nvcc"].append("-O0")
            extra_compile_args["nvcc"].append("-g")

    sources = [os.path.join(extensions_dir, s) for s in sources]

    include_dirs = [extensions_dir]

    ext_modules = [
        extension(
            'torchvision._C',
            sorted(sources),
            include_dirs=include_dirs,
            define_macros=define_macros,
            extra_compile_args=extra_compile_args,
        )
    ]
    if compile_cpp_tests:
        ext_modules.append(
            extension(
                'torchvision._C_tests',
                tests,
                include_dirs=tests_include_dirs,
                define_macros=define_macros,
                extra_compile_args=extra_compile_args,
            )
        )

    # ------------------- Torchvision extra extensions ------------------------
    vision_include = os.environ.get('TORCHVISION_INCLUDE', None)
    vision_library = os.environ.get('TORCHVISION_LIBRARY', None)
    vision_include = (vision_include.split(os.pathsep)
                      if vision_include is not None else [])
    vision_library = (vision_library.split(os.pathsep)
                      if vision_library is not None else [])
    include_dirs += vision_include
    library_dirs = vision_library

    # Image reading extension
    image_macros = []
    image_include = [extensions_dir]
    image_library = []
    image_link_flags = []

    # Locating libPNG
    libpng = distutils.spawn.find_executable('libpng-config')
    pngfix = distutils.spawn.find_executable('pngfix')
    png_found = libpng is not None or pngfix is not None
    print('PNG found: {0}'.format(png_found))
    if png_found:
        if libpng is not None:
            # Linux / Mac
            png_version = subprocess.run([libpng, '--version'],
                                         stdout=subprocess.PIPE)
            png_version = png_version.stdout.strip().decode('utf-8')
            print('libpng version: {0}'.format(png_version))
            png_version = parse_version(png_version)
            if png_version >= parse_version("1.6.0"):
                print('Building torchvision with PNG image support')
                png_lib = subprocess.run([libpng, '--libdir'],
                                         stdout=subprocess.PIPE)
                png_lib = png_lib.stdout.strip().decode('utf-8')
                if 'disabled' not in png_lib:
                    image_library += [png_lib]
                png_include = subprocess.run([libpng, '--I_opts'],
                                             stdout=subprocess.PIPE)
                png_include = png_include.stdout.strip().decode('utf-8')
                _, png_include = png_include.split('-I')
                print('libpng include path: {0}'.format(png_include))
                image_include += [png_include]
                image_link_flags.append('png')
            else:
                print('libpng installed version is less than 1.6.0, '
                      'disabling PNG support')
                png_found = False
        else:
            # Windows
            png_lib = os.path.join(
                os.path.dirname(os.path.dirname(pngfix)), 'lib')
            png_include = os.path.join(os.path.dirname(
                os.path.dirname(pngfix)), 'include', 'libpng16')
            image_library += [png_lib]
            image_include += [png_include]
            image_link_flags.append('libpng')

    # Locating libjpeg
    (jpeg_found, jpeg_conda,
     jpeg_include, jpeg_lib) = find_library('jpeglib', vision_include)

    print('JPEG found: {0}'.format(jpeg_found))
    image_macros += [('PNG_FOUND', str(int(png_found)))]
    image_macros += [('JPEG_FOUND', str(int(jpeg_found)))]
    if jpeg_found:
        print('Building torchvision with JPEG image support')
        image_link_flags.append('jpeg')
        if jpeg_conda:
            image_library += [jpeg_lib]
            image_include += [jpeg_include]

    image_path = os.path.join(extensions_dir, 'io', 'image')
    image_src = glob.glob(os.path.join(image_path, '*.cpp')) + glob.glob(os.path.join(image_path, 'cpu', '*.cpp'))

    if png_found or jpeg_found:
        ext_modules.append(extension(
            'torchvision.image',
            image_src,
            include_dirs=image_include + include_dirs + [image_path],
            library_dirs=image_library + library_dirs,
            define_macros=image_macros,
            libraries=image_link_flags,
            extra_compile_args=extra_compile_args
        ))

    ffmpeg_exe = distutils.spawn.find_executable('ffmpeg')
    has_ffmpeg = ffmpeg_exe is not None
    print("FFmpeg found: {}".format(has_ffmpeg))

    if has_ffmpeg:
        ffmpeg_libraries = {
            'libavcodec',
            'libavformat',
            'libavutil',
            'libswresample',
            'libswscale'
        }

        ffmpeg_bin = os.path.dirname(ffmpeg_exe)
        ffmpeg_root = os.path.dirname(ffmpeg_bin)
        ffmpeg_include_dir = os.path.join(ffmpeg_root, 'include')
        ffmpeg_library_dir = os.path.join(ffmpeg_root, 'lib')

        gcc = distutils.spawn.find_executable('gcc')
        platform_tag = subprocess.run(
            [gcc, '-print-multiarch'], stdout=subprocess.PIPE)
        platform_tag = platform_tag.stdout.strip().decode('utf-8')

        if platform_tag:
            # Most probably a Debian-based distribution
            ffmpeg_include_dir = [
                ffmpeg_include_dir,
                os.path.join(ffmpeg_include_dir, platform_tag)
            ]
            ffmpeg_library_dir = [
                ffmpeg_library_dir,
                os.path.join(ffmpeg_library_dir, platform_tag)
            ]
        else:
            ffmpeg_include_dir = [ffmpeg_include_dir]
            ffmpeg_library_dir = [ffmpeg_library_dir]

        has_ffmpeg = True
        for library in ffmpeg_libraries:
            library_found = False
            for search_path in ffmpeg_include_dir + include_dirs:
                full_path = os.path.join(search_path, library, '*.h')
                library_found |= len(glob.glob(full_path)) > 0

            if not library_found:
                print('{0} header files were not found, disabling ffmpeg '
                      'support')
                has_ffmpeg = False

    if has_ffmpeg:
        print("ffmpeg include path: {}".format(ffmpeg_include_dir))
        print("ffmpeg library_dir: {}".format(ffmpeg_library_dir))

        # TorchVision base decoder + video reader
        video_reader_src_dir = os.path.join(this_dir, 'torchvision', 'csrc', 'io', 'video_reader')
        video_reader_src = glob.glob(os.path.join(video_reader_src_dir, "*.cpp"))
        base_decoder_src_dir = os.path.join(this_dir, 'torchvision', 'csrc', 'io', 'decoder')
        base_decoder_src = glob.glob(
            os.path.join(base_decoder_src_dir, "*.cpp"))
        # Torchvision video API
        videoapi_src_dir = os.path.join(this_dir, 'torchvision', 'csrc', 'io', 'video')
        videoapi_src = glob.glob(os.path.join(videoapi_src_dir, "*.cpp"))
        # exclude tests
        base_decoder_src = [x for x in base_decoder_src if '_test.cpp' not in x]

        combined_src = video_reader_src + base_decoder_src + videoapi_src

        ext_modules.append(
            CppExtension(
                'torchvision.video_reader',
                combined_src,
                include_dirs=[
                    base_decoder_src_dir,
                    video_reader_src_dir,
                    videoapi_src_dir,
                    extensions_dir,
                    *ffmpeg_include_dir,
                    *include_dirs
                ],
                library_dirs=ffmpeg_library_dir + library_dirs,
                libraries=[
                    'avcodec',
                    'avformat',
                    'avutil',
                    'swresample',
                    'swscale',
                ],
                extra_compile_args=["-std=c++14"] if os.name != 'nt' else ['/std:c++14', '/MP'],
                extra_link_args=["-std=c++14" if os.name != 'nt' else '/std:c++14'],
            )
        )

    return ext_modules