"""Download saved viewport PNGs without exposing a live browser or CDP."""
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from .model import _context

MAX_IMAGE_BYTES = 4 * 1024 * 1024


def get_screenshot(image_id):
    """Return PNG bytes for an observation in the current task session."""
    session = _context.get()
    if session is None:
        raise RuntimeError('get_screenshot is available only during an active Agent invocation')
    if not isinstance(image_id, str) or not re.fullmatch(r'[0-9a-f]{32}', image_id):
        raise ValueError('Invalid screenshot image_id')
    server, token, jid, rid, deadline = session
    remaining = deadline-time.time()
    if remaining <= 0:
        raise TimeoutError('Task execution deadline reached')
    query = urllib.parse.urlencode({'job_id': jid, 'run_id': rid})
    request = urllib.request.Request(server.rstrip('/')+'/api/client/screenshots/'+image_id+'?'+query,
                                    headers={'Authorization': 'Bearer '+token})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None  # Never forward a bearer token to a redirect target.
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=remaining) as response:
            if response.headers.get_content_type() != 'image/png':
                raise RuntimeError('Platform returned an invalid screenshot')
            raw = response.read(MAX_IMAGE_BYTES+1)
        if len(raw)>MAX_IMAGE_BYTES or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
            raise RuntimeError('Platform returned an invalid screenshot')
        if time.time()>=deadline:
            raise TimeoutError('Task execution deadline reached')
        return raw
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        raise RuntimeError(f'Platform screenshot request failed: HTTP {status}') from None
    except (OSError, ValueError) as exc:
        if isinstance(exc, TimeoutError):
            raise
        raise RuntimeError('Platform screenshot transport failed') from None


def save_screenshot(observation, directory):
    """Save a verified observation PNG; return its Path, or None on older servers."""
    import hashlib
    from pathlib import Path
    import struct
    metadata = observation.get('screenshot')
    if not metadata:
        return None
    image_id = metadata.get('image_id')
    if not isinstance(image_id, str) or not re.fullmatch(r'[0-9a-f]{32}', image_id) or metadata.get('mime_type') != 'image/png':
        raise ValueError('Invalid screenshot metadata')
    raw = get_screenshot(image_id)
    if (len(raw) != metadata.get('byte_size') or hashlib.sha256(raw).hexdigest() != metadata.get('sha256')
            or len(raw) < 24 or raw[:8] != b'\x89PNG\r\n\x1a\n' or raw[12:16] != b'IHDR'
            or struct.unpack('>II', raw[16:24]) != (metadata.get('width'), metadata.get('height'))):
        raise ValueError('Screenshot bytes do not match observation metadata')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (image_id + '.png')
    path.write_bytes(raw)
    return path
