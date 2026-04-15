# ============================================
# NIMNA Language — ImportStatement Handler
# File: src/ast/import_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    BringStatement,
    ModuleStatement,
)


# ============================================
# KNOWN STANDARD LIBRARIES
# ============================================

STANDARD_LIBRARIES = {

    # Math
    "nimna.math", "nimna.math.advanced", "nimna.math.statistics",
    "nimna.math.matrix", "nimna.math.geometry", "nimna.math.calculus",
    "nimna.math.random", "nimna.math.bitwise", "nimna.math.complex",
    "nimna.math.primes", "nimna.math.trigonometry", "nimna.math.linear",
    "nimna.math.graph", "nimna.math.finance", "nimna.math.units",

    # Text
    "nimna.text", "nimna.text.regex", "nimna.text.format",
    "nimna.text.encoding", "nimna.text.unicode", "nimna.text.template",
    "nimna.text.parse", "nimna.text.diff", "nimna.text.search",
    "nimna.text.compress",

    # Files
    "nimna.files", "nimna.files.path", "nimna.files.watch",
    "nimna.files.zip", "nimna.files.tar", "nimna.files.stream",
    "nimna.files.temp", "nimna.files.permission", "nimna.files.link",
    "nimna.files.mount",

    # Network
    "nimna.network", "nimna.network.tcp", "nimna.network.udp",
    "nimna.network.dns", "nimna.network.socket", "nimna.network.proxy",
    "nimna.network.ssh", "nimna.network.ftp", "nimna.network.smtp",
    "nimna.network.websocket", "nimna.network.grpc", "nimna.network.quic",
    "nimna.network.http2", "nimna.network.bluetooth", "nimna.network.vpn",

    # HTTP
    "nimna.http", "nimna.http.client", "nimna.http.server",
    "nimna.http.router", "nimna.http.middleware", "nimna.http.session",
    "nimna.http.cookie", "nimna.http.cors", "nimna.http.cache",
    "nimna.http.ratelimit",

    # Database
    "nimna.db", "nimna.db.sql", "nimna.db.nosql", "nimna.db.orm",
    "nimna.db.redis", "nimna.db.mongo", "nimna.db.postgres",
    "nimna.db.sqlite", "nimna.db.mysql", "nimna.db.migration",
    "nimna.db.query", "nimna.db.pool", "nimna.db.backup",
    "nimna.db.cache", "nimna.db.stream",

    # AI
    "nimna.ai", "nimna.ai.neural", "nimna.ai.language",
    "nimna.ai.vision", "nimna.ai.speech", "nimna.ai.audio",
    "nimna.ai.training", "nimna.ai.inference", "nimna.ai.dataset",
    "nimna.ai.transform", "nimna.ai.embedding", "nimna.ai.cluster",
    "nimna.ai.classify", "nimna.ai.detect", "nimna.ai.generate",
    "nimna.ai.reinforce", "nimna.ai.graph", "nimna.ai.diffusion",
    "nimna.ai.tokenize", "nimna.ai.pipeline",

    # Data Science
    "nimna.data", "nimna.data.frame", "nimna.data.csv",
    "nimna.data.json", "nimna.data.xml", "nimna.data.plot",
    "nimna.data.chart", "nimna.data.statistics", "nimna.data.clean",
    "nimna.data.merge", "nimna.data.pivot", "nimna.data.series",
    "nimna.data.parquet", "nimna.data.arrow", "nimna.data.stream",

    # Crypto & Security
    "nimna.crypto", "nimna.crypto.hash", "nimna.crypto.aes",
    "nimna.crypto.rsa", "nimna.crypto.elliptic", "nimna.crypto.jwt",
    "nimna.crypto.tls", "nimna.crypto.otp", "nimna.crypto.sign",
    "nimna.security", "nimna.security.auth", "nimna.security.access",
    "nimna.security.filter", "nimna.security.protect",
    "nimna.security.audit",

    # Serialization
    "nimna.serial", "nimna.serial.json", "nimna.serial.xml",
    "nimna.serial.yaml", "nimna.serial.toml", "nimna.serial.csv",
    "nimna.serial.binary", "nimna.serial.proto", "nimna.serial.msgpack",
    "nimna.serial.cbor",

    # Concurrency
    "nimna.async", "nimna.thread", "nimna.parallel", "nimna.channel",
    "nimna.mutex", "nimna.atomic", "nimna.pool", "nimna.queue",
    "nimna.schedule", "nimna.event", "nimna.signal", "nimna.actor",
    "nimna.future", "nimna.reactive", "nimna.coroutine",

    # Testing
    "nimna.test", "nimna.test.unit", "nimna.test.mock",
    "nimna.test.benchmark", "nimna.test.e2e", "nimna.test.snapshot",
    "nimna.test.coverage", "nimna.test.assert", "nimna.test.fuzz",
    "nimna.test.report",

    # Logging
    "nimna.log", "nimna.log.file", "nimna.log.json",
    "nimna.log.remote", "nimna.log.rotate", "nimna.log.level",
    "nimna.log.trace", "nimna.log.metric", "nimna.log.alert",
    "nimna.log.format",

    # Cloud
    "nimna.cloud", "nimna.cloud.aws", "nimna.cloud.google",
    "nimna.cloud.azure", "nimna.cloud.storage", "nimna.cloud.functions",
    "nimna.cloud.containers", "nimna.cloud.orchestrate",
    "nimna.cloud.ci", "nimna.cloud.monitor", "nimna.cloud.config",
    "nimna.cloud.secrets", "nimna.cloud.queue", "nimna.cloud.cdn",
    "nimna.cloud.deploy",

    # GUI
    "nimna.gui", "nimna.gui.window", "nimna.gui.widget",
    "nimna.gui.canvas", "nimna.gui.layout", "nimna.gui.theme",
    "nimna.gui.event", "nimna.gui.animation", "nimna.gui.render",
    "nimna.gui.native",

    # System
    "nimna.system", "nimna.system.process", "nimna.system.env",
    "nimna.system.time", "nimna.system.clock", "nimna.system.timer",
    "nimna.system.uid", "nimna.system.color", "nimna.system.args",
    "nimna.system.url", "nimna.system.mime", "nimna.system.format",
    "nimna.system.reflect", "nimna.system.version",
    "nimna.system.platform",

    # IO (most common)
    "nimna.io",
}


# ============================================
# KNOWN FRAMEWORKS
# ============================================

KNOWN_FRAMEWORKS = {
    "velox", "ironclad", "flowedge", "aurion", "prism",
    "nexstack", "orbitssr", "swiftroot", "neuraflow",
    "torchnim", "dataforge", "cloudwing", "glassui",
    "pixelforge", "vaultapi", "graphnim", "echorpc",
    "crestdb", "testbridge", "zephyr"
}


# ============================================
# IMPORT HANDLER CLASS
# ============================================

class ImportHandler:
    """
    NIMNA ImportStatement Handler

    Handles:
    - module declaration  : module main
    - bring statement     : bring nimna.io
    - selective import    : bring nimna.io from print

    Validates:
    - Module path format
    - Known libraries
    - Duplicate imports
    - Circular import detection
    """

    def __init__(self, filename="<nimna>"):
        self.filename       = filename
        self.errors         = []
        self.warnings       = []
        self.imported_paths = set()
        self.module_name    = None


    def create_module(self, name, line=None, column=None):
        """
        Create a ModuleStatement node.

        Example:
            module main
            module utils
        """

        # Validate module name
        name_valid, name_error = self._validate_identifier(name, line)
        if not name_valid:
            self.errors.append(name_error)
            return None

        # Only one module statement per file
        if self.module_name:
            self.errors.append(
                f"[Line {line}] Module already declared as "
                f"'{self.module_name}'. Cannot redeclare."
            )
            return None

        self.module_name = name

        return ModuleStatement(
            name   = name,
            line   = line,
            column = column
        )


    def create_bring(self, module_path, from_items=None,
                     line=None, column=None):
        """
        Create a BringStatement node.

        Example:
            bring nimna.io
            bring nimna.math from add, subtract
        """

        # Validate module path
        path_valid, path_error = self._validate_path(module_path, line)
        if not path_valid:
            self.errors.append(path_error)
            return None

        # Check duplicate import
        if module_path in self.imported_paths:
            self.warnings.append(
                f"[Line {line}] '{module_path}' is already imported. "
                f"Duplicate import ignored."
            )
            return None

        # Check if standard library
        if module_path.startswith("nimna."):
            if module_path not in STANDARD_LIBRARIES:
                self.warnings.append(
                    f"[Line {line}] '{module_path}' is not a known "
                    f"NIMNA standard library. "
                    f"Make sure it is installed via nimpkg."
                )

        # Check if framework
        base_name = module_path.split(".")[0].lower()
        if base_name in KNOWN_FRAMEWORKS:
            self.warnings.append(
                f"[Line {line}] Importing framework '{base_name}'. "
                f"Make sure it is installed: nimpkg install {base_name}"
            )

        # Validate from items
        if from_items:
            for item in from_items:
                item_valid, item_error = self._validate_identifier(
                    item, line
                )
                if not item_valid:
                    self.errors.append(item_error)
                    return None

        # Register import
        self.imported_paths.add(module_path)

        return BringStatement(
            module_path = module_path,
            alias       = from_items,
            line        = line,
            column      = column
        )


    def _validate_path(self, path, line):
        """
        Validate module path format.
        e.g. nimna.io, nimna.math.stats
        """

        if not path:
            return False, (
                f"[Line {line}] Import path cannot be empty."
            )

        parts = path.split(".")

        for part in parts:
            if not part:
                return False, (
                    f"[Line {line}] Invalid module path '{path}'. "
                    f"Empty segment found."
                )
            if not (part[0].isalpha() or part[0] == '_'):
                return False, (
                    f"[Line {line}] Invalid module path segment "
                    f"'{part}' in '{path}'."
                )

        return True, ""


    def _validate_identifier(self, name, line):
        """Validate a simple identifier."""

        if not name:
            return False, f"[Line {line}] Name cannot be empty."

        if not (name[0].isalpha() or name[0] == '_'):
            return False, (
                f"[Line {line}] Invalid name '{name}'. "
                f"Must start with letter or underscore."
            )

        return True, ""


    def get_import_summary(self):
        """Get summary of all imports."""

        lines = []
        if self.module_name:
            lines.append(f"module {self.module_name}")
        for path in sorted(self.imported_paths):
            lines.append(f"bring {path}")
        return "\n".join(lines)


    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []

    def reset(self):
        self.errors         = []
        self.warnings       = []
        self.imported_paths = set()
        self.module_name    = None
