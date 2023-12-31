    def __init__(self) -> None:
        # -- build options --
        self.build_type = BuildType.STANDARD
        self.python_version = defaults.PYTHON3_VERSION
        self.platform = sys.platform
        self.custom_typing_module = None  # type: str
        self.report_dirs = {}  # type: Dict[str, str]
        self.silent_imports = False
        self.almost_silent = False

        # Disallow calling untyped functions from typed ones
        self.disallow_untyped_calls = False

        # Disallow defining untyped (or incompletely typed) functions
        self.disallow_untyped_defs = False

        # Type check unannotated functions
        self.check_untyped_defs = False

        # Disallow subclassing values of type 'Any'
        self.disallow_subclassing_any = False

        # Also check typeshed for missing annotations
        self.warn_incomplete_stub = False

        # Warn about casting an expression to its inferred type
        self.warn_redundant_casts = False

        # Warn about falling off the end of a function returning non-None
        self.warn_no_return = False

        # Warn about unused '# type: ignore' comments
        self.warn_unused_ignores = False

        # Apply strict None checking
        self.strict_optional = False

        # Files in which to allow strict-Optional related errors
        # TODO: Kill this in favor of show_none_errors
        self.strict_optional_whitelist = None   # type: Optional[List[str]]

        # Alternate way to show/hide strict-None-checking related errors
        self.show_none_errors = True

        # Use script name instead of __main__
        self.scripts_are_modules = False

        # Config file name
        self.config_file = None  # type: Optional[str]

        # Per-file options (raw)
        self.per_file_options = {}  # type: Dict[str, Dict[str, object]]

        # -- development options --
        self.verbosity = 0  # More verbose messages (for troubleshooting)
        self.pdb = False
        self.show_traceback = False
        self.dump_type_stats = False
        self.dump_inference_stats = False

        # -- test options --
        # Stop after the semantic analysis phase
        self.semantic_analysis_only = False

        # Use stub builtins fixtures to speed up tests
        self.use_builtins_fixtures = False

        # -- experimental options --
        self.fast_parser = False
        self.incremental = False
        self.cache_dir = defaults.CACHE_DIR
        self.debug_cache = False
        self.hide_error_context = False  # Hide "note: In function "foo":" messages.
        self.shadow_file = None  # type: Optional[Tuple[str, str]]
        self.show_column_numbers = False  # type: bool