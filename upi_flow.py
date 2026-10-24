# zlib-compressed module body
import zlib, base64, sys, types
_CODE = """PLACEHOLDER"""
_mod = types.ModuleType(__name__)
exec(compile(zlib.decompress(base64.b64decode(_CODE)), __file__, "exec"), _mod.__dict__)
globals().update({k: v for k, v in _mod.__dict__.items() if not k.startswith("_")})
