import base64, csv, io, json, mimetypes, os, pathlib, re, secrets, sys, threading, time, urllib.error, urllib.parse, urllib.request, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT=pathlib.Path(__file__).resolve().parent
EXPLORER_DATA=ROOT.parent/'ebay-category-explorer'/'data'
# Vorhandene Zugangsdaten bevorzugen, sonst neben der App ablegen.
DATA=next((p for p in (EXPLORER_DATA,ROOT/'data') if (p/'config.json').exists()),ROOT/'data'); DATA.mkdir(exist_ok=True)
CONFIG=DATA/'config.json'; CACHE=DATA/'cache'; CACHE.mkdir(exist_ok=True)
DEFAULT={'client_id':'','client_secret':'','environment':'production','marketplace':'EBAY_DE'}
TOKEN={'token':'','expires':0}
LOCK=threading.RLock()

def settings():
    try: return {**DEFAULT, **json.loads(CONFIG.read_text('utf-8'))}
    except (FileNotFoundError,ValueError): return dict(DEFAULT)

def error_message(exc):
    if isinstance(exc,urllib.error.HTTPError):
        body=exc.read(5000).decode('utf-8','replace')
        try:
            j=json.loads(body); body=json.dumps(j,ensure_ascii=False)
        except ValueError: pass
        return f'eBay HTTP {exc.code}: {body[:1000]}'
    return str(exc)

def api(path,params=None):
    s=settings()
    with LOCK:
        if not TOKEN['token'] or time.time()>TOKEN['expires']-60:
            if not s['client_id'] or not s['client_secret']: raise ValueError('Bitte erst Client ID und Client Secret unter Einstellungen speichern.')
            domain='api.sandbox.ebay.com' if s['environment']=='sandbox' else 'api.ebay.com'
            basic=base64.b64encode((s['client_id']+':'+s['client_secret']).encode()).decode()
            payload=urllib.parse.urlencode({'grant_type':'client_credentials','scope':'https://api.ebay.com/oauth/api_scope'}).encode()
            req=urllib.request.Request(f'https://{domain}/identity/v1/oauth2/token',data=payload,headers={'Authorization':'Basic '+basic,'Content-Type':'application/x-www-form-urlencoded'},method='POST')
            with urllib.request.urlopen(req,timeout=25) as r: j=json.load(r)
            TOKEN.update(token=j['access_token'],expires=time.time()+int(j.get('expires_in',7200)))
        domain='api.sandbox.ebay.com' if s['environment']=='sandbox' else 'api.ebay.com'
        url=f'https://{domain}/commerce/taxonomy/v1/{path}'
        if params: url+='?'+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+TOKEN['token'],'Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)

def tree():
    s=settings(); cache=CACHE/f"tree_{s['environment']}_{s['marketplace']}.json"
    if cache.exists() and time.time()-cache.stat().st_mtime < 86400:
        return json.loads(cache.read_text('utf-8'))
    data=api('get_default_category_tree_id',{'marketplace_id':s['marketplace']}); cache.write_text(json.dumps(data),'utf-8'); return data

def get_aspects(category,refresh=False,category_name=''):
    if not re.fullmatch(r'\d{1,15}',str(category)):raise ValueError('Ungültige Kategorie-ID.')
    t=tree(); s=settings(); fname=CACHE/f"aspects_{s['environment']}_{s['marketplace']}_{t['categoryTreeId']}_{category}.json"
    if not refresh and fname.exists():
        obj=json.loads(fname.read_text('utf-8'))
        if category_name and not obj.get('categoryName'):
            obj['categoryName']=category_name;fname.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
        return obj,True
    j=api(f"category_tree/{t['categoryTreeId']}/get_item_aspects_for_category",{'category_id':category})
    obj={'categoryId':category,'categoryName':category_name,'treeId':t['categoryTreeId'],'marketplace':s['marketplace'],'environment':s['environment'],'fetchedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'aspects':j.get('aspects',[])}
    fname.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8'); return obj,False

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def cors(self):
        # Erlaubt der auf GitHub Pages installierten PWA den Zugriff auf diesen
        # lokalen Dienst. Der Dienst bindet ausschliesslich an 127.0.0.1.
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type,Authorization')
        self.send_header('Access-Control-Max-Age','86400')
    def respond(self,value,status=200):
        raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.cors();self.end_headers();self.wfile.write(raw)
    def fail(self,e):self.respond({'error':error_message(e)},400)
    def static(self,url_path):
        relative=urllib.parse.unquote(url_path).lstrip('/') or 'index.html'
        target=(ROOT/relative).resolve()
        if ROOT not in target.parents and target!=ROOT:return False
        if not target.is_file():return False
        raw=target.read_bytes();mime=mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        if target.suffix in ('.html','.json','.js','.webmanifest'):mime+='; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)));self.cors();self.end_headers();self.wfile.write(raw);return True
    def do_OPTIONS(self):
        self.send_response(204);self.cors();self.send_header('Content-Length','0');self.end_headers()
    def do_GET(self):
        url=urllib.parse.urlsplit(self.path); p=urllib.parse.parse_qs(url.query); q=lambda k,d='':p.get(k,[d])[0]
        try:
            if url.path=='/':
                self.static('/index.html')
            elif url.path=='/api/config':
                s=settings();self.respond({'client_id':s['client_id'],'client_secret_set':bool(s['client_secret']),'environment':s['environment'],'marketplace':s['marketplace']})
            elif url.path=='/api/test':
                self.respond({'ok':True,'tree':tree()})
            elif url.path=='/api/search':
                term=q('q').strip()
                if not term:raise ValueError('Suchbegriff fehlt.')
                t=tree();self.respond(api(f"category_tree/{t['categoryTreeId']}/get_category_suggestions",{'q':term}))
            elif url.path=='/api/aspects':
                obj,cached=get_aspects(q('category'),q('refresh')=='true',q('name').strip());self.respond({'data':obj,'cached':cached})
            elif url.path=='/api/categories':
                s=settings(); prefix=f"aspects_{s['environment']}_{s['marketplace']}_"; out=[]
                for f in CACHE.glob(prefix+'*.json'):
                    try:
                        a=json.loads(f.read_text('utf-8'));out.append({'categoryId':a['categoryId'],'categoryName':a.get('categoryName',''),'count':len(a['aspects']),'fetchedAt':a.get('fetchedAt')})
                    except Exception:continue
                self.respond(sorted(out,key=lambda o:o['fetchedAt'] or '',reverse=True))
            elif url.path=='/api/export':
                obj,_=get_aspects(q('category'))
                fmt=q('format','json')
                if fmt=='json':raw=json.dumps(obj,ensure_ascii=False,indent=2).encode('utf-8');mime='application/json';suffix='json'
                elif fmt=='csv':
                    s=io.StringIO();w=csv.writer(s,delimiter=';');w.writerow(['Kategorie-ID','Merkmal','Pflicht','Typ','Eingabemodus','Mehrfachwerte','Varianten','Werte','Rohdaten (JSON)'])
                    for a in obj['aspects']:
                        c=a.get('aspectConstraint') or {}; w.writerow([obj['categoryId'],a.get('localizedAspectName',''),c.get('aspectRequired',''),c.get('aspectDataType',''),c.get('aspectMode',''),c.get('itemToAspectCardinality',''),c.get('aspectEnabledForVariations',''),' | '.join(v.get('localizedValue','') for v in a.get('aspectValues',[])),json.dumps(a,ensure_ascii=False)])
                    raw=('\ufeff'+s.getvalue()).encode('utf-8');mime='text/csv; charset=utf-8';suffix='csv'
                else:raise ValueError('Exportformat nicht unterstützt')
                self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Disposition',f'attachment; filename="ebay_aspects_{obj["categoryId"]}.{suffix}"');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            elif not self.static(url.path):self.respond({'error':'Not found'},404)
        except (ValueError,KeyError,urllib.error.URLError,TimeoutError) as e:self.fail(e)
        except Exception as e:self.fail(e)
    def do_POST(self):
        try:
            if self.path!='/api/config':return self.respond({'error':'Not found'},404)
            length=int(self.headers.get('Content-Length','0'))
            if length>20000:raise ValueError('Zu große Eingabe')
            j=json.loads(self.rfile.read(length)); old=settings()
            if j.get('environment','production') not in ('production','sandbox'):raise ValueError('Ungültige Umgebung')
            if j.get('marketplace','EBAY_DE') not in ('EBAY_DE','EBAY_AT','EBAY_CH','EBAY_US','EBAY_GB'):raise ValueError('Ungültiger Marktplatz')
            new={'client_id':str(j.get('client_id') or old['client_id']).strip(),'client_secret':str(j.get('client_secret') or old['client_secret']),'environment':j['environment'],'marketplace':j['marketplace']}
            CONFIG.write_text(json.dumps(new,ensure_ascii=False,indent=2),'utf-8')
            try:os.chmod(CONFIG,0o600)
            except OSError:pass
            TOKEN.update(token='',expires=0)
            self.respond({'ok':True})
        except Exception as e:self.fail(e)

if __name__=='__main__':
    # Fester Port, damit die auf GitHub Pages installierte PWA den lokalen
    # Dienst unter einer bekannten Adresse erreichen kann.
    PORT=int(os.environ.get('EBAY_TOOL_PORT','8765'))
    def probe(port):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/config',timeout=2) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception:return None
    existing=probe(PORT)
    if existing is not None:
        print(f'Ebay Category Explorer laeuft bereits: http://127.0.0.1:{PORT}',flush=True)
        threading.Timer(0.5,lambda:webbrowser.open(f'http://127.0.0.1:{PORT}')).start()
        sys.exit(0)
    server=None
    for port in (PORT,0):
        try:
            server=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
        except OSError:continue
    if server is None:
        print('Kein freier Port verfuegbar.',flush=True);sys.exit(1)
    port=server.server_address[1];url=f'http://127.0.0.1:{port}'
    print('eBay Category Explorer läuft: '+url,flush=True)
    print('Die PWA erreicht diesen Dienst über dieselbe Adresse.',flush=True)
    threading.Timer(0.8,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
