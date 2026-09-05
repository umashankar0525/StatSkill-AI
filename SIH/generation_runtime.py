"""Bounded retries and prompt-free diagnostics for local model requests."""
import contextvars,json,logging,os,random,socket,time,urllib.error
from logging.handlers import RotatingFileHandler
from pathlib import Path
from storage import db

context=contextvars.ContextVar('generation_context',default={})
logger=logging.getLogger('statskill.generation')

class GenerationError(RuntimeError):
    def __init__(self,code,message,retryable=True,retry_after=0):
        super().__init__(message);self.code=code;self.retryable=retryable;self.retry_after=retry_after

def init():
    with db() as c:c.execute('CREATE TABLE IF NOT EXISTS generation_events(id INTEGER PRIMARY KEY,created REAL,session_id TEXT,event TEXT,payload TEXT)')
    if not logger.handlers:
        folder=Path(__file__).parent/'logs';folder.mkdir(exist_ok=True)
        handler=RotatingFileHandler(folder/f'generation-{os.getpid()}.jsonl',maxBytes=2_000_000,backupCount=3,encoding='utf-8')
        logger.addHandler(handler);logger.setLevel(logging.INFO)

def memory():
    if os.name!='nt':return {}
    try:
        import ctypes
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
        value=Memory();value.length=ctypes.sizeof(value);ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value))
        return {'available_memory_mb':round(value.available/1048576),'memory_load_percent':value.load}
    except Exception:return {}

def event(name,**fields):
    value={**context.get(),**fields,**memory()}
    logger.info(json.dumps(dict(event=name,created=time.time(),**value)))
    try:
        with db() as c:
            c.execute('INSERT INTO generation_events(created,session_id,event,payload) VALUES(?,?,?,?)',(time.time(),value.get('session_id'),name,json.dumps(value)))
            c.execute('DELETE FROM generation_events WHERE id < (SELECT coalesce(max(id),0)-5000 FROM generation_events)')
    except Exception:logger.exception('Could not persist generation diagnostics')

def classify(exc):
    if isinstance(exc,GenerationError):return exc
    if isinstance(exc,urllib.error.HTTPError):
        try:delay=float(exc.headers.get('Retry-After','0'))
        except (TypeError,ValueError):delay=0
        return GenerationError('http_'+str(exc.code),'Local model service returned HTTP '+str(exc.code),exc.code in (408,429,500,502,503,504),min(30,max(0,delay)))
    if isinstance(exc,(TimeoutError,socket.timeout)):return GenerationError('timeout','The local model request timed out.')
    if isinstance(exc,urllib.error.URLError):return GenerationError('connection','The local model service could not be reached.')
    if isinstance(exc,(ValueError,KeyError,TypeError)):return GenerationError('invalid_output',str(exc)[:250])
    return GenerationError('service_error',str(exc)[:250])

def retry(fn,attempts=4):
    for attempt in range(1,attempts+1):
        try:return fn(attempt)
        except Exception as exc:
            failure=classify(exc)
            event('attempt_failed',attempt=attempt,error_code=failure.code,error=str(failure),retryable=failure.retryable)
            if not failure.retryable or attempt==attempts:raise failure from exc
            # A locally rejected duplicate needs a different prompt, not a network backoff.
            delay=0 if failure.code=='duplicate' else max(failure.retry_after,min(8,2**(attempt-1)))+random.uniform(0,.25)
            event('retry_scheduled',attempt=attempt,delay_seconds=round(delay,2))
            if delay:time.sleep(delay)
