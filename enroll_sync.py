"""Enroll Sync - Servis Tyres. UFace 800 / UFace 900 (ZKTeco), talks to the machines through the ZKTeco SDK (zkemkeeper).
 * Enrollments done on the Enroller machine (user, fingerprints, FACE, RFID card) are copied to every machine that is switched on,
   and are then removed from the Enroller (only after every machine has them and the backup is saved).
 * Backup: every enrollment found on any machine is kept in a backup database and updated; Reports tab lists the daily activity / deletions.
 * Employee list (Data button on the Connectivity tab, Decibel): employees whose service end date is before today are deleted from every machine.
 * Daily activity report + backup are e-mailed automatically (Email tab).
 * Restore: Reports tab > Restore from backup puts the saved enrollments back on the Enroller / machines.
 * Protected: the exe needs the password to open, and every entry / edit / Stop / Restore / Exit needs it too. The reset key (built into the exe, see PW_HASH) is needed to change the password and works on any PC / network.
Needs the ZKTeco SDK registered on this PC (zkemkeeper.dll) and a 32-bit build of this exe."""
import csv, hashlib, hmac, http.cookiejar, io, json, os, queue, re, shutil, smtplib, socket, sqlite3, ssl, tempfile, threading, time, urllib.parse, urllib.request, zipfile
from datetime import date, datetime, timedelta, time as dtime
from email.message import EmailMessage
import html as htmllib
from html.parser import HTMLParser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

LOGO_B64 = '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'
APP = os.path.join(os.environ.get('APPDATA') or os.path.dirname(os.path.abspath(__file__)), 'EnrollSync')
os.makedirs(APP, exist_ok=True)
CFG_FILE, SNAP_FILE, LIST_FILE = os.path.join(APP, 'config.json'), os.path.join(APP, 'snapshot.json'), os.path.join(APP, 'employee_list.dat')
BULK_LIMIT = 20                                   # more deletions than this in one cycle are skipped unless "Allow bulk delete" is ticked
q, STOP = queue.Queue(), threading.Event()
def log(msg): q.put(msg)


# ---------------------------------------------------------------- password
# RESET KEY: built into the exe (so it is never lost when the exe is copied to another PC / network). It is needed to set a new password,
#            and it is also the password until a new one is set. To change the reset key itself:
#   python -c "import hashlib;print(hashlib.pbkdf2_hmac('sha256', b'NEWKEY', b'EnrollSync-Servis', 200000).hex())"   -> paste into PW_HASH -> build the exe again.
# The everyday password set with "Reset password" is kept (hashed) in access.dat in the settings folder of this PC.
PW_SALT, PW_HASH = b'EnrollSync-Servis', 'b9386cd8c24bbd726abb598cb01765d2ff8a5d11f3f201f73f941ce893adf80b'
PW_FILE = os.path.join(APP, 'access.dat')
PW_FAIL = {'n': 0, 'until': 0.0}


def _hash(p, salt): return hashlib.pbkdf2_hmac('sha256', p.encode('utf-8'), salt, 200000).hex()


def check_master(p): return hmac.compare_digest(_hash(p, PW_SALT), PW_HASH)


def _custom():
    try:
        with open(PW_FILE, encoding='utf-8') as f: d = json.load(f)
        return bytes.fromhex(d['salt']), d['hash']
    except Exception:
        return None


def check_password(p):
    """The password that was set with 'Reset password'; until then the built-in key."""
    c = _custom()
    return hmac.compare_digest(_hash(p, c[0]), c[1]) if c else check_master(p)


def set_password(p):
    salt = os.urandom(16); save_json(PW_FILE, {'salt': salt.hex(), 'hash': _hash(p, salt)})


def load_json(path, default):
    try:
        with open(path, encoding='utf-8') as f: return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f)


def _default_machines():
    names = [f'IN {i:02d}' for i in range(1, 6)] + [f'OUT {i:02d}' for i in range(6, 11)] + ['Colony Gate IN', 'Colony Gate OUT']
    return [{'name': n, 'ip': '', 'on': True} for n in names]


cfg = {'enroller': '', 'port': 4370, 'comm_key': 0, 'interval': 60, 'bulk': False, 'purge': True, 'machines': None,
       'list_url': 'https://hrms1.mydecibel.com/TMS/CustomAttendanceReport.aspx?ReportIndex=1839', 'login_url': 'https://bpo.mydecibel.com/login.aspx', 'list_min': 60, 'del_leavers': True, 'dc_user': 'ST.404473', 'dc_pass': 'Ahmed!@4190',
       'backup_dir': '', 'scan_hours': 24, 'last_full': 0,
       'mail_on': True, 'mail_to': '', 'mail_server': 'smtp.gmail.com', 'mail_port': 587, 'mail_user': '', 'mail_pass': '', 'mail_time': '20:00', 'mail_last': ''}
cfg.update(load_json(CFG_FILE, {}))
cfg['list_url'] = cfg.get('list_url', '').replace('CustomAttendanceReport.aspx?&ReportIndex', 'CustomAttendanceReport.aspx?ReportIndex')   # old saved link -> link of the steps file
if not cfg.get('dc_user') or not cfg.get('dc_pass'): cfg['dc_user'], cfg['dc_pass'] = 'ST.404473', 'Ahmed!@4190'                   # User ID / Password of step 2
if not cfg.get('machines'):                                                   # first run, or settings of the older version (fixed IN / OUT rows)
    old, ms = cfg.get('rows') or {}, []
    for m in _default_machines():
        r = old.get(m['name'], {})
        on = bool(r.get('ip')) if m['name'].startswith('IN') else r.get('on', True)
        ms.append({'name': m['name'], 'ip': r.get('ip', ''), 'on': on})
    cfg['machines'] = ms


def norm(s):
    """Employee IDs from the list and from the machines are compared in this form (spaces, '.0' and leading zeros ignored)."""
    s = str(s if s is not None else '').strip()
    if s.endswith('.0'): s = s[:-2]
    return s.lstrip('0') or ('0' if s else '')


# ---------------------------------------------------------------- backup + report database (SQLite, one file in the backup folder)
def db_path():
    d = cfg.get('backup_dir') or os.path.join(APP, 'Backup')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'enroll_backup.db')


def db():
    c = sqlite3.connect(db_path(), timeout=30)
    c.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, priv INTEGER, pw TEXT, card TEXT, fp TEXT, face TEXT, first_seen TEXT, updated TEXT, source TEXT, status TEXT, deleted_on TEXT, reason TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, day TEXT, kind TEXT, uid TEXT, name TEXT, machine TEXT, detail TEXT)')
    return c


EV_BUF, EV_LOCK = [], threading.Lock()
KIND_LABEL = {'TRANSFER': 'Enrollment transferred', 'BACKUP': 'Backup saved / updated', 'DELETE': 'Deleted', 'RESTORE': 'Restored from backup'}
KIND_FILTER = {'All': None, 'Transfers': ['TRANSFER'], 'Deletions': ['DELETE'], 'Backups': ['BACKUP'], 'Restores': ['RESTORE']}


def ev(kind, uid='', name='', machine='', detail=''):
    now = datetime.now()
    with EV_LOCK: EV_BUF.append((now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d'), kind, str(uid), name or '', machine, detail))


def flush_events():
    with EV_LOCK: rows, EV_BUF[:] = list(EV_BUF), []
    if not rows: return
    try:
        c = db(); c.executemany('INSERT INTO events (ts, day, kind, uid, name, machine, detail) VALUES (?,?,?,?,?,?,?)', rows); c.commit(); c.close()
    except Exception as e:
        log(f'report database error: {e}')
        with EV_LOCK: EV_BUF[:0] = rows


def save_backup(u, t, source):
    """Keep / update one employee in the backup. t = {'fp': [(finger no, data)], 'face': (data, length) or None}. Never loses stored data: new + old are merged.
    -> 'new' | 'updated' | 'same'"""
    c = db()
    try:
        row = c.execute('SELECT name, priv, pw, card, fp, face, status FROM users WHERE id=?', (u['id'],)).fetchone()
        fp = {int(f): d for f, d in (json.loads(row[4]) if row and row[4] else [])}
        fp.update({int(f): d for f, d in t['fp']})
        face = t['face'] or (json.loads(row[5]) if row and row[5] else None)
        card = u.get('card') or (row[3] if row else '') or ''
        new = (u['name'], int(u.get('priv') or 0), u.get('pw') or '', str(card), json.dumps(sorted(fp.items())), json.dumps(face) if face else '')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if row and tuple(row[:6]) == new and row[6] == 'active': return 'same'
        if row:
            c.execute('UPDATE users SET name=?, priv=?, pw=?, card=?, fp=?, face=?, updated=?, source=?, status="active", deleted_on=NULL, reason=NULL WHERE id=?', new + (now, source, u['id']))
        else:
            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,"active",NULL,NULL)', (u['id'],) + new + (now, now, source))
        c.commit()
        bits = [f'{len(fp)} fingerprint(s)' if fp else '', 'face' if face else '', 'RFID card' if card else '']
        ev('BACKUP', u['id'], u['name'], source, ('new: ' if not row else 'updated: ') + (', '.join(b for b in bits if b) or 'user data only'))
        return 'updated' if row else 'new'
    finally:
        c.close()


def mark_deleted(uid, reason):
    try:
        c = db(); c.execute('UPDATE users SET status="deleted", deleted_on=?, reason=? WHERE id=? AND status="active"', (date.today().isoformat(), reason, uid)); c.commit(); c.close()
    except Exception as e:
        log(f'backup database error: {e}')


def backup_ids():
    c = db()
    try: return {r[0] for r in c.execute('SELECT id FROM users')}
    finally: c.close()


def backup_stats():
    c = db()
    try:
        n, f, fc, cd, last = c.execute("SELECT COUNT(*), SUM(fp != '[]' AND fp != ''), SUM(face != ''), SUM(card != '' AND card != '0'), MAX(updated) FROM users").fetchone()
        return n or 0, f or 0, fc or 0, cd or 0, last or '-'
    finally:
        c.close()


def query_events(d1, d2, kinds=None):
    c = db()
    try:
        sql, args = 'SELECT ts, kind, uid, name, machine, detail FROM events WHERE day >= ? AND day <= ?', [d1.isoformat(), d2.isoformat()]
        if kinds: sql += ' AND kind IN (%s)' % ','.join('?' * len(kinds)); args += kinds
        return c.execute(sql + ' ORDER BY ts', args).fetchall()
    finally:
        c.close()


def export_report(path, d1, d2, kinds=None):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Activity'
    ws.append(['Date', 'Time', 'Type', 'Employee ID', 'Name', 'Machine', 'Details'])
    rows = query_events(d1, d2, kinds)
    for ts, kind, uid, name, mach, det in rows: ws.append([ts[:10], ts[11:], KIND_LABEL.get(kind, kind), uid, name, mach, det])
    sm = wb.create_sheet('Summary'); sm.append(['Date', 'Type', 'Count'])
    cnt = {}
    for r in rows: cnt[(r[0][:10], r[1])] = cnt.get((r[0][:10], r[1]), 0) + 1
    for (day, kind), n in sorted(cnt.items()): sm.append([day, KIND_LABEL.get(kind, kind), n])
    for w in (ws, sm):
        for col, wd in zip('ABCDEFG', (12, 10, 26, 14, 28, 18, 60)): w.column_dimensions[col].width = wd
    wb.save(path); return len(rows)


def export_backup_xlsx(path):
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Backup'
    ws.append(['Employee ID', 'Name', 'RFID card', 'Fingerprints', 'Face', 'First backed up', 'Last updated', 'Status', 'Deleted on', 'Reason'])
    c = db()
    try:
        for r in c.execute('SELECT id, name, card, fp, face, first_seen, updated, status, deleted_on, reason FROM users ORDER BY id'):
            ws.append([r[0], r[1], r[2] if r[2] not in ('', '0') else '', len(json.loads(r[3])) if r[3] else 0, 'Yes' if r[4] else 'No', r[5], r[6], r[7], r[8] or '', r[9] or ''])
    finally:
        c.close()
    wb.save(path)


def make_backup_zip(path):
    """Zip with the full backup database (all templates) + a readable Excel list."""
    tmp = tempfile.mkdtemp()
    dbf, xl = os.path.join(tmp, 'enroll_backup.db'), os.path.join(tmp, 'backup_users.xlsx')
    src = db(); dst = sqlite3.connect(dbf)
    try: src.backup(dst)
    finally: dst.close(); src.close()
    export_backup_xlsx(xl)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z: z.write(dbf, 'enroll_backup.db'); z.write(xl, 'backup_users.xlsx')
    return os.path.getsize(path)


# ---------------------------------------------------------------- e-mail (daily activity report + backup)
def _smtp_login():
    """Connect to the sender account (Gmail / Outlook ...) and log in with the saved sender e-mail + password -> server object."""
    if not (cfg['mail_server'] and cfg['mail_user'] and cfg['mail_pass']): raise ValueError('enter the sender e-mail settings (server, e-mail, password)')
    port, ctx = int(cfg['mail_port']), ssl.create_default_context()
    s = smtplib.SMTP_SSL(cfg['mail_server'], port, timeout=90, context=ctx) if port == 465 else smtplib.SMTP(cfg['mail_server'], port, timeout=90)
    try:
        if port != 465: s.starttls(context=ctx)
        pw = cfg['mail_pass'].replace(' ', '') if any(k in cfg['mail_server'].lower() for k in ('gmail', 'google')) else cfg['mail_pass']   # Google shows App passwords in groups with spaces
        try: s.login(cfg['mail_user'].strip(), pw)
        except smtplib.SMTPAuthenticationError: raise ValueError('the mail server refused the login - check the sender e-mail and password (Gmail needs a 16-letter App password, not the normal password)')
    except Exception:
        try: s.quit()
        except Exception: pass
        raise
    return s


def send_mail(subject, body, attachments, to=None):
    """Logs in to the sender account with the saved e-mail + password and sends. No 'Send to' address = the sender's own address."""
    to = to or [x for x in re.split(r'[;,\s]+', cfg['mail_to']) if x] or [cfg['mail_user'].strip()]
    s = _smtp_login()
    try:
        msg = EmailMessage(); msg['From'], msg['To'], msg['Subject'] = cfg['mail_user'].strip(), ', '.join(to), subject; msg.set_content(body)
        for name, data in attachments: msg.add_attachment(data, maintype='application', subtype='octet-stream', filename=name)
        s.send_message(msg)
    finally:
        try: s.quit()
        except Exception: pass


def daily_mail():
    """Send today's activity report + the backup. Raises on any problem."""
    flush_events(); day = date.today(); tmp = tempfile.mkdtemp()
    rep = os.path.join(tmp, f'Activity_Report_{day:%Y-%m-%d}.xlsx'); n = export_report(rep, day, day)
    zp = os.path.join(tmp, f'Backup_{day:%Y-%m-%d}.zip'); size = make_backup_zip(zp)
    rows = query_events(day, day); cnt = lambda k: sum(1 for r in rows if r[1] == k)
    nb, fpn, fcn, cdn, last = backup_stats()
    body = (f'Enroll Sync - daily report {day:%d %b %Y}\n\nEnrollments transferred: {cnt("TRANSFER")}\nDeletions: {cnt("DELETE")}\nBackup entries saved / updated: {cnt("BACKUP")}\n\n'
            f'Backup now holds {nb} employees ({fpn} with fingerprints, {fcn} with face, {cdn} with RFID card).\n')
    atts = [(os.path.basename(rep), open(rep, 'rb').read())]
    if size <= 20 * 1024 * 1024: atts.append((os.path.basename(zp), open(zp, 'rb').read()))
    else: body += f'\nThe backup file is {size // 1048576} MB - too big to attach. It is in the backup folder: {os.path.dirname(db_path())}\n'
    send_mail(f'Enroll Sync daily report {day:%d %b %Y}', body, atts)
    return n


def parse_day(s):
    for f in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y'):
        try: return datetime.strptime(s.strip(), f).date()
        except ValueError: pass
    raise ValueError(f'"{s}" is not a date (use dd-mm-yyyy)')


# ---------------------------------------------------------------- employee list (link -> ID + service end date)
LIST = {'emp': {}, 'time': '-', 'result': 'No employee list loaded yet', 'next': 0, 'cols': '', 'rows': 0, 'bad': 0, 'refused': None}
REG = {'file': ''}                                 # the attendance register file saved by the last download
ID_WORDS = ('employeeid', 'employee id', 'emp id', 'empid', 'emp code', 'employee code', 'emp no', 'employee no', 'emp. id', 'staff id', 'personnel no')
END_WORDS = ('serviceenddate', 'service end', 'end of service', 'end date', 'last working', 'leaving', 'resign', 'termination', 'separation', 'left date', 'exit date', 'last day')
DATE_FORMATS = ('%d-%b-%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y', '%d %b %Y', '%d-%b-%y', '%d/%m/%y', '%d-%m-%y', '%Y/%m/%d', '%d %B %Y', '%b %d, %Y')


class _Html(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows, self.row, self.cell = [], None, None
    def handle_starttag(self, t, a):
        if t == 'tr': self.row = []
        elif t in ('td', 'th') and self.row is not None: self.cell = []
    def handle_data(self, d):
        if self.cell is not None: self.cell.append(d)
    def handle_endtag(self, t):
        if t in ('td', 'th') and self.cell is not None and self.row is not None: self.row.append(' '.join(''.join(self.cell).split())); self.cell = None
        elif t == 'tr' and self.row is not None: self.rows.append(self.row); self.row = None


def read_sheets(raw):
    """File bytes (.xlsx, .xls binary, .xls that is really HTML, or .csv) -> list of sheets, each a list of rows."""
    if raw[:2] == b'PK':
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        return [[list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets]
    if raw[:4] == b'\xd0\xcf\x11\xe0':
        import xlrd
        wb = xlrd.open_workbook(file_contents=raw)
        return [[[xlrd.xldate_as_datetime(c.value, wb.datemode) if c.ctype == 3 else c.value for c in ws.row(i)] for i in range(ws.nrows)] for ws in wb.sheets()]
    try: text = raw.decode('utf-8-sig')
    except UnicodeDecodeError: text = raw.decode('cp1252', 'replace')
    if '<table' in text.lower():
        h = _Html(); h.feed(text); return [h.rows]
    try: dialect = csv.Sniffer().sniff(text[:4000], delimiters=',;\t|')
    except csv.Error: dialect = csv.excel
    return [list(csv.reader(io.StringIO(text), dialect))]


def parse_date(v):
    """-> date, or None if empty / not a readable date (day first: 05/11/2026 = 5 November)."""
    if v is None or v == '': return None
    if isinstance(v, datetime): return v.date()
    if isinstance(v, date): return v
    if isinstance(v, (int, float)) and 20000 < v < 80000: return (datetime(1899, 12, 30) + timedelta(days=float(v))).date()
    t = str(v).strip()
    for cand in (t, t.split(' ')[0], t.split('T')[0]):
        for f in DATE_FORMATS:
            try: return datetime.strptime(cand, f).date()
            except ValueError: pass
    return None


def parse_list(raw):
    """-> ({normalised ID: end date or None}, info text, rows with an unreadable end date). Raises ValueError if the columns are not found."""
    for rows in read_sheets(raw):
        for i, row in enumerate(rows[:25]):
            h = [str(c if c is not None else '').strip().lower() for c in row]
            idc = next((j for j, t in enumerate(h) if t in ('id', 'code', 'emp') or any(k in t for k in ID_WORDS)), None)
            endc = next((j for j, t in enumerate(h) if any(k in t for k in END_WORDS)), None)
            if idc is None or endc is None or idc == endc: continue
            emp, bad = {}, 0
            for r in rows[i + 1:]:
                if idc >= len(r) or r[idc] in (None, ''): continue
                k = norm(r[idc]); raw_end = r[endc] if endc < len(r) else None
                e = parse_date(raw_end)
                if e is not None and e.year <= 1900: e = None                          # 01/01/1900 = no end date = still in service
                elif e is None and raw_end not in (None, '') and not (isinstance(raw_end, (int, float)) and raw_end < 100): bad += 1
                emp[k] = e
            if emp: return emp, f'ID column "{row[idc]}", end date column "{row[endc]}"', bad
    raise ValueError('could not find an Employee ID column and a service end date column in the file')


class _Form(HTMLParser):
    """The fields of an ASP.NET page: inputs (with the text next to each checkbox), selects, the form action."""
    def __init__(self):
        super().__init__(); self.inputs, self.selects, self.action = [], [], None
        self._labels, self._for, self._pending, self._sel = {}, None, None, None
        self._opt, self.links, self._link = False, [], None
    def handle_starttag(self, t, a):
        a = {k: (v if v is not None else '') for k, v in a}
        if t == 'form' and self.action is None: self.action = a.get('action', '')
        elif t == 'input': self.inputs.append(dict(a, type=a.get('type', 'text').lower(), text='', checked='checked' in a)); self._pending = len(self.inputs) - 1
        elif t == 'label': self._for, self._pending = a.get('for'), None
        elif t == 'select': self._sel = {'name': a.get('name', ''), 'options': [], 'texts': []}; self.selects.append(self._sel)
        elif t == 'option' and self._sel is not None: self._sel['options'].append((a.get('value', ''), 'selected' in a)); self._sel['texts'].append(''); self._opt = True
        elif t == 'button': self.inputs.append(dict(a, type=a.get('type', 'submit').lower(), text='', checked=False)); self._pending = len(self.inputs) - 1
        elif t == 'a': self._link = {'text': '', 'href': a.get('href', ''), 'onclick': a.get('onclick', '')}; self.links.append(self._link)
    def handle_data(self, d):
        d = d.strip()
        if not d: return
        if self._opt and self._sel is not None: self._sel['texts'][-1] = (self._sel['texts'][-1] + ' ' + d).strip(); return
        if self._link is not None: self._link['text'] = (self._link['text'] + ' ' + d).strip()
        if self._for: self._labels[self._for] = (self._labels.get(self._for, '') + ' ' + d).strip()
        elif self._pending is not None: self.inputs[self._pending]['text'] = d; self._pending = None
    def handle_endtag(self, t):
        if t == 'label': self._for = None
        elif t == 'option': self._opt = False
        elif t == 'a': self._link = None
        elif t == 'select': self._sel = None; self._opt = False
    def done(self):
        for i in self.inputs:
            if not i['text']: i['text'] = self._labels.get(i.get('id', ''), '')
        return self


def parse_form(html):
    f = _Form(); f.feed(html); return f.done()


def form_data(f, skip_types=('checkbox', 'radio', 'submit', 'image', 'button', 'reset', 'file'), override=None):
    """Hidden / text / select values of the form, as the browser would send them."""
    out = [(i['name'], i.get('value', '')) for i in f.inputs if i.get('name') and i['type'] not in skip_types]
    for sel in f.selects:
        if sel['name'] and sel['options']: out.append((sel['name'], next((v for v, on in sel['options'] if on), sel['options'][0][0])))
    out += [(i['name'], i.get('value', 'on')) for i in f.inputs if i.get('name') and i['type'] == 'radio' and i['checked']]
    if override:
        out = [(k, override.get(k, v)) for k, v in out]; have = {k for k, _ in out}; out += [(k, v) for k, v in override.items() if k not in have]
    return out


def press(f, words, exact=None):
    """The button to press -> form fields to send. `exact` = its caption, so 'Get Report' is not mixed up with 'Get Report List'."""
    cap = lambda i: ' '.join((i.get('value', '') + ' ' + i['text']).lower().split())
    subs = [i for i in f.inputs if i['type'] in ('submit', 'image') and i.get('name')]
    b = (next((i for i in subs if exact and cap(i) == exact), None) or next((i for i in subs if any(w in cap(i) for w in words) and 'list' not in cap(i)), None)
         or next((i for i in subs if any(w in cap(i) for w in words)), None))
    if not b:
        for l in f.links:                                                         # a link that does an ASP.NET postback
            m = re.search(r"__doPostBack\('([^']*)'\s*,\s*'([^']*)'", l['href'] + ' ' + l['onclick'])
            if m and any(w in l['text'].lower() for w in words): return [('__EVENTTARGET', m.group(1)), ('__EVENTARGUMENT', m.group(2))]
        b = subs[0] if subs else None
    if not b: return []
    return [(b['name'] + '.x', '1'), (b['name'] + '.y', '1')] if b['type'] == 'image' else [(b['name'], b.get('value', ''))]


def with_event(data, extra):
    """A postback event (__EVENTTARGET ...) replaces the empty hidden one of the form."""
    keys = {k for k, _ in extra if k.startswith('__EVENT')}
    return [(k, v) for k, v in data if k not in keys] + extra


def group_of(name): return re.sub(r'\$\d+$', '', name)


def report_checks(f):
    """The Decibel report form as in the screenshot: fields Emp Id + Service End Date + Export To Excel ticked, every other field unticked;
    ALL service statuses and ALL grades ticked so that leavers (Resigned, Terminated ...) are included. Anything else keeps its default."""
    boxes = [i for i in f.inputs if i['type'] == 'checkbox' and i.get('name')]
    text = lambda i: ' '.join(i['text'].lower().split())               # also 'Emp&nbsp;Id'
    find = lambda label: next((group_of(i['name']) for i in boxes if text(i) == label), None)
    g_status, g_grade, g_field = find('in service'), find('eg1'), find('emp id')
    if not g_field: raise ValueError(f'the "Emp Id" field was not found on the report page ({len(boxes)} tick boxes seen: ' + ', '.join((text(i) or i["name"][-18:]) for i in boxes[:8]) + ') - the page was saved as last_report_page.html in the EnrollSync settings folder')
    out = []
    for i in boxes:
        t, g = text(i), group_of(i['name'])
        if t == 'select all': continue
        if t == 'export to excel': on = True
        elif g == g_field: on = t in ('emp id', 'service end date')
        elif g in (g_status, g_grade): on = True
        else: on = i['checked']
        if on: out.append((i['name'], i.get('value') or 'on'))
    if not any(t == 'service end date' for t in map(text, boxes)): raise ValueError('report form changed: the "Service End Date" field was not found')
    return out


# ---------------------------------------------------------------- Decibel session: the SAME method as the kiosk's Work Hour / Leave Balance download
# (plain regex form reader, log in with the form the site shows, press the report page's own buttons, keep the cookies)
class LoginFailed(ValueError):
    pass


_DC_TAG = re.compile(r'<(/?)(form|input|select|option|textarea|button)\b((?:"[^"]*"|\'[^\']*\'|[^\'">])*)>', re.I)
_DC_ATTR = re.compile(r'([\w:.-]+)(?:\s*=\s*("[^"]*"|\'[^\']*\'|[^\s"\'>]+))?')


def _dc_attrs(s):
    out = {}
    for m in _DC_ATTR.finditer(s):
        v = m.group(2)
        out[m.group(1).lower()] = htmllib.unescape(v[1:-1] if v and v[0] in '"\'' else v) if v is not None else ''
    return out


def _dc_forms(page):
    """Forms of an HTML page as [{'action', 'els': [...]}]."""
    forms, f, sel = [], None, None
    ms = list(_DC_TAG.finditer(page))
    for k, m in enumerate(ms):
        close, tag, a = m.group(1), m.group(2).lower(), _dc_attrs(m.group(3))
        nxt = ms[k + 1].start() if k + 1 < len(ms) else len(page)
        if close:
            if tag == 'select': sel = None
            elif tag == 'form': f = None
            continue
        if tag == 'form':
            f = {'action': a.get('action', ''), 'els': []}; forms.append(f)
        elif f is None:
            continue
        elif tag == 'input':
            t, v = (a.get('type') or 'text').lower(), a.get('value')
            f['els'].append({'t': t, 'n': a.get('name'), 'v': ('on' if v is None and t in ('checkbox', 'radio') else v or ''), 'c': 'checked' in a, 'dis': 'disabled' in a, 'id': a.get('id', ''), 'oc': a.get('onclick', '')})
        elif tag == 'button':
            f['els'].append({'t': (a.get('type') or 'submit').lower(), 'n': a.get('name'), 'v': a.get('value', ''), 'c': False, 'dis': 'disabled' in a, 'id': a.get('id', ''), 'oc': a.get('onclick', ''), 'x': ' '.join(htmllib.unescape(page[m.end():nxt].split('<', 1)[0]).split())})
        elif tag == 'select':
            sel = {'t': 'select', 'n': a.get('name'), 'opts': [], 'dis': 'disabled' in a}; f['els'].append(sel)
        elif tag == 'option' and sel is not None:
            text = htmllib.unescape(page[m.end():nxt].split('<', 1)[0])
            sel['opts'].append([a['value'] if 'value' in a else text.strip(), text, 'selected' in a])
        elif tag == 'textarea':
            f['els'].append({'t': 'textarea', 'n': a.get('name'), 'v': htmllib.unescape(page[m.end():nxt].split('<', 1)[0]), 'dis': 'disabled' in a})
    return forms


def _dc_has_login(page, url=''):
    """Is this the LOGIN page? Logged-in Decibel pages also carry a hidden 'Change Password' box (New / Re-Type password), so a password box alone does not mean login:
    the report page itself never counts, and a page with several password boxes is a login page only when its address says login."""
    for f in _dc_forms(page):
        pws = [e for e in f['els'] if e['t'] == 'password']
        if not pws: continue
        names = ' '.join((e.get('n') or '') for e in f['els']).lower()
        if 'btn_getreport' in names or 'ddl_companyname' in names: continue          # the report page (with its hidden Change Password box)
        if len(pws) == 1 or 'login' in url.lower(): return True
    return False


def _dc_plain(page):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', page, flags=re.S | re.I)
    return ' '.join(htmllib.unescape(re.sub(r'<[^>]+>', ' ', t)).split())


def _dc_payload(form, over=None, button=None):
    """What a browser would send for this form: hidden / text fields, ticked boxes, the selected option of every list; `over` {name: value | None} changes or
    removes fields; `button` = name of the submit button that was pressed."""
    out = []
    for e in form['els']:
        n, t = e.get('n'), e['t']
        if not n or e.get('dis'): continue
        if t in ('submit', 'button', 'image', 'reset', 'file'):
            if t in ('submit', 'image') and n == button: out += [(n + '.x', '1'), (n + '.y', '1')] if t == 'image' else [(n, e['v'])]
            continue
        if t in ('checkbox', 'radio'):
            if e['c']: out.append((n, e['v']))
        elif t == 'select':
            sel = next((o for o in e['opts'] if o[2]), e['opts'][0] if e['opts'] else None)
            if sel: out.append((n, sel[0]))
        else:
            out.append((n, e['v']))
    for n, v in (over or {}).items():
        out = [(a, b) for a, b in out if a != n]
        if v is not None: out.append((n, v))
    return out


def _dc_option(form, name, want=None, text=None):
    """(list name, option value) of the list whose name ends with `name`: the option whose value == want or whose text contains `text`. Option None = not in the list."""
    for e in form['els']:
        if e['t'] == 'select' and e.get('n') and e['n'].lower().endswith(name.lower()):
            for v, tx, _ in e['opts']:
                if (want is not None and v == str(want)) or (text and text in ' '.join(tx.lower().split())): return e['n'], v
            return e['n'], None
    return None, None


def _dc_find_option(form, text):
    """Any list that has an option containing `text` (used when the list's name is not what was expected) -> (list name, option value)."""
    for e in form['els']:
        if e['t'] == 'select' and e.get('n'):
            for v, tx, _ in e['opts']:
                if text in ' '.join(tx.lower().split()): return e['n'], v
    return None, None


def _dc_name(form, suffix): return next((e['n'] for e in form['els'] if e.get('n') and e['n'].lower().endswith(suffix.lower())), None)


_DC_A = re.compile(r'<a\b((?:"[^"]*"|\'[^\']*\'|[^\'">])*)>(.*?)</a>', re.I | re.S)
_DC_PB = re.compile(r"__doPostBack\(\s*['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]*)['\"]")
_DC_GOOD = ('login', 'log in', 'sign in', 'signin')
_DC_BAD = ('forgot', 'otp', 'cancel', 'reset', 'change', 'send', 'disclaimer', 'privacy', 'close', 'register')


def _dc_with_event(data, extra):
    """A postback event (__EVENTTARGET ...) replaces the empty hidden one of the form."""
    keys = {k for k, _ in extra if k.startswith('__EVENT')}
    return [(k, v) for k, v in data if k not in keys] + extra


def _dc_login_actions(page, form):
    """What can 'press Login' on this page, best first -> [(label, fields to send)]: a button that says Login, the first submit button, a postback link that
    says Login, a control named *login*. Forgot Password / Send OTP / Cancel are never used."""
    acts, seen = [], set()
    def add(label, fields):
        if tuple(fields) not in seen: seen.add(tuple(fields)); acts.append((label, fields))
    has = lambda c, ws: any(w in c for w in ws)
    cap = lambda e: ' '.join((e.get('n') or '', e.get('id', ''), e.get('v') or '', e.get('x', ''))).lower()
    def pb(text):
        m = _DC_PB.search(text or '')
        return [('__EVENTTARGET', m.group(1)), ('__EVENTARGUMENT', m.group(2))] if m else None
    def fields_of(e):
        return pb(e.get('oc')) or ([(e['n'] + '.x', '1'), (e['n'] + '.y', '1')] if e['t'] == 'image' else [(e['n'], e['v'])])
    btns = [e for e in form['els'] if e['t'] in ('submit', 'image', 'button') and e.get('n') and not e.get('dis')]
    for e in btns:
        if has(cap(e), _DC_GOOD) and not has(cap(e), _DC_BAD): add(f'button {e["n"].split("$")[-1]}', fields_of(e))
    for e in btns:
        if e['t'] in ('submit', 'image') and not has(cap(e), _DC_BAD): add(f'button {e["n"].split("$")[-1]}', fields_of(e)); break
    for m in _DC_A.finditer(page):
        at = _dc_attrs(m.group(1)); text = ' '.join(htmllib.unescape(re.sub(r'<[^>]+>', ' ', m.group(2))).split()); c = (text + ' ' + at.get('id', '')).lower()
        ev = pb(at.get('href', '') + ' ' + at.get('onclick', ''))
        if ev and has(c, _DC_GOOD) and not has(c, _DC_BAD): add(f'link {text or at.get("id")}', ev)
    for e in form['els']:
        n = e.get('n') or ''
        if 'login' in n.lower() and e['t'] not in ('text', 'password', 'hidden', 'email', 'checkbox', 'radio', 'select', 'textarea') and not has(n.lower(), _DC_BAD):
            add(f'event {n.split("$")[-1]}', [('__EVENTTARGET', n), ('__EVENTARGUMENT', '')])
    return acts


def _dc_controls(page):
    """Short list of the controls of a page (no values, no secrets) - shown when the login fails, so the page can be understood."""
    out = []
    for f in _dc_forms(page):
        for e in f['els']:
            if e['t'] == 'hidden': continue
            nm = (e.get('n') or e.get('id') or '?').split('$')[-1]
            out.append(f'{e["t"]}:{nm}' + (f'="{e.get("v") or e.get("x")}"' if e['t'] in ('submit', 'button', 'image') and (e.get('v') or e.get('x')) else ''))
    for m in _DC_A.finditer(page):
        at = _dc_attrs(m.group(1)); ev = _DC_PB.search(at.get('href', '') + ' ' + at.get('onclick', ''))
        if ev: out.append(f'link:{" ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split()) or at.get("id", "?")}->{ev.group(1).split("$")[-1]}')
    return ', '.join(out[:30])


def _dc_date(d, existing=''):
    """The date as the page writes it (same pattern as the value already in the box); default 'November 23, 2026'."""
    t = (existing or '').strip()
    for f in ('%d-%b-%Y', '%d %b %Y', '%Y-%m-%d', '%b %d, %Y'):
        try:
            datetime.strptime(t, f); return d.strftime(f)
        except ValueError: pass
    return f'{MONTHS[d.month - 1]} {d.day}, {d.year}'


class DcSession:
    def __init__(self, user, pw):
        self.user, self.pw, self.url, self.page, self.after_login, self.tried = user, pw, '', '', '', []
        self.jar, self.insecure = http.cookiejar.CookieJar(), False
        self._mk(True)

    def _mk(self, verify):
        """verify=False only for the Decibel site itself, when this PC cannot verify its certificate chain (server sends an incomplete chain / company proxy)."""
        ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), urllib.request.HTTPSHandler(context=ctx))
        self.op.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) EnrollSync')]

    def go(self, url, fields=None):
        """GET (fields=None) or POST; returns (headers, body bytes). Redirects are followed; self.url = final address."""
        data = urllib.parse.urlencode(fields).encode('utf-8') if fields is not None else None
        try:
            with self.op.open(urllib.request.Request(url, data=data), timeout=120) as r:
                self.url, body, hd = r.geturl(), r.read(), r.headers
        except Exception as e:
            host = (urllib.parse.urlparse(url).hostname or '').lower()
            if 'CERTIFICATE_VERIFY_FAILED' in str(e) and host.endswith('mydecibel.com') and not self.insecure:
                self.insecure = True; self._mk(False)                          # certificate chain not verifiable on this PC: retry once for the Decibel host only
                with self.op.open(urllib.request.Request(url, data=data), timeout=120) as r:
                    self.url, body, hd = r.geturl(), r.read(), r.headers
            else: raise
        ctype, disp = hd.get('Content-Type', '').lower(), hd.get('Content-Disposition', '').lower()
        if 'text/html' in ctype and 'attachment' not in disp:
            enc = re.search(r'charset=([\w-]+)', ctype)
            self.page = body.decode(enc.group(1) if enc else 'utf-8', 'replace')
        return hd, body

    def login_on(self):
        """Sign in on the login page now shown: the User ID and Password go in, then the page's Login control is pressed (button, postback link ...). Each control is tried
        only once (a wrong password is never sent twice through the same button). True = the login page is gone."""
        login_form = lambda: next((f for f in _dc_forms(self.page) if any(e['t'] == 'password' for e in f['els'])), None)
        form = login_form()
        if form is None: return True
        acts = _dc_login_actions(self.page, form)
        if not acts: raise LoginFailed('the login page has no Login button / link that could be found')
        for label, fields in acts:
            form = login_form()
            if form is None: return True
            els = form['els']
            pw = next(i for i, e in enumerate(els) if e['t'] == 'password')
            usr = next((e for e in reversed(els[:pw]) if e['t'] in ('text', 'email', 'tel') and e.get('n')), None)
            if usr is None: raise LoginFailed('login form not recognised (no User ID box)')
            base = _dc_payload(form, {usr['n']: self.user, els[pw]['n']: self.pw})
            self.go(urllib.parse.urljoin(self.url, form['action']), _dc_with_event(base, fields))
            self.after_login = self.page; self.tried.append(label)
            if not _dc_has_login(self.page, self.url): return True
        return False


LOGIN_URL = 'https://bpo.mydecibel.com/login.aspx'
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
COMPANY_WORD = 'service tyre'                      # the company to pick: "Service Tyres Private Limited"


ALT_HOST = 'https://mydecibel.com'                 # the main Decibel site (the kiosk's login page): second way in if the HRMS portal login cannot be used


def decibel_download(url, user, pw, login_url=''):
    """The attendance register, through the address given; if the login there is refused, through the same page on the main Decibel site."""
    try: return _decibel_browser(url, user, pw)                                    # 1) real browser (hidden Edge / Chrome) - the most reliable way
    except BrowserUnavailable as e: log(f'Browser method not available ({e}) - using the direct method instead')
    alt = re.sub(r'^https?://[^/]+', ALT_HOST, url)                                # 2) fallback: direct method (no browser needed)
    urls = [url] + ([alt] if alt != url else []); errs = []
    for i, u in enumerate(urls):
        try: return _decibel_register(u, user, pw, login_url)
        except LoginFailed as e: errs.append(f'[{urllib.parse.urlparse(u).netloc}] {e}')
        except Exception as e:
            if i == 0: raise
            errs.append(f'[{urllib.parse.urlparse(u).netloc}] {e}')
    raise LoginFailed(' || '.join(errs))


def _decibel_register(url, user, pw, login_url=''):
    """Log in to Decibel, open the attendance register page, pick the company (Service Tyres Private Limited), put today in From and To,
    press Get Report and return what Decibel sends back (the register: Excel file or table)."""
    def dump(name, content):                                                       # what Decibel really sent, for diagnosis
        try:
            with open(os.path.join(APP, name), 'wb') as f: f.write(content if isinstance(content, bytes) else content.encode('utf-8', 'replace'))
        except Exception: pass
    if not (user and pw): raise ValueError('enter the Decibel User ID and Password in the Data window')
    ses = DcSession(user, pw)
    ses.go(url)
    if _dc_has_login(ses.page, ses.url):                                           # not signed in: use the login page the site shows (each Login control once)
        dump('last_login_page.html', ses.page); controls = _dc_controls(ses.page)
        dump('last_login_controls.txt', f'{ses.url}\n{controls}')
        ok = ses.login_on()
        if ok: ses.go(url)
        if not ok or _dc_has_login(ses.page, ses.url):
            dump('last_login.html', ses.after_login or ses.page)
            m = re.search(r'.{0,80}(invalid|incorrect|wrong|not correct|captcha|locked|expired|blocked|inactive|does not exist|disabled|authenticat).{0,120}', _dc_plain(ses.after_login or ses.page).split('Change Password')[0], re.I)
            raise LoginFailed(('Decibel did not accept the login' if not ok else 'Decibel accepted the login but asked for it again on the report page (session not kept)')
                              + (f' (Decibel says: {m.group(0).strip()})' if m else '') + f'. Pressed: {", ".join(ses.tried) or "nothing"}. Login page controls: {controls}')
    elif not any(_dc_name(f, 'btn_GetReport') for f in _dc_forms(ses.page)) and login_url:
        ses.go(login_url)
        if ses.login_on(): ses.go(url)
    report = lambda: next((f for f in _dc_forms(ses.page) if _dc_name(f, 'btn_GetReport')), None)
    form = report()
    if not form:
        dump('last_report_page.html', ses.page)
        hint = ' Decibel may be asking for a NEW PASSWORD (Change Password): log in once in the browser, change it, then type the new password in the Data window.' if 'change password' in _dc_plain(ses.page).lower() else ''
        raise ValueError('Attendance Register page not recognised (the Get Report button was not found) - saved as last_report_page.html in the EnrollSync settings folder.' + hint)
    action = urllib.parse.urljoin(ses.url, form['action'])
    n, cv = _dc_option(form, 'ddl_CompanyName', text=COMPANY_WORD)                 # 1) company: the page may reload itself when it changes
    if n is None or cv is None: n, cv = _dc_find_option(form, COMPANY_WORD)
    if n is None or cv is None:
        dump('last_report_page.html', ses.page); raise ValueError('company "Service Tyres Private Limited" not in the list of the register page')
    try:
        ses.go(action, _dc_payload(form, {n: cv, '__EVENTTARGET': n, '__EVENTARGUMENT': ''}))
        f2 = report()
        if f2: form, action = f2, urllib.parse.urljoin(ses.url, f2['action'])      # (if the reload failed, the first form is simply used)
    except Exception: pass
    today = date.today()
    over = {'__EVENTTARGET': '', '__EVENTARGUMENT': '', n: cv}
    ex = _dc_name(form, 'cb_ExportToExcel')
    if ex: over[ex] = 'on'
    dated = False                                                                  # 2) From / To = today (text boxes tb_CheckIn / tb_CheckOut, or day / month / year lists)
    for suf in ('tb_CheckIn', 'tb_CheckOut'):
        e = next((e for e in form['els'] if e.get('n') and e['n'].lower().endswith(suf.lower())), None)
        if e: over[e['n']] = _dc_date(today, e.get('v')); dated = True
    for pre in ('F', 'T'):
        for suf, val in (('Day', today.day), ('Month', today.month), ('Year', today.year)):
            sn, ov = _dc_option(form, f'ddl_{pre}{suf}', want=val)
            if sn and ov is not None: over[sn] = ov; dated = True
    if not dated:
        dump('last_report_page.html', ses.page); raise ValueError('From Date / To Date fields not found on the register page')
    hd, body = ses.go(action, _dc_payload(form, over, _dc_name(form, 'btn_GetReport')))       # 3) Get Report
    if not body.strip() or (b'<table' not in body.lower() and body[:2] != b'PK' and body[:4] != b'\xd0\xcf\x11\xe0' and b',' not in body[:2000]):
        dump('last_download.html', body); raise ValueError('Decibel did not send a register (saved as last_download.html in the EnrollSync settings folder)')
    return body


class BrowserUnavailable(Exception):
    """Selenium / Edge / Chrome cannot be started on this PC -> the old direct method is used instead."""


def _decibel_browser(url, user, pw):
    """Real-browser way (recommended): a hidden Microsoft Edge (Chrome as second choice) opens the Decibel page, types the User ID + Password, logs in exactly like a person,
    picks Service Tyres Private Limited, puts today in From / To, ticks Export To Excel, presses Get Report and takes the downloaded file.
    Because it is a real browser, JavaScript logins / hidden fields / cookies all work. The password is sent ONCE only (a wrong password is never retried)."""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.chrome.service import Service as ChromeService
    except Exception as e: raise BrowserUnavailable(f'selenium is not installed ({e})')
    if not (user and pw): raise ValueError('enter the Decibel User ID and Password in the Data window')
    dl = tempfile.mkdtemp(prefix='decibel_'); drv = None; alerts = []

    def dump(name, content):
        try:
            with open(os.path.join(APP, name), 'wb') as f: f.write(content if isinstance(content, bytes) else content.encode('utf-8', 'replace'))
        except Exception: pass

    def start():
        last = None
        for kind in ('edge', 'chrome'):
            try:
                o = webdriver.EdgeOptions() if kind == 'edge' else webdriver.ChromeOptions()
                svc = EdgeService() if kind == 'edge' else ChromeService()
                for a in ('--headless=new', '--disable-gpu', '--window-size=1400,1000', '--no-sandbox', '--disable-dev-shm-usage'): o.add_argument(a)
                o.add_experimental_option('prefs', {'download.default_directory': dl, 'download.prompt_for_download': False, 'download.directory_upgrade': True,
                                                    'safebrowsing.enabled': False, 'safebrowsing.disable_download_protection': True})
                try: svc.creation_flags = 0x08000000                                   # no black console window
                except Exception: pass
                return (webdriver.Edge if kind == 'edge' else webdriver.Chrome)(options=o, service=svc)
            except Exception as e: last = e
        raise BrowserUnavailable(f'Edge / Chrome could not be started ({str(last).splitlines()[0] if last else "?"})')

    def alert_text():
        try:
            a = drv.switch_to.alert; t = a.text; a.accept(); return t
        except Exception: return ''

    def wait(cond, secs, step=0.5):
        end = time.time() + secs
        while time.time() < end:
            t = alert_text()
            if t: alerts.append(t)
            try:
                v = cond()
                if v: return v
            except Exception: pass
            time.sleep(step)
        return None

    vis = lambda css: [e for e in drv.find_elements(By.CSS_SELECTOR, css) if e.is_displayed()]
    pick = lambda suf: next(iter(drv.find_elements(By.CSS_SELECTOR, f"[id$='{suf}'],[name$='{suf}']")), None)
    on_report = lambda: pick('btn_GetReport') is not None

    def body_text():
        try: return ' '.join(drv.find_element(By.TAG_NAME, 'body').text.split())[:300]
        except Exception: return ''

    def gone(el):
        try: el.tag_name; return False
        except Exception: return True

    try:
        drv = start(); drv.set_page_load_timeout(120)
        drv.get(url); t = alert_text()
        if t: alerts.append(t)
        pws = [] if on_report() else vis('input[type=password]')
        if pws:                                                                       # ---- login page
            if len(pws) > 1: raise LoginFailed('Decibel is asking for a NEW PASSWORD (Change Password): log in once in the browser, change it, then type the new password in the Data window')
            pwe = pws[0]
            users = [e for e in pwe.find_elements(By.XPATH, "preceding::input[@type='text' or @type='email' or @type='tel' or not(@type)]") if e.is_displayed()]
            if not users: raise LoginFailed('login form not recognised (no User ID box)')
            for el, val in ((users[-1], user), (pwe, pw)):
                el.clear(); el.send_keys(val)
            btn = None
            for e in vis('input[type=submit], input[type=button], input[type=image], button, a'):
                cap = ' '.join((e.get_attribute('value') or '', e.text or '', e.get_attribute('id') or '', e.get_attribute('name') or '', e.get_attribute('title') or '')).lower()
                if any(w in cap for w in _DC_GOOD) and not any(w in cap for w in _DC_BAD): btn = e; break
            try: btn.click() if btn else pwe.send_keys(Keys.ENTER)                    # pressed ONCE
            except Exception:
                try: pwe.send_keys(Keys.ENTER)
                except Exception: pass
            if not wait(lambda: not vis('input[type=password]') or on_report(), 40):
                try: drv.save_screenshot(os.path.join(APP, 'last_login.png'))
                except Exception: pass
                raise LoginFailed('Decibel did not accept the login - check the User ID and Password' + (f' (Decibel says: {" ".join(alerts)[:200] or body_text()})' if (alerts or body_text()) else '')
                                  + ' - a screenshot was saved as last_login.png in the EnrollSync settings folder')
            if len(vis('input[type=password]')) > 1: raise LoginFailed('Decibel is asking for a NEW PASSWORD (Change Password): log in once in the browser, change it, then type the new password in the Data window')
            if not on_report(): drv.get(url)                                          # logged in: open the attendance register page
        if not wait(on_report, 25):
            dump('last_report_page.html', drv.page_source)
            try: drv.save_screenshot(os.path.join(APP, 'last_report.png'))
            except Exception: pass
            raise ValueError('Attendance Register page not recognised (the Get Report button was not found) - saved as last_report_page.html / last_report.png in the EnrollSync settings folder')
        co = pick('ddl_CompanyName')                                                  # ---- company
        if co is None: raise ValueError('company list (ddl_CompanyName) not found on the register page')
        sel = Select(co); opt = next((o for o in sel.options if COMPANY_WORD in ' '.join(o.text.lower().split())), None)
        if opt is None: raise ValueError('company "Service Tyres Private Limited" not in the list of the register page')
        if not opt.is_selected():
            sel.select_by_visible_text(opt.text)                                       # the page may reload itself here
            wait(lambda: gone(co), 6); wait(lambda: pick('btn_GetReport') is not None and pick('ddl_CompanyName') is not None, 30)
            s2 = Select(pick('ddl_CompanyName'))
            if COMPANY_WORD not in ' '.join(s2.first_selected_option.text.lower().split()): s2.select_by_visible_text(opt.text)
        today = date.today(); dated = False                                           # ---- From / To = today
        for suf in ('tb_CheckIn', 'tb_CheckOut'):
            e = pick(suf)
            if e is not None:
                drv.execute_script("var e=arguments[0];e.removeAttribute('readonly');e.value=arguments[1];", e, _dc_date(today, e.get_attribute('value'))); dated = True
        for pre in ('F', 'T'):
            for suf, val in (('Day', today.day), ('Month', today.month), ('Year', today.year)):
                e = pick(f'ddl_{pre}{suf}')
                if e is not None:
                    try: Select(e).select_by_value(str(val)); dated = True
                    except Exception: pass
        if not dated:
            dump('last_report_page.html', drv.page_source); raise ValueError('From Date / To Date fields not found on the register page')
        ex = pick('cb_ExportToExcel')
        if ex is not None and not ex.is_selected(): drv.execute_script('arguments[0].checked=true;', ex)
        for f in os.listdir(dl):
            try: os.remove(os.path.join(dl, f))
            except OSError: pass
        drv.execute_script('arguments[0].click();', pick('btn_GetReport'))             # ---- Get Report
        def got():
            fs = [f for f in os.listdir(dl) if not f.lower().endswith(('.crdownload', '.tmp'))]
            return os.path.join(dl, fs[0]) if fs else None
        p = wait(got, 90, 1)
        if p:
            time.sleep(1)
            with open(p, 'rb') as f: body = f.read()
            if body.strip(): return body
        src = drv.page_source                                                         # no file: the register may be shown on the page itself
        if '<table' in src.lower() and any(k in src.lower() for k in ('serviceenddate', 'service end date', 'emp id', 'empid')): return src.encode('utf-8')
        dump('last_download.html', src)
        try: drv.save_screenshot(os.path.join(APP, 'last_report.png'))
        except Exception: pass
        raise ValueError('Decibel did not send a register (page saved as last_download.html / last_report.png in the EnrollSync settings folder)')
    finally:
        try:
            if drv is not None: drv.quit()
        except Exception: pass
        shutil.rmtree(dl, ignore_errors=True)



def fetch_list_bytes(cfg):
    src = cfg['list_url'].strip()
    if not src: raise ValueError('the employee list link is empty')
    if re.match(r'https?://', src, re.I):
        if 'originate.aspx' in src.lower() or 'attendancereport' in src.lower() or cfg.get('dc_user'): return decibel_download(src, cfg.get('dc_user', ''), cfg.get('dc_pass', ''), cfg.get('login_url', ''))
        m = re.match(r'(https://docs\.google\.com/spreadsheets/d/[^/]+)', src)
        if m and 'export' not in src: src = m.group(1) + '/export?format=csv'          # a normal Google Sheets link works too
        req = urllib.request.Request(src, headers={'User-Agent': 'EnrollSync', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=30) as r: return r.read()
    with open(src.strip('"'), 'rb') as f: return f.read()                            # a file on this PC / network folder also works


def apply_list(raw, keep_file=True):
    emp, info, bad = parse_list(raw)
    LIST.update(emp=emp, cols=info, bad=bad, rows=len(emp), time=datetime.now().strftime('%d %b %H:%M'))
    if keep_file:
        with open(LIST_FILE, 'wb') as f: f.write(raw)
    return len(emp)


def save_register(raw):
    """Keep the downloaded attendance register as a file (one per day, replaced by the next download of that day)."""
    ext = '.xlsx' if raw[:2] == b'PK' else '.xls'
    d = os.path.join(APP, 'Register'); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f'Attendance Register {date.today():%Y-%m-%d}{ext}')
    with open(p, 'wb') as f: f.write(raw)
    REG['file'] = p


def refresh_list(cfg, manual=False):
    """Download (or read) the employee list now. On any problem the previous list stays in use. A refused login is not retried by the timer (only by 'Download now')."""
    who = (cfg.get('dc_user', ''), cfg.get('dc_pass', ''))
    if LIST.get('refused') == who and not manual:
        LIST['next'] = time.time() + max(1, int(cfg['list_min'])) * 60; return False
    try:
        raw = fetch_list_bytes(cfg)
        try: n = apply_list(raw)
        except Exception:
            with open(os.path.join(APP, 'last_download.html'), 'wb') as f: f.write(raw)       # what Decibel really sent, for diagnosis
            raise
        LIST['refused'] = None
        if re.match(r'https?://', cfg['list_url'].strip(), re.I):
            try: save_register(raw)
            except OSError as e: log(f'Register file could not be saved ({e})')
        LIST['result'] = f'OK - {n} employees, {len(leavers_now(cfg, True))} with an end date before today'
        log(f'Employee list: {n} employees ({LIST["cols"]})' + (f', {LIST["bad"]} unreadable end dates ignored' if LIST['bad'] else ''))
        LIST['next'] = time.time() + max(1, int(cfg['list_min'])) * 60
        return True
    except Exception as e:
        if isinstance(e, LoginFailed): LIST['refused'] = who
        LIST['result'] = f'FAILED - {e}' + (' (the last good list stays in use)' if LIST['emp'] else '') + (' - the timer will not retry this login; press Download now after correcting it' if isinstance(e, LoginFailed) else '')
        log(f'Employee list: download failed ({e})')
        LIST['next'] = time.time() + 5 * 60                                          # try again in 5 minutes
        return False


def leavers_now(cfg, ignore_switch=False):
    """Normalised IDs whose service end date is before today."""
    if not ignore_switch and not cfg.get('del_leavers', True): return set()
    today = date.today()
    return {k for k, e in LIST['emp'].items() if e and e < today}


def load_cached_list():
    try:
        with open(LIST_FILE, 'rb') as f: apply_list(f.read(), keep_file=False)
        LIST['result'] = 'Saved list from the last run (not downloaded yet)'
    except Exception:
        pass


FACE_INDEX = 50                                   # ZKTeco SDK: face template slot used by the UFace / iFace models


class Dev:
    """One machine through the ZKTeco SDK (COM object zkemkeeper.ZKEM)."""
    def __init__(self, ip, port, key):
        import pythoncom
        pythoncom.CoInitialize(); self._co = pythoncom
        from win32com.client import Dispatch, gencache
        try: self.z = gencache.EnsureDispatch('zkemkeeper.ZKEM')
        except Exception: self.z = Dispatch('zkemkeeper.ZKEM')
        if key: self.z.SetCommPassword(int(key))
        if not self.z.Connect_Net(ip, int(port)): raise RuntimeError('cannot connect (check IP / Comm Key / SDK)')

    def disable(self): self.z.EnableDevice(1, False)
    def enable(self): self.z.EnableDevice(1, True)
    def refresh(self): self.z.RefreshData(1)

    def users(self):
        self.z.ReadAllUserID(1); out = []
        while True:
            r = self.z.SSR_GetAllUserInfo(1)                    # (ok, id, name, password, privilege, enabled)
            if not r[0]: break
            card = ''
            try:
                c = self.z.GetStrCardNumber()                   # RFID card of the user just read: (ok, card)
                card = str(c[1]) if isinstance(c, tuple) and c[0] else ''
            except Exception: pass
            out.append({'id': str(r[1]), 'name': r[2], 'pw': r[3], 'priv': r[4], 'en': r[5], 'card': card})
        return out

    def templates(self, uid):
        """-> {'fp': [(finger index, data)], 'face': (data, length) or None}"""
        fp = []
        for fid in range(10):
            r = self.z.SSR_GetUserTmpStr(1, uid, fid)           # (ok, data, length)
            if r[0] and r[1]: fp.append((fid, r[1]))
        r = self.z.GetUserFaceStr(1, uid, FACE_INDEX, '', 0)    # (ok, data, length)
        return {'fp': fp, 'face': (r[1], r[2]) if r[0] and r[1] else None}

    def set_user(self, u):
        if u.get('card'):
            try: self.z.SetStrCardNumber(str(u['card']))
            except Exception: pass
        if not self.z.SSR_SetUserInfo(1, u['id'], u['name'], u['pw'], u['priv'], u['en']): raise RuntimeError('machine refused the user')
    def set_fp(self, uid, fid, data):
        if not self.z.SSR_SetUserTmpStr(1, uid, fid, data): raise RuntimeError('machine refused the fingerprint')
    def set_face(self, uid, face):
        if not self.z.SetUserFaceStr(1, uid, FACE_INDEX, face[0], face[1]): raise RuntimeError('machine refused the face')
    def delete(self, uid): self.z.SSR_DeleteEnrollData(1, uid, 12)      # 12 = the user with all fingerprints / face

    def close(self):
        try: self.z.Disconnect()
        except Exception: pass
        try: self._co.CoUninitialize()
        except Exception: pass


# ---------------------------------------------------------------- machine connectivity (shown next to every machine)
MSTAT, WATCH = {}, []                              # ip -> {'online', 'last'};  WATCH = IPs to check (kept up to date by the window)


def status_loop():
    while True:
        for ip in list(WATCH):
            if not ip: continue
            try: socket.create_connection((ip, int(cfg.get('port') or 4370)), 2).close(); ok = True
            except Exception: ok = False
            MSTAT.setdefault(ip, {'online': None, 'last': ''})['online'] = ok
        time.sleep(15)


def set_last(ip, text): MSTAT.setdefault(ip, {'online': None, 'last': ''})['last'] = text


# ---------------------------------------------------------------- sync engine
def backup_scan(d, name, users, full):
    """Back up what is on this machine: users the backup does not know yet (or everybody when `full`). Runs while the machine is enabled again."""
    known, new = backup_ids(), 0
    for u in users:
        if STOP.is_set(): break
        if not full and u['id'] in known: continue
        try:
            if save_backup(u, d.templates(u['id']), name) == 'new': new += 1
        except Exception as e:
            log(f'{name}: backup of ID {u["id"]} failed ({e})')
    return new


def sync_target(name, ip, cfg, users, tmpl, removed=frozenset(), leavers=frozenset(), allow_bulk=False, push_all=False, full_scan=False):
    """Copy the Enroller users to this machine (new ones; everybody when push_all), delete `removed` and the leavers, then back the machine up.
    Returns a dict: added, fingers, faces, deleted, left, ok (IDs that are now on the machine with all their templates), scanned."""
    d = Dev(ip, cfg['port'], cfg['comm_key'])
    r = {'added': 0, 'fingers': 0, 'faces': 0, 'deleted': 0, 'left': 0, 'ok': set(), 'scanned': 0}
    try:
        try:
            d.disable()
            dst = d.users(); have = {u['id'] for u in dst}; names = {u['id']: u['name'] for u in dst}; bad = set()
            for u in users:
                if STOP.is_set(): break
                new = u['id'] not in have
                if not (new or push_all): continue
                try: d.set_user(u)
                except Exception as e: bad.add(u['id']); log(f'{name} {ip}: ID {u["id"]} failed ({e})'); continue
                t = tmpl(u['id'])
                for fid, data in t['fp']:
                    try: d.set_fp(u['id'], fid, data); r['fingers'] += 1
                    except Exception as e: bad.add(u['id']); log(f'{name} {ip}: fingerprint {fid} of ID {u["id"]} failed ({e})')
                if t['face']:
                    try: d.set_face(u['id'], t['face']); r['faces'] += 1
                    except Exception as e: bad.add(u['id']); log(f'{name} {ip}: face of ID {u["id"]} failed ({e})')
                if new and u['id'] not in bad:
                    r['added'] += 1
                    ev('TRANSFER', u['id'], u['name'], name, 'copied: ' + ', '.join(b for b in (f'{len(t["fp"])} fingerprint(s)' if t['fp'] else '', 'face' if t['face'] else '', 'RFID card' if u.get('card') else '') if b))
            gone = set()
            for uid in removed:                                           # deleted on the Enroller (mirror mode) -> delete here
                if uid in have:
                    d.delete(uid); gone.add(uid); r['deleted'] += 1; ev('DELETE', uid, names.get(uid), name, 'deleted on the Enroller (mirror)')
            lv = [u for u in dst if norm(u['id']) in leavers and u['id'] not in gone]
            if lv and len(lv) > BULK_LIMIT and not allow_bulk:
                log(f'{name} {ip}: {len(lv)} leavers NOT deleted (more than {BULK_LIMIT} at once). Tick "Allow bulk delete" if this is correct.')
            else:
                for u in lv:
                    if u['id'] not in backup_ids():                       # a leaver is always backed up before it is deleted
                        try: save_backup(u, d.templates(u['id']), name)
                        except Exception as e: log(f'{name}: backup of leaver {u["id"]} failed ({e})')
                    end = LIST['emp'].get(norm(u['id']))
                    d.delete(u['id']); r['left'] += 1; ev('DELETE', u['id'], u['name'], name, f'leaver - service end {end:%d %b %Y}' if end else 'leaver')
                    mark_deleted(u['id'], f'service end {end:%d %b %Y}' if end else 'leaver')
            after = {x['id'] for x in d.users()}
            r['ok'] = {u['id'] for u in users if u['id'] in after and u['id'] not in bad}
            d.refresh()
        finally:
            try: d.enable()
            except Exception: pass
        try: r['scanned'] = backup_scan(d, name, dst, full_scan)           # backup of what is already on the machine
        except Exception as e: log(f'{name}: backup scan failed ({e})')
        return r
    finally:
        d.close()


def run_cycle(cfg, targets, allow_bulk, force=False, leavers=frozenset(), full_scan=False):
    """One round. Returns True when a full backup scan was done."""
    purge, did_full = bool(cfg.get('purge', True)), False
    try:
        src = Dev(cfg['enroller'], cfg['port'], cfg['comm_key'])
    except Exception as e:
        log(f'Enroller {cfg["enroller"]}: cannot connect ({e}). Nothing changed.'); return False
    try:
        users = src.users()
        if not users and not purge:
            log('Enroller returned 0 users - stopped, nothing changed (protection against wiping the other machines).'); return False
        ids = {u['id'] for u in users}
        copy = [u for u in users if norm(u['id']) not in leavers]         # leavers are never copied to the other machines
        cache = {}
        def tmpl(uid):                                                    # templates are read from the Enroller once per cycle
            if uid not in cache: cache[uid] = src.templates(uid)
            return cache[uid]
        snap = load_json(SNAP_FILE, {})
        if users or leavers: log(f'Enroller: {len(users)} users waiting' + (' (full re-copy)' if force else '') + (f', {len(leavers)} leavers in the employee list' if leavers else ''))
        results, failed = {}, []
        for name, ip in targets:
            if STOP.is_set(): break
            removed, keep = set(), None
            if not purge:                                                 # mirror mode: a user deleted on the Enroller is deleted on the machines too
                prev = set(snap.get(ip, []))
                removed = (prev - ids) if prev else set()                 # first sync of a machine never deletes
                if len(removed) > BULK_LIMIT and not allow_bulk:
                    log(f'{name} {ip}: {len(removed)} deletions skipped (more than {BULK_LIMIT}). Tick "Allow bulk delete" if this is intended.')
                    removed, keep = set(), prev
            try:
                r = sync_target(name, ip, cfg, copy, tmpl, removed, leavers, allow_bulk, purge or force, full_scan and not did_full)
                did_full = did_full or full_scan
                results[name] = r
                if not purge:
                    snap[ip] = sorted(keep | ids) if keep else sorted(ids); save_json(SNAP_FILE, snap)
                txt = f'+{r["added"]} users, {r["fingers"]} fingerprints, {r["faces"]} faces' + (f', -{r["left"]} leavers' if r['left'] else '') + (f', -{r["deleted"]} deleted' if r['deleted'] else '') + (f', backup +{r["scanned"]}' if r['scanned'] else '')
                set_last(ip, txt + f'  ({datetime.now():%H:%M})'); log(f'{name} {ip}: {txt}')
            except Exception as e:
                failed.append(name); set_last(ip, f'FAILED ({e})'); log(f'{name} {ip}: FAILED ({e}) - will retry next cycle')
        if not STOP.is_set():                                             # back up what is on the Enroller BEFORE anything is removed from it
            backed = set()
            for u in copy:
                try: save_backup(u, tmpl(u['id']), f'Enroller {cfg["enroller"]}'); backed.add(u['id'])
                except Exception as e: log(f'Enroller: backup of ID {u["id"]} failed ({e})')
            confirmed = set()
            if purge and copy and targets and not failed:                 # on EVERY machine with all templates, and backed up
                confirmed = backed & set.intersection(*(r['ok'] for r in results.values())) if results else set()
            elif purge and copy and failed:
                log(f'Enroller: {len(copy)} users stay on the Enroller until these machines are reachable: {", ".join(failed)}')
            lv = [u for u in users if norm(u['id']) in leavers]
            todo = [u for u in users if u['id'] in confirmed]
            if lv and len(lv) > BULK_LIMIT and not allow_bulk:
                log(f'Enroller: {len(lv)} leavers NOT deleted (more than {BULK_LIMIT} at once). Tick "Allow bulk delete" if this is correct.'); lv = []
            for u in lv:
                if u['id'] not in backup_ids():
                    try: save_backup(u, tmpl(u['id']), f'Enroller {cfg["enroller"]}')
                    except Exception as e: log(f'Enroller: backup of leaver {u["id"]} failed ({e})')
            if todo or lv:
                try:
                    src.disable()
                    for u in todo: src.delete(u['id']); ev('DELETE', u['id'], u['name'], 'Enroller', f'removed from the Enroller after transfer to {len(results)} machine(s)')
                    for u in lv:
                        end = LIST['emp'].get(norm(u['id'])); src.delete(u['id']); ev('DELETE', u['id'], u['name'], 'Enroller', f'leaver - service end {end:%d %b %Y}' if end else 'leaver')
                        mark_deleted(u['id'], f'service end {end:%d %b %Y}' if end else 'leaver')
                    src.refresh(); src.enable()
                    set_last(cfg['enroller'], f'{len(todo)} removed after transfer' + (f', {len(lv)} leavers' if lv else '') + f'  ({datetime.now():%H:%M})')
                    log(f'Enroller {cfg["enroller"]}: {len(todo)} users removed after transfer' + (f', {len(lv)} leavers deleted' if lv else ''))
                except Exception as e:
                    log(f'Enroller clean-up: FAILED ({e})')
    finally:
        src.close(); flush_events()
    return did_full


# ---------------------------------------------------------------- restore: put enrollments from the backup back on the machines
def backup_people(path=None):
    """Active employees of the backup (this PC's backup, or a backup .db / .zip file) with all templates -> list of dicts."""
    tmp = None
    try:
        if path:
            if not os.path.isfile(path): raise ValueError('backup file not found')
            if path.lower().endswith('.zip'):
                tmp = tempfile.mkdtemp()
                with zipfile.ZipFile(path) as z: z.extract('enroll_backup.db', tmp)
                path = os.path.join(tmp, 'enroll_backup.db')
        c = sqlite3.connect(path or db_path(), timeout=30)
        try:
            out = []
            for i, n, pr, pw, card, fp, face in c.execute("SELECT id, name, priv, pw, card, fp, face FROM users WHERE status = 'active' ORDER BY id"):
                out.append({'id': i, 'name': n or '', 'priv': int(pr or 0), 'pw': pw or '', 'card': card if card not in (None, '', '0') else '', 'en': True,
                            'fp': [(int(f), d) for f, d in (json.loads(fp) if fp else [])], 'face': tuple(json.loads(face)) if face else None})
            return out
        finally:
            c.close()
    except (zipfile.BadZipFile, KeyError, sqlite3.DatabaseError): raise ValueError('this is not an Enroll Sync backup file')
    finally:
        if tmp: shutil.rmtree(tmp, ignore_errors=True)


def restore_to(name, ip, people, overwrite):
    """Write the people (user + fingerprints + face + card) to one machine. Employees already there are left alone unless `overwrite`."""
    d = Dev(ip, cfg['port'], cfg['comm_key'])
    r = {'done': 0, 'skipped': 0, 'failed': 0}
    try:
        try:
            d.disable(); have = {u['id'] for u in d.users()}
            for p in people:
                if p['id'] in have and not overwrite: r['skipped'] += 1; continue
                try:
                    d.set_user(p)
                    for fid, data in p['fp']: d.set_fp(p['id'], fid, data)
                    if p['face']: d.set_face(p['id'], p['face'])
                    r['done'] += 1
                    ev('RESTORE', p['id'], p['name'], name, 'restored from backup: ' + (', '.join(b for b in (f'{len(p["fp"])} fingerprint(s)' if p['fp'] else '', 'face' if p['face'] else '', 'RFID card' if p['card'] else '') if b) or 'user data only'))
                except Exception as e:
                    r['failed'] += 1; log(f'{name} {ip}: restore of ID {p["id"]} failed ({e})')
            d.refresh()
        finally:
            try: d.enable()
            except Exception: pass
    finally:
        d.close()
    return r


def run_restore(people, tgts, overwrite, label):
    lv = leavers_now(cfg); ppl = [p for p in people if norm(p['id']) not in lv]
    log(f'Restore from {label}: {len(ppl)} employees' + (f' ({len(people) - len(ppl)} leavers skipped)' if len(ppl) != len(people) else ''))
    lines = []
    for name, ip in tgts:
        try:
            r = restore_to(name, ip, ppl, overwrite); txt = f'{r["done"]} restored, {r["skipped"]} already there, {r["failed"]} failed'
            set_last(ip, f'restore: {txt}  ({datetime.now():%H:%M})')
        except Exception as e:
            txt = f'FAILED ({e})'; set_last(ip, f'restore FAILED ({e})')
        log(f'{name} {ip}: restore - {txt}'); lines.append(f'{name} ({ip}): {txt}')
    flush_events()
    return lines


# ---------------------------------------------------------------- window
RED, RED_D, INK, MUTED, LINE, BG, GREEN = '#c8000f', '#a3040c', '#1a1a1a', '#6b6b6b', '#e3e3e3', '#ffffff', '#1a7f37'
FN, FB = ('Segoe UI', 10), ('Segoe UI', 10, 'bold')
root = tk.Tk(); root.withdraw(); root.title('Enroll Sync - Servis Tyres'); root.configure(bg=BG)
try: logo = tk.PhotoImage(data=LOGO_B64); root.iconphoto(True, logo)
except Exception: logo = None
_w, _h = min(1120, root.winfo_screenwidth() - 40), min(930, root.winfo_screenheight() - 90)
root.geometry(f'{_w}x{_h}+{max(0, (root.winfo_screenwidth() - _w) // 2)}+10'); root.minsize(min(980, _w), min(640, _h))


def setup_style():
    s = ttk.Style()
    try: s.theme_use('clam')
    except tk.TclError: pass
    s.configure('.', font=FN, background=BG, foreground=INK, focuscolor=BG)
    s.configure('TNotebook', background=BG, borderwidth=0, bordercolor=BG, lightcolor=BG, darkcolor=BG, tabmargins=(14, 8, 14, 0))
    s.configure('TNotebook.Tab', font=('Segoe UI', 11, 'bold'), padding=(26, 10), background='#f1f1f1', foreground=MUTED, bordercolor=BG, lightcolor=BG, darkcolor=BG)
    s.map('TNotebook.Tab', background=[('selected', RED), ('active', '#e2e2e2')], foreground=[('selected', 'white')], bordercolor=[('selected', RED)], lightcolor=[('selected', RED)], darkcolor=[('selected', RED)], expand=[('selected', (0, 0, 0, 0))])
    s.configure('TButton', font=FB, padding=(14, 7), background='#f2f2f2', foreground='#111111', bordercolor='#d0d0d0', lightcolor='#f2f2f2', darkcolor='#f2f2f2', relief='flat', focusthickness=0)
    s.map('TButton', background=[('pressed', '#d8d8d8'), ('active', '#e2e2e2')], foreground=[('disabled', '#a8a8a8')])
    s.configure('Primary.TButton', background=RED, foreground='white', bordercolor=RED, lightcolor=RED, darkcolor=RED)
    s.map('Primary.TButton', background=[('pressed', '#82030a'), ('active', RED_D)])
    s.configure('Ghost.TButton', padding=(6, 3), foreground=RED)
    for w in ('TEntry', 'TCombobox'):
        s.configure(w, padding=(7, 5), fieldbackground='white', bordercolor=LINE, lightcolor=LINE, darkcolor=LINE, insertcolor=RED)
        s.map(w, bordercolor=[('focus', RED)], lightcolor=[('focus', RED)], darkcolor=[('focus', RED)])
    s.configure('Card.TCheckbutton', background='white', foreground=INK, font=FN, indicatorbackground='white', indicatorforeground=INK, focuscolor='white', indicatorsize=17, indicatormargin=(0, 0, 8, 0))
    s.map('Card.TCheckbutton', background=[('active', 'white')], indicatorbackground=[('selected', RED), ('!selected', 'white')], indicatorforeground=[('selected', 'white')])
    s.configure('Treeview', rowheight=24, fieldbackground='white', background='white', bordercolor=LINE, font=('Segoe UI', 9))
    s.configure('Treeview.Heading', font=FB, background='#f1f1f1', foreground=INK, relief='flat', padding=(6, 5))
    s.map('Treeview', background=[('selected', '#fde3e5')], foreground=[('selected', INK)])
    s.configure('Vertical.TScrollbar', background='#c9c9c9', troughcolor=BG, bordercolor=BG, lightcolor='#c9c9c9', darkcolor='#c9c9c9', arrowcolor=INK, gripcount=0)


setup_style()


def make_card(parent, title=None, px=16, py=12):
    outer = tk.Frame(parent, bg=LINE); inner = tk.Frame(outer, bg='white'); inner.pack(fill='both', expand=True, padx=1, pady=1)
    if title:
        tk.Label(inner, text=title, font=('Segoe UI', 11, 'bold'), fg=INK, bg='white').pack(anchor='w', padx=px, pady=(py, 0))
        tk.Frame(inner, bg=LINE, height=1).pack(fill='x', padx=px, pady=(7, 0))
    body = tk.Frame(inner, bg='white'); body.pack(fill='both', expand=True, padx=px, pady=py)
    return outer, body


def note(parent, text, **kw): return tk.Label(parent, text=text, bg='white', fg=MUTED, font=('Segoe UI', 9), justify='left', wraplength=kw.pop('wrap', 980), **kw)
def lbl(parent, text, **kw): return tk.Label(parent, text=text, bg='white', fg=kw.pop('fg', MUTED), font=kw.pop('font', FN), **kw)


CANVAS = {}


def scroll_tab(tab):
    """A tab whose content scrolls (small laptop screens). Returns the frame to put the content in."""
    c = tk.Canvas(tab, bg=BG, highlightthickness=0); sc = ttk.Scrollbar(tab, orient='vertical', command=c.yview)
    inner = tk.Frame(c, bg=BG); win = c.create_window((0, 0), window=inner, anchor='nw')
    inner.bind('<Configure>', lambda e: c.configure(scrollregion=c.bbox('all'))); c.bind('<Configure>', lambda e: c.itemconfig(win, width=e.width))
    c.configure(yscrollcommand=sc.set); sc.pack(side='right', fill='y'); c.pack(side='left', fill='both', expand=True)
    CANVAS[str(tab)] = c
    return inner


def _wheel(e):
    c = CANVAS.get(nb.select())
    if c and e.widget.winfo_toplevel() is root and not isinstance(e.widget, (tk.Text, ttk.Treeview, ttk.Combobox)): c.yview_scroll(-1 * (e.delta // 120), 'units')


root.bind_all('<MouseWheel>', _wheel)


def _dialog(title, parent):
    win = tk.Toplevel(root); win.title(title); win.configure(bg='white'); win.resizable(False, False)
    if parent is not None and parent.winfo_viewable():
        try: win.transient(parent)
        except tk.TclError: pass
    win.attributes('-topmost', True)
    return win


def _center(win, parent):
    win.update_idletasks()
    if parent is not None and parent.winfo_viewable(): x, y = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2, parent.winfo_rooty() + 120
    else: x, y = (win.winfo_screenwidth() - win.winfo_width()) // 2, (win.winfo_screenheight() - win.winfo_height()) // 3
    win.geometry('+%d+%d' % (max(0, x), max(0, y)))


def _wrong(win, err):
    PW_FAIL['n'] += 1
    if PW_FAIL['n'] >= 5: PW_FAIL.update(n=0, until=time.time() + 60); win.destroy(); log('5 wrong passwords - locked for 60 seconds.'); return
    err.set(f'Wrong password ({5 - PW_FAIL["n"]} tries left)')


def _locked_msg():
    if time.time() < PW_FAIL['until']:
        messagebox.showwarning('Locked', f'Too many wrong passwords. Try again in {int(PW_FAIL["until"] - time.time()) + 1} seconds.'); return True
    return False


def ask_password(why='This action', login=False):
    """Modal password box. True only for the right password; 5 wrong tries lock it for 60 seconds. login=True: the box that opens the program."""
    if _locked_msg(): return False
    try: parent = None if login else root.focus_get().winfo_toplevel()
    except Exception: parent = None if login else root
    win = _dialog('Enroll Sync - Login' if login else 'Password required', parent)
    tk.Label(win, text='Enroll Sync - Servis Tyres' if login else 'Password required', font=('Segoe UI', 12, 'bold'), fg=INK, bg='white').pack(anchor='w', padx=22, pady=(16, 0))
    tk.Label(win, text=why, font=('Segoe UI', 9), fg=MUTED, bg='white').pack(anchor='w', padx=22, pady=(2, 8))
    var, err, ok = tk.StringVar(), tk.StringVar(), [False]
    ent = ttk.Entry(win, textvariable=var, show='*', width=30, font=('Segoe UI', 11)); ent.pack(padx=22)
    tk.Label(win, textvariable=err, font=('Segoe UI', 9), fg=RED, bg='white').pack(anchor='w', padx=22, pady=(4, 0))

    def submit(_e=None):
        if check_password(var.get()): PW_FAIL['n'] = 0; ok[0] = True; win.destroy(); return
        var.set(''); _wrong(win, err)

    bf = tk.Frame(win, bg='white'); bf.pack(anchor='e', padx=22, pady=14)
    ttk.Button(bf, text='OK', style='Primary.TButton', command=submit).pack(side='left'); ttk.Button(bf, text='Exit' if login else 'Cancel', command=win.destroy).pack(side='left', padx=(8, 0))
    if login: ttk.Button(bf, text='Reset password', command=lambda: (reset_password(win), win.grab_set(), ent.focus_set())).pack(side='left', padx=(8, 0))
    win.bind('<Return>', submit); win.bind('<Escape>', lambda _e: win.destroy())
    _center(win, parent); win.grab_set(); ent.focus_set(); root.wait_window(win)
    return ok[0]


def reset_password(parent=None):
    """Set a new password. Needs the reset key (built into the exe)."""
    if _locked_msg(): return
    win = _dialog('Reset password', parent); vk, vn, vc, err = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(); first = None
    tk.Label(win, text='Reset password', font=('Segoe UI', 12, 'bold'), fg=INK, bg='white').pack(anchor='w', padx=22, pady=(16, 6))
    for text, var in (('Reset key', vk), ('New password  (at least 6 characters)', vn), ('Confirm new password', vc)):
        tk.Label(win, text=text, font=('Segoe UI', 9), fg=MUTED, bg='white').pack(anchor='w', padx=22)
        e = ttk.Entry(win, textvariable=var, show='*', width=30, font=('Segoe UI', 11)); e.pack(padx=22, pady=(0, 6)); first = first or e
    tk.Label(win, textvariable=err, font=('Segoe UI', 9), fg=RED, bg='white').pack(anchor='w', padx=22)

    def go(_e=None):
        if not check_master(vk.get()): vk.set(''); _wrong(win, err); return
        if len(vn.get()) < 6: err.set('The new password needs at least 6 characters'); return
        if vn.get() != vc.get(): err.set('The two passwords are different'); return
        set_password(vn.get()); PW_FAIL['n'] = 0; log('Password changed.'); win.destroy(); messagebox.showinfo('Password', 'The new password is saved.')

    bf = tk.Frame(win, bg='white'); bf.pack(anchor='e', padx=22, pady=14)
    ttk.Button(bf, text='Save password', style='Primary.TButton', command=go).pack(side='left'); ttk.Button(bf, text='Cancel', command=win.destroy).pack(side='left', padx=(8, 0))
    win.bind('<Return>', go); win.bind('<Escape>', lambda _e: win.destroy())
    _center(win, parent); win.grab_set(); first.focus_set(); root.wait_window(win)


# ---- editing is locked: entries, tick boxes, add / remove machine are disabled until the password is entered (re-locks after Save or 3 minutes without use)
EDIT, EDIT_SECS = {'on': False, 'until': 0.0}, 180
LOCK_BTNS = ('+ Add machine', '\u2715', 'Browse')


def _walk(w):
    yield w
    for c in w.winfo_children():
        if isinstance(c, tk.Toplevel) and c is not globals().get('data_win'): continue         # other windows (restore / password boxes) manage themselves
        yield from _walk(c)


def apply_lock():
    try: free = {str(rf), str(rt)}                                                               # the report date filters only choose what to look at
    except NameError: free = set()
    st = ['!disabled'] if EDIT['on'] else ['disabled']
    for w in _walk(root):
        if isinstance(w, ttk.Combobox): continue
        if isinstance(w, ttk.Entry) and str(w.cget('textvariable')) in free: continue
        if isinstance(w, (ttk.Entry, ttk.Checkbutton)) or (isinstance(w, ttk.Button) and str(w.cget('text')) in LOCK_BTNS): w.state(st)


def set_lock(locked):
    EDIT['on'] = not locked; EDIT['until'] = time.time() + EDIT_SECS; apply_lock()
    b = globals().get('edit_btn')
    if b is not None: b.config(text='Editing - click to lock' if EDIT['on'] else 'Unlock to edit')


def unlock_ui():
    if ask_password('Enter the password to edit'): set_lock(False)


def toggle_edit(): set_lock(True) if EDIT['on'] else unlock_ui()


def _activity(e):
    try:
        w = e.widget
        if EDIT['on']: EDIT['until'] = time.time() + EDIT_SECS
        elif e.type == tk.EventType.ButtonPress and isinstance(w, (ttk.Entry, ttk.Checkbutton, ttk.Button)) and not isinstance(w, ttk.Combobox) and w.winfo_toplevel() in (root, globals().get('data_win')) and w.instate(['disabled']): unlock_ui()
    except Exception: pass


root.bind_all('<Button-1>', _activity, add='+'); root.bind_all('<Key>', _activity, add='+')


def guarded(fn, why):
    if ask_password(why): return fn()


def stop_sync():
    if ask_password('Stop the sync'): STOP.set(); log('Stopped (password entered).')


def exit_app():
    if not ask_password('Exit Enroll Sync - the sync and the daily e-mail stop'): return
    STOP.set(); flush_events(); root.destroy()


# ---- header: logo, title, status pill
hd = tk.Frame(root, bg='white'); hd.pack(fill='x')
if logo: tk.Label(hd, image=logo, bg='white').pack(side='left', padx=(18, 14), pady=4)
tb = tk.Frame(hd, bg='white'); tb.pack(side='left')
tk.Label(tb, text='Enroll Sync', font=('Segoe UI', 21, 'bold'), fg=INK, bg='white').pack(anchor='w')
tk.Label(tb, text='Servis Tyres  |  UFace 800 / 900 enrollment transfer, backup and reports', font=('Segoe UI', 9), fg=MUTED, bg='white').pack(anchor='w')
pill = tk.Label(hd, text='\u25cf  STOPPED', font=('Segoe UI', 10, 'bold'), fg=INK, bg='#eeeeee', padx=16, pady=6); pill.pack(side='right', padx=18)
ttk.Button(hd, text='Exit', style='Primary.TButton', command=lambda: exit_app()).pack(side='right', padx=(0, 4))
edit_btn = ttk.Button(hd, text='Unlock to edit', command=lambda: toggle_edit()); edit_btn.pack(side='right', padx=(0, 4))
ttk.Button(hd, text='Reset password', command=lambda: reset_password(root)).pack(side='right', padx=(0, 4))
tk.Frame(root, bg=RED, height=4).pack(fill='x')

nb = ttk.Notebook(root); nb.pack(fill='both', expand=True, padx=8, pady=(4, 4))
tab_conn, tab_rep, tab_mail = (tk.Frame(nb, bg=BG) for _ in range(3))
for t, n in ((tab_conn, 'Connectivity'), (tab_rep, 'Reports'), (tab_mail, 'Email')): nb.add(t, text=n)
TAB = {'cur': nb.select() or nb.tabs()[0]}


def _tab_click(e):
    """Clicking another tab asks for the password every time; the tab changes only when it is right."""
    try: idx = nb.index(f'@{e.x},{e.y}')
    except tk.TclError: return None                                                  # not on a tab
    if nb.tabs()[idx] == TAB['cur']: return None
    if ask_password('Enter the password to open the tab "' + nb.tab(idx, 'text') + '"'): TAB['cur'] = nb.tabs()[idx]; nb.select(idx)
    return 'break'


def _tab_changed(_e=None):
    c = nb.select()
    if c != TAB['cur']: nb.select(TAB['cur'])                                          # any other way of switching (keyboard ...) is undone


nb.bind('<Button-1>', _tab_click); nb.bind('<<NotebookTabChanged>>', _tab_changed)
for _k in ('<Control-Tab>', '<Control-Shift-Tab>', '<Control-ISO_Left_Tab>', '<Control-Prior>', '<Control-Next>', '<Left>', '<Right>'):
    try: nb.bind(_k, lambda _e: 'break')
    except tk.TclError: pass   # ISO_Left_Tab sirf Linux/X11 par hota hai
# buttons of the Connectivity tab stay visible at the bottom of the tab; everything above them scrolls
bt = tk.Frame(tab_conn, bg='#f6f6f6', highlightthickness=1, highlightbackground=LINE); bt.pack(side='bottom', fill='x')
ttk.Button(bt, text='Save + Start auto sync', style='Primary.TButton', command=lambda: start_auto()).pack(side='left', padx=(12, 0), pady=8)
ttk.Button(bt, text='Sync now', command=lambda: sync_now()).pack(side='left', padx=8, pady=8)
ttk.Button(bt, text='Stop', command=lambda: stop_sync()).pack(side='left', pady=8)
ttk.Button(bt, text='Re-copy all fingerprints + faces', command=lambda: guarded(lambda: sync_now(True), 'Re-copy all fingerprints + faces to the machines')).pack(side='left', padx=8, pady=8)
ttk.Button(bt, text='Data  (employee list)', command=lambda: open_data()).pack(side='right', padx=12, pady=8)
bc, br, bm = scroll_tab(tab_conn), scroll_tab(tab_rep), scroll_tab(tab_mail)
data_win = tk.Toplevel(root); data_win.title('Data - Employee list'); data_win.configure(bg=BG); data_win.transient(root); data_win.withdraw()
data_win.geometry(f'{min(1060, _w)}x{min(700, _h)}+60+30'); data_win.protocol('WM_DELETE_WINDOW', data_win.withdraw)
if logo: data_win.iconphoto(False, logo)
bd = tk.Frame(data_win, bg=BG); bd.pack(fill='both', expand=True)


def open_data():
    if not ask_password('Enter the password to open Data'): return
    data_win.deiconify(); data_win.lift(); data_win.focus_force(); show_leavers()

# ---- settings variables
S = lambda k: tk.StringVar(value=str(cfg[k])); B = lambda k: tk.BooleanVar(value=bool(cfg[k]))
enr, interval, comm, purge_v, bulk_v = S('enroller'), S('interval'), S('comm_key'), B('purge'), B('bulk')
list_url, list_min, del_lv, dc_user, dc_pass = S('list_url'), S('list_min'), B('del_leavers'), S('dc_user'), S('dc_pass')
mail_on, mail_to, mail_server, mail_port, mail_user, mail_pass, mail_time = B('mail_on'), S('mail_to'), S('mail_server'), S('mail_port'), S('mail_user'), S('mail_pass'), S('mail_time')
bdir = tk.StringVar(value=cfg['backup_dir'] or os.path.dirname(db_path()))

# ================================================================ Connectivity tab
c1o, c1 = make_card(bc, 'Enroller machine'); c1o.pack(fill='x', padx=12, pady=(10, 6))
r1 = tk.Frame(c1, bg='white'); r1.pack(fill='x')
lbl(r1, 'Enroller Machine IP', fg=INK, font=FB).pack(side='left'); ttk.Entry(r1, textvariable=enr, width=18, font=('Segoe UI', 11)).pack(side='left', padx=10)
enr_st = lbl(r1, '-', width=16, anchor='w'); enr_st.pack(side='left'); enr_last = lbl(r1, '', font=('Segoe UI', 9)); enr_last.pack(side='left')
note(c1, 'New enrollments are done on this machine. They are copied to the machines below and then removed from it (see Options).').pack(anchor='w', pady=(6, 0))

c2o, c2 = make_card(bc, 'Machines  (IN / OUT / Colony gates)'); c2o.pack(fill='x', padx=12, pady=6)
minner = tk.Frame(c2, bg='white'); minner.pack(fill='x')
for c, t in enumerate(('Use', 'Machine name', 'IP address', 'Connectivity', 'Last sync', '')): lbl(minner, t, font=('Segoe UI', 9, 'bold')).grid(row=0, column=c, sticky='w', padx=(0, 8), pady=(0, 4))
mrows = []


def regrid():
    for i, r in enumerate(mrows, 1):
        for c, w in enumerate(r['w']): w.grid(row=i, column=c, sticky='w', padx=(0, 8), pady=2)


def add_row(m=None):
    m = m or {'name': f'Machine {len(mrows) + 1}', 'ip': '', 'on': True}
    r = {'on': tk.BooleanVar(value=bool(m.get('on', True))), 'name': tk.StringVar(value=m.get('name', '')), 'ip': tk.StringVar(value=m.get('ip', ''))}
    r['st'] = lbl(minner, '-', width=14, anchor='w'); r['last'] = lbl(minner, '', font=('Segoe UI', 9), width=48, anchor='w')
    r['w'] = [ttk.Checkbutton(minner, variable=r['on'], style='Card.TCheckbutton'), ttk.Entry(minner, textvariable=r['name'], width=20), ttk.Entry(minner, textvariable=r['ip'], width=16),
              r['st'], r['last'], ttk.Button(minner, text='\u2715', width=3, style='Ghost.TButton', command=lambda r=r: remove_row(r))]
    mrows.append(r); regrid(); apply_lock()


def remove_row(r):
    for w in r['w']: w.destroy()
    mrows.remove(r); regrid()


for _m in cfg['machines']: add_row(_m)
mb = tk.Frame(c2, bg='white'); mb.pack(fill='x', pady=(8, 0))
ttk.Button(mb, text='+ Add machine', command=lambda: add_row()).pack(side='left')
note(mb, 'Tick = this machine receives the enrollments.  \u2715 = remove the machine from the list.', wrap=700).pack(side='left', padx=14)

c3o, c3 = make_card(bc, 'Options'); c3o.pack(fill='x', padx=12, pady=6)
r3 = tk.Frame(c3, bg='white'); r3.pack(fill='x')
lbl(r3, 'Check every').pack(side='left'); ttk.Entry(r3, textvariable=interval, width=6, justify='center').pack(side='left', padx=6); lbl(r3, 'seconds').pack(side='left', padx=(0, 22))
lbl(r3, 'Comm Key').pack(side='left'); ttk.Entry(r3, textvariable=comm, width=8, justify='center').pack(side='left', padx=6)
ttk.Checkbutton(c3, text='Delete from the Enroller after the enrollment is on every machine and saved in the backup', variable=purge_v, style='Card.TCheckbutton').pack(anchor='w', pady=(8, 2))
ttk.Checkbutton(c3, text='Allow bulk delete (more than 20 leavers / deletions at once)', variable=bulk_v, style='Card.TCheckbutton').pack(anchor='w', pady=2)

busy, auto_t = threading.Lock(), [None]


def targets(): return [(m['name'], m['ip']) for m in cfg['machines'] if m['on'] and m['ip']]


def save():
    """Writes the settings. A change needs the password; when nothing was changed nothing is asked."""
    try:
        mt = datetime.strptime(mail_time.get().strip(), '%H:%M').strftime('%H:%M')      # 8:00 is kept as 08:00
        new = dict(enroller=enr.get().strip(), interval=max(10, int(interval.get())), comm_key=int(comm.get()), bulk=bulk_v.get(), purge=purge_v.get(),
                   list_url=list_url.get().strip(), list_min=max(1, int(list_min.get())), del_leavers=del_lv.get(), dc_user=dc_user.get().strip(), dc_pass=dc_pass.get(),
                   mail_on=mail_on.get(), mail_to=mail_to.get().strip(), mail_server=mail_server.get().strip(), mail_port=int(mail_port.get()), mail_user=mail_user.get().strip(),
                   mail_pass=mail_pass.get(), mail_time=mt)
    except ValueError:
        messagebox.showerror('Check settings', 'Seconds, minutes, Comm Key and port must be numbers, and the e-mail time must look like 20:00'); return False
    new['machines'] = [{'name': r['name'].get().strip() or 'Machine', 'ip': r['ip'].get().strip(), 'on': r['on'].get()} for r in mrows]
    new['backup_dir'] = '' if bdir.get().strip() == os.path.dirname(os.path.join(APP, 'Backup', 'x')) else bdir.get().strip()
    changed = any(cfg.get(k) != v for k, v in new.items())
    if changed and not EDIT['on'] and not ask_password('Save the changed settings'): return False
    cfg.update(new); save_json(CFG_FILE, cfg)
    if changed: set_lock(True)
    return True


def cycle(force=False, list_now=False, full=False):
    if not busy.acquire(blocking=False): log('A sync is already running.'); return
    try:
        if cfg['list_url'].strip() and (list_now or time.time() >= LIST['next']): refresh_list(cfg, manual=list_now)          # the employee list is refreshed on its own timer
        due = time.time() - float(cfg.get('last_full') or 0) > float(cfg['scan_hours']) * 3600
        if run_cycle(cfg, targets(), cfg['bulk'], force, leavers_now(cfg), full or due): cfg['last_full'] = time.time(); save_json(CFG_FILE, cfg)
    except Exception as e: log(f'Error: {e}')
    finally: busy.release()


def sync_now(force=False, full=False):
    if not save(): return
    if not cfg['enroller']: messagebox.showinfo('Enroll Sync', 'Enter the Enroller Machine IP'); return
    if not (auto_t[0] and auto_t[0].is_alive()): STOP.clear()
    threading.Thread(target=cycle, args=(force, True, full), daemon=True).start()


def loop():
    while not STOP.is_set():
        cycle(); STOP.wait(cfg['interval'])
    log('Auto sync stopped')


def start_auto():
    if not save(): return
    if not cfg['enroller'] or not targets(): messagebox.showinfo('Enroll Sync', 'Enter the Enroller IP and at least one machine IP (ticked)'); return
    if auto_t[0] and auto_t[0].is_alive() and not STOP.is_set(): log('Auto sync is already running.'); return
    STOP.clear(); auto_t[0] = threading.Thread(target=loop, daemon=True); auto_t[0].start(); log(f'Auto sync started (every {cfg["interval"]} s)')


# ================================================================ Data tab: employee list
d1o, d1 = make_card(bd, 'Employee list  (Decibel)'); d1o.pack(fill='x', padx=12, pady=(10, 6))
note(d1, 'The tool logs in to Decibel, opens the Attendance Register, selects Service Tyres Private Limited, sets From / To Date = today and clicks Get Report. Employee ID + serviceenddate are read from it (01/01/1900 or a date from today on = active, an earlier date = left). '
         'Any other Excel / CSV / Google Sheets link or a file path also works. Employees whose end date is before today are deleted from all machines and are never copied. The list is downloaded again on the timer below.').pack(anchor='w', pady=(0, 8))
lr = tk.Frame(d1, bg='white'); lr.pack(fill='x', pady=3)
lbl(lr, 'Employee list link', fg=INK, font=FB, width=18, anchor='w').pack(side='left'); ttk.Entry(lr, textvariable=list_url).pack(side='left', fill='x', expand=True)
lc = tk.Frame(d1, bg='white'); lc.pack(fill='x', pady=3)
lbl(lc, 'Decibel User ID', width=18, anchor='w').pack(side='left'); ttk.Entry(lc, textvariable=dc_user, width=20).pack(side='left', padx=(0, 20))
lbl(lc, 'Password').pack(side='left'); dc_pw_e = ttk.Entry(lc, textvariable=dc_pass, width=22, show='*'); dc_pw_e.pack(side='left', padx=8)
dc_show = tk.BooleanVar(value=False)
tk.Checkbutton(lc, text='Show', variable=dc_show, bg='white', activebackground='white', fg=MUTED, font=FN, bd=0, highlightthickness=0, command=lambda: dc_pw_e.config(show='' if dc_show.get() else '*')).pack(side='left')
lo = tk.Frame(d1, bg='white'); lo.pack(fill='x', pady=3)
lbl(lo, 'Download again every', width=18, anchor='w').pack(side='left'); ttk.Entry(lo, textvariable=list_min, width=6, justify='center').pack(side='left', padx=(0, 6)); lbl(lo, 'minutes').pack(side='left', padx=(0, 22))
ttk.Checkbutton(lo, text='Delete leavers (service end date before today)', variable=del_lv, style='Card.TCheckbutton').pack(side='left')
list_status, lv_sig = tk.StringVar(value=LIST['result']), [None]


def list_now():
    if save(): threading.Thread(target=lambda: refresh_list(cfg, True), daemon=True).start()


def open_register_folder():
    d = os.path.join(APP, 'Register'); os.makedirs(d, exist_ok=True)
    try: os.startfile(d)
    except Exception: messagebox.showinfo('Register folder', d)


ld = tk.Frame(d1, bg='white'); ld.pack(fill='x', pady=(8, 0))
ttk.Button(ld, text='Save', command=save).pack(side='left'); ttk.Button(ld, text='Download / check list now', style='Primary.TButton', command=list_now).pack(side='left', padx=8)
ttk.Button(ld, text='Open register folder', command=open_register_folder).pack(side='left')
d2o, d2 = make_card(bd, 'Status'); d2o.pack(fill='both', expand=True, padx=12, pady=(6, 10))
tk.Label(d2, textvariable=list_status, bg='white', fg=INK, font=FN, justify='left', wraplength=1000).pack(anchor='w', pady=(0, 6))
lvbox = tk.Text(d2, height=10, font=('Consolas', 10), bg='#f6f6f6', fg=INK, relief='flat', bd=0, padx=10, pady=8, state='disabled'); lvbox.pack(fill='both', expand=True)


def show_leavers():
    lv = sorted(((e, k) for k, e in LIST['emp'].items() if e and e < date.today()), reverse=True)
    lines = [f'{len(lv)} employees with a service end date before today ({date.today():%d %b %Y}):' if LIST['emp'] else 'No employee list loaded yet.', '']
    lines += [f'{k:<14}{e:%d %b %Y}' for e, k in lv[:200]]
    if len(lv) > 200: lines.append(f'... and {len(lv) - 200} more')
    lvbox.config(state='normal'); lvbox.delete('1.0', 'end'); lvbox.insert('end', '\n'.join(lines)); lvbox.config(state='disabled')


# ================================================================ Reports tab: backup + activity / deletion reports
b1o, b1 = make_card(br, 'Backup  (fingerprints, face, RFID card of every enrollment)'); b1o.pack(fill='x', padx=12, pady=(10, 6))
bstat = tk.StringVar(value='-')
tk.Label(b1, textvariable=bstat, bg='white', fg=INK, font=FB, justify='left').pack(anchor='w')
note(b1, 'From the first day, every enrollment that is transferred or already on a machine is saved here and kept up to date. Deleted employees stay in the backup (marked as deleted).').pack(anchor='w', pady=(2, 6))
bf = tk.Frame(b1, bg='white'); bf.pack(fill='x', pady=2)
lbl(bf, 'Backup folder').pack(side='left'); ttk.Entry(bf, textvariable=bdir).pack(side='left', fill='x', expand=True, padx=8)


def pick_dir():
    d = filedialog.askdirectory(initialdir=bdir.get() or APP)
    if d: bdir.set(d.replace('/', os.sep)); save()


ttk.Button(bf, text='Browse', command=pick_dir).pack(side='left')


def save_as(title, name, ext):
    return filedialog.asksaveasfilename(title=title, initialfile=name, defaultextension=ext, filetypes=[(ext.upper().strip('.') + ' file', '*' + ext)])


def dl_zip():
    p = save_as('Save backup', f'Backup_{date.today():%Y-%m-%d}.zip', '.zip')
    if p:
        flush_events()
        try: log(f'Backup saved: {p} ({make_backup_zip(p) // 1024} KB)')
        except Exception as e: messagebox.showerror('Backup', str(e))


def dl_xlsx():
    p = save_as('Save backup list', f'Backup_list_{date.today():%Y-%m-%d}.xlsx', '.xlsx')
    if p:
        try: export_backup_xlsx(p); log(f'Backup list saved: {p}')
        except Exception as e: messagebox.showerror('Backup', str(e))


def open_restore():
    if not ask_password('Open Restore from backup'): return
    win = tk.Toplevel(root); win.title('Restore from backup'); win.configure(bg=BG); win.transient(root); win.geometry(f'780x{min(660, _h)}+80+30')
    outer, body = make_card(win, 'Restore enrollments from the backup'); outer.pack(fill='both', expand=True, padx=12, pady=12)
    note(body, 'Puts the saved users, fingerprints, faces and RFID cards back on the machines ticked below. Employees whose service end date is before today are skipped. The password is required.', wrap=700).pack(anchor='w', pady=(0, 8))
    src, path, idv, ow, st = tk.StringVar(value='current'), tk.StringVar(), tk.StringVar(), tk.BooleanVar(value=False), tk.StringVar()
    rb = lambda text, val: tk.Radiobutton(body, text=text, variable=src, value=val, bg='white', activebackground='white', fg=INK, font=FN, anchor='w', justify='left', wraplength=700)
    rb(f'The backup of this PC  ({db_path()})', 'current').pack(anchor='w')
    rb('A backup file from another PC / from the e-mail  (.zip or .db)', 'file').pack(anchor='w', pady=(4, 0))
    fr = tk.Frame(body, bg='white'); fr.pack(fill='x', pady=(2, 8)); ttk.Entry(fr, textvariable=path).pack(side='left', fill='x', expand=True, padx=(24, 8))

    def browse():
        p = filedialog.askopenfilename(parent=win, title='Backup file', filetypes=[('Backup', '*.zip *.db'), ('All files', '*.*')])
        if p: path.set(p.replace('/', os.sep)); src.set('file')

    ttk.Button(fr, text='Browse', command=browse).pack(side='left')
    lbl(body, 'Only these employee IDs  (comma separated - empty = everybody in the backup)', fg=INK).pack(anchor='w')
    ttk.Entry(body, textvariable=idv).pack(fill='x', pady=(2, 8))
    ttk.Checkbutton(body, text='Overwrite employees that are already on the machine  (default: only the missing ones are added)', variable=ow, style='Card.TCheckbutton').pack(anchor='w', pady=(0, 8))
    lbl(body, 'Restore to', fg=INK, font=FB).pack(anchor='w')
    grid = tk.Frame(body, bg='white'); grid.pack(fill='x', pady=(2, 4)); tv = []
    items = ([('Enroller', enr.get().strip(), False)] if enr.get().strip() else []) + [(r['name'].get().strip() or 'Machine', r['ip'].get().strip(), r['on'].get()) for r in mrows if r['ip'].get().strip()]
    for k, (n, ip, on) in enumerate(items):
        v = tk.BooleanVar(value=on); tv.append((v, n, ip))
        ttk.Checkbutton(grid, text=f'{n}  ({ip})', variable=v, style='Card.TCheckbutton').grid(row=k // 2, column=k % 2, sticky='w', padx=(0, 24), pady=2)
    note(body, 'Tip: restoring to the Enroller is enough while auto sync is running - it copies them to every machine and removes them from the Enroller.', wrap=700).pack(anchor='w', pady=(4, 6))
    tk.Label(body, textvariable=st, bg='white', fg=INK, font=FN, justify='left', wraplength=700).pack(anchor='w', pady=(4, 0))
    bar = tk.Frame(body, bg='white'); bar.pack(fill='x', pady=(10, 0))
    go_b = ttk.Button(bar, text='Start restore', style='Primary.TButton'); go_b.pack(side='left'); ttk.Button(bar, text='Close', command=win.destroy).pack(side='left', padx=8)

    def go():
        ids = {norm(x) for x in re.split(r'[;,\s]+', idv.get()) if x}
        tg, use_file, fpath, over = [(n, ip) for v, n, ip in tv if v.get()], src.get() == 'file', path.get().strip().strip('"'), ow.get()
        if not tg: messagebox.showinfo('Restore', 'Tick at least one machine.', parent=win); return
        if use_file and not fpath: messagebox.showinfo('Restore', 'Choose the backup file.', parent=win); return
        if not busy.acquire(blocking=False): messagebox.showinfo('Restore', 'A sync is running - try again in a minute.', parent=win); return
        st.set('Restoring ... please wait (progress is in the log under the tabs)'); go_b.config(state='disabled'); out = []

        def work():
            try:
                ppl = backup_people(fpath if use_file else None)
                if ids: ppl = [p for p in ppl if norm(p['id']) in ids]
                out.append('\n'.join(run_restore(ppl, tg, over, os.path.basename(fpath) if use_file else 'this PC') if ppl else ['No matching employees found in the backup.']))
            except Exception as e:
                out.append(f'FAILED: {e}'); log(f'Restore FAILED: {e}')
            finally: busy.release()

        def wait():
            try:
                if not out: win.after(500, wait); return
                st.set(out[0]); go_b.config(state='normal')
            except tk.TclError: pass

        threading.Thread(target=work, daemon=True).start(); wait()

    go_b.config(command=go)


bb = tk.Frame(b1, bg='white'); bb.pack(fill='x', pady=(8, 0))
ttk.Button(bb, text='Backup now (scan all machines)', style='Primary.TButton', command=lambda: sync_now(False, True)).pack(side='left')
ttk.Button(bb, text='Download backup (zip)', command=dl_zip).pack(side='left', padx=8); ttk.Button(bb, text='Download backup list (Excel)', command=dl_xlsx).pack(side='left')
ttk.Button(bb, text='Restore from backup', command=open_restore).pack(side='left', padx=8)

r1o, r1c = make_card(br, 'Activity and deletion reports'); r1o.pack(fill='both', expand=True, padx=12, pady=(6, 10))
rf, rt, rtype, rinfo = tk.StringVar(value=f'{date.today():%d-%m-%Y}'), tk.StringVar(value=f'{date.today():%d-%m-%Y}'), tk.StringVar(value='All'), tk.StringVar()
rbar = tk.Frame(r1c, bg='white'); rbar.pack(fill='x')
lbl(rbar, 'From').pack(side='left'); ttk.Entry(rbar, textvariable=rf, width=12, justify='center').pack(side='left', padx=(6, 14))
lbl(rbar, 'To').pack(side='left'); ttk.Entry(rbar, textvariable=rt, width=12, justify='center').pack(side='left', padx=(6, 14))
lbl(rbar, 'Show').pack(side='left'); ttk.Combobox(rbar, textvariable=rtype, values=list(KIND_FILTER), width=11, state='readonly').pack(side='left', padx=(6, 14))


def get_range():
    try: return parse_day(rf.get()), parse_day(rt.get())
    except ValueError as e: messagebox.showerror('Date', str(e)); return None


def show_report():
    rg = get_range()
    if not rg: return
    flush_events(); rows = query_events(rg[0], rg[1], KIND_FILTER[rtype.get()]); tree.delete(*tree.get_children())
    for r in rows[-2000:]: tree.insert('', 'end', values=(r[0], KIND_LABEL.get(r[1], r[1]), r[2], r[3], r[4], r[5]))
    rinfo.set(f'{len(rows)} entries' + ('  (last 2000 shown - the Excel file has all)' if len(rows) > 2000 else ''))


def dl_report():
    rg = get_range()
    if not rg: return
    p = save_as('Save report', f'Activity_Report_{rg[0]:%Y-%m-%d}_{rg[1]:%Y-%m-%d}.xlsx', '.xlsx')
    if p:
        flush_events()
        try: log(f'Report saved: {p} ({export_report(p, rg[0], rg[1], KIND_FILTER[rtype.get()])} entries)')
        except Exception as e: messagebox.showerror('Report', str(e))


ttk.Button(rbar, text='Show', style='Primary.TButton', command=show_report).pack(side='left'); ttk.Button(rbar, text='Download report (Excel)', command=dl_report).pack(side='left', padx=8)
lbl(rbar, '', font=('Segoe UI', 9)).pack(side='left'); tk.Label(rbar, textvariable=rinfo, bg='white', fg=MUTED, font=('Segoe UI', 9)).pack(side='left', padx=8)
tw = tk.Frame(r1c, bg='white'); tw.pack(fill='both', expand=True, pady=(8, 0))
cols = (('time', 'Time', 130), ('type', 'Type', 160), ('id', 'Employee ID', 90), ('name', 'Name', 170), ('machine', 'Machine', 110), ('detail', 'Details', 380))
tree = ttk.Treeview(tw, columns=[c[0] for c in cols], show='headings', height=8)
for k, t, w in cols: tree.heading(k, text=t); tree.column(k, width=w, anchor='w')
tsc = ttk.Scrollbar(tw, orient='vertical', command=tree.yview); tree.configure(yscrollcommand=tsc.set); tree.pack(side='left', fill='both', expand=True); tsc.pack(side='right', fill='y')

# ================================================================ Email tab
e1o, e1 = make_card(bm, 'Automatic daily e-mail'); e1o.pack(fill='x', padx=12, pady=(10, 6))
ttk.Checkbutton(e1, text='Send the daily activity report + backup files by e-mail automatically', variable=mail_on, style='Card.TCheckbutton').pack(anchor='w')
er = tk.Frame(e1, bg='white'); er.pack(fill='x', pady=(10, 4))
lbl(er, 'Send to (e-mail address)', fg=INK, font=FB, width=24, anchor='w').pack(side='left'); ttk.Entry(er, textvariable=mail_to).pack(side='left', fill='x', expand=True)
note(e1, 'Several addresses: separate them with a comma. Empty = the report is sent to the sender e-mail itself.').pack(anchor='w')
et = tk.Frame(e1, bg='white'); et.pack(fill='x', pady=4)
lbl(et, 'Send every day at', width=24, anchor='w').pack(side='left'); ttk.Entry(et, textvariable=mail_time, width=8, justify='center').pack(side='left'); lbl(et, '  (24-hour, e.g. 20:00)').pack(side='left')
e2o, e2 = make_card(bm, 'Sender account  (the e-mail the reports are sent FROM)'); e2o.pack(fill='x', padx=12, pady=6)
for text, var, wd, show in (('SMTP server', mail_server, 28, ''), ('Port', mail_port, 8, ''), ('Sender e-mail', mail_user, 34, ''), ('Password', mail_pass, 30, '*')):
    rr = tk.Frame(e2, bg='white'); rr.pack(fill='x', pady=2); lbl(rr, text, width=24, anchor='w').pack(side='left'); en = ttk.Entry(rr, textvariable=var, width=wd, show=show); en.pack(side='left')
    if text == 'Password': mail_pw = en; ttk.Checkbutton(rr, text='Show', style='Card.TCheckbutton', command=lambda: mail_pw.config(show='' if mail_pw.cget('show') else '*')).pack(side='left', padx=12)
note(e2, 'Gmail: server smtp.gmail.com, port 587, and use an "App password" (Google account > Security > 2-Step Verification > App passwords) - not the normal password. '
         'Outlook / Office 365: smtp.office365.com, port 587. The password is stored on this PC only.').pack(anchor='w', pady=(6, 0))
MAIL = {'status': 'Not sent yet', 'tried': 0.0}


def send_daily(auto=False):
    try:
        n = daily_mail()
        if auto: cfg['mail_last'] = date.today().isoformat(); save_json(CFG_FILE, cfg)          # only the scheduled e-mail counts as 'sent today'
        MAIL['status'] = f'Last e-mail sent {datetime.now():%d %b %H:%M} ({n} activity entries)'; log(MAIL['status'])
    except Exception as e:
        MAIL['status'] = f'E-mail FAILED: {e}'; log(MAIL['status'])


def send_test():
    try: send_mail('Enroll Sync test', 'This is a test e-mail from Enroll Sync. The daily report will arrive the same way.', [], to=None); MAIL['status'] = f'Test e-mail sent {datetime.now():%H:%M}'
    except Exception as e: MAIL['status'] = f'E-mail FAILED: {e}'
    log(MAIL['status'])


def check_gmail():
    """Log in with the saved sender e-mail + password (nothing is sent) and show whether it works."""
    try:
        _smtp_login().quit()
        MAIL['status'] = f'Gmail login OK ({cfg["mail_user"]}) - ' + ('daily e-mails are sent from this account' if cfg.get('mail_on') else 'tick "Send ... automatically" and Save to start the daily e-mails')
    except Exception as e: MAIL['status'] = f'Gmail login FAILED: {e}'
    log(MAIL['status'])


def save_mail():
    if save() and cfg['mail_user'] and cfg['mail_pass']: threading.Thread(target=check_gmail, daemon=True).start()     # after saving the account, log in at once to prove it works


def mail_due():
    """True from the set time on (every day)."""
    try: h, m = (int(x) for x in cfg.get('mail_time', '20:00').split(':'))
    except ValueError: h, m = 20, 0
    return datetime.now() >= datetime.combine(date.today(), dtime(h, m))


def mail_loop():
    while True:
        time.sleep(30)
        try:
            if cfg.get('mail_on') and cfg.get('mail_user') and cfg.get('mail_pass') and mail_due() and cfg.get('mail_last') != date.today().isoformat() and time.time() - MAIL['tried'] > 600:
                MAIL['tried'] = time.time(); send_daily(True)
        except Exception as e: log(f'E-mail timer: {e}')


eb = tk.Frame(bm, bg=BG); eb.pack(fill='x', padx=12, pady=8)
ttk.Button(eb, text='Save', style='Primary.TButton', command=save_mail).pack(side='left')
ttk.Button(eb, text='Check Gmail login', command=lambda: save() and threading.Thread(target=check_gmail, daemon=True).start()).pack(side='left', padx=8)
ttk.Button(eb, text='Send test e-mail', command=lambda: save() and threading.Thread(target=send_test, daemon=True).start()).pack(side='left', padx=8)
ttk.Button(eb, text='Send daily report now', command=lambda: save() and threading.Thread(target=send_daily, daemon=True).start()).pack(side='left')
mstat = tk.StringVar(); tk.Label(bm, textvariable=mstat, bg=BG, fg=INK, font=FN).pack(anchor='w', padx=14)

# ---- live log (under every tab)
lo_o, lo_b = make_card(root, None, px=8, py=6)
box = tk.Text(lo_b, height=3, font=('Consolas', 9), bg='#111111', fg='#f2f2f2', relief='flat', wrap='word', bd=0, padx=8, pady=6); box.pack(fill='both', expand=True)
lo_o.pack(side='bottom', fill='x', padx=12, pady=(0, 10), before=nb)


def conn_text(ip):
    ms = MSTAT.get(ip) if ip else None
    if not ip: return '-', MUTED
    if not ms or ms['online'] is None: return '\u25cb Checking...', MUTED
    return ('\u25cf Connected', GREEN) if ms['online'] else ('\u25cf Offline', RED)


tick = [0]


def poll():
    while not q.empty(): box.insert('end', q.get() + '\n'); box.see('end')
    if EDIT['on'] and time.time() > EDIT['until']: set_lock(True)
    tick[0] += 1
    WATCH[:] = [enr.get().strip()] + [r['ip'].get().strip() for r in mrows]
    t, c = conn_text(enr.get().strip()); enr_st.config(text=t, fg=c); enr_last.config(text=(MSTAT.get(enr.get().strip()) or {}).get('last', ''))
    for r in mrows:
        ip = r['ip'].get().strip(); t, c = conn_text(ip); r['st'].config(text=t, fg=c); r['last'].config(text=(MSTAT.get(ip) or {}).get('last', ''))
    run = bool(auto_t[0] and auto_t[0].is_alive() and not STOP.is_set())
    pill.config(text='\u25cf  RUNNING' if run else '\u25cf  STOPPED', bg=RED if run else '#eeeeee', fg='white' if run else INK)
    list_status.set(f'{LIST["result"]}\nLast update: {LIST["time"]}' + (f'   |   next download {datetime.fromtimestamp(LIST["next"]):%H:%M}' if LIST['next'] > time.time() else '') + f'   |   {LIST["cols"] or "columns not detected yet"}'
                    + (f'\nRegister saved: {REG["file"]}' if REG['file'] else ''))
    sig = (LIST['time'], date.today(), LIST['result'])
    if sig != lv_sig[0]: lv_sig[0] = sig; show_leavers()
    mstat.set(MAIL['status'] + (f'   |   daily e-mail at {cfg["mail_time"]}' + (' - already sent today' if cfg.get('mail_last') == date.today().isoformat() else '') if cfg.get('mail_on') else '   |   automatic e-mail is off'))
    if tick[0] % 20 == 1:
        try: n, f, fc, cd, last = backup_stats(); bstat.set(f'{n} employees in the backup   |   {f} with fingerprints, {fc} with face, {cd} with RFID card   |   last update: {last}')
        except Exception as e: bstat.set(f'backup database: {e}')
    root.after(500, poll)


root.protocol('WM_DELETE_WINDOW', lambda: (root.iconify(), log('The window cannot be closed - it was minimized. To exit use the Exit button (password).')))
if ask_password('Enter the password to open the program', login=True):
    root.deiconify(); set_lock(True)
    for _fn in (status_loop, mail_loop): threading.Thread(target=_fn, daemon=True).start()
    load_cached_list()
    poll(); root.mainloop()
else:
    root.destroy()
