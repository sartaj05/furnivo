import shutil
import subprocess
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def backup_database(app):
    folder = Path(app.config['BACKUP_FOLDER']); folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    if uri.startswith('sqlite:///'):
        source = Path(uri.replace('sqlite:///', '', 1))
        if not source.is_absolute(): source = Path(app.root_path).parent / source
        if not source.exists(): raise RuntimeError('SQLite database file does not exist yet.')
        target = folder / f'furnivo-{stamp}.db'; shutil.copy2(source, target)
    elif uri.startswith(('postgresql://', 'postgresql+psycopg://', 'postgres://')):
        target = folder / f'furnivo-{stamp}.dump'
        try: subprocess.run(['pg_dump', uri, '--format=custom', '--file', str(target)], check=True, capture_output=True, text=True, timeout=120)
        except FileNotFoundError as exc: raise RuntimeError('pg_dump is required for PostgreSQL backups.') from exc
        except subprocess.CalledProcessError as exc: raise RuntimeError(exc.stderr.strip() or 'PostgreSQL backup failed.') from exc
    elif uri.startswith(('mysql://', 'mysql+pymysql://')):
        target = folder / f'furnivo-{stamp}.sql'
        parsed = urlparse(uri.replace('mysql+pymysql://', 'mysql://', 1)); database = parsed.path.lstrip('/')
        command = ['mysqldump', f'--host={parsed.hostname}', f'--port={parsed.port or 3306}', f'--user={parsed.username}', database]
        try:
            with target.open('w', encoding='utf-8') as stream: subprocess.run(command, stdout=stream, stderr=subprocess.PIPE, check=True, text=True, timeout=120)
        except FileNotFoundError as exc: raise RuntimeError('mysqldump is required for MySQL backups.') from exc
        except subprocess.CalledProcessError as exc: raise RuntimeError(exc.stderr.strip() or 'MySQL backup failed.') from exc
    else:
        raise RuntimeError('Unsupported database backup driver.')
    return {'filename': target.name, 'path': str(target), 'size_bytes': target.stat().st_size, 'created_at': datetime.now(timezone.utc).isoformat()}


def list_backups(app):
    folder = Path(app.config['BACKUP_FOLDER']); folder.mkdir(parents=True, exist_ok=True)
    return [{'filename': path.name, 'size_bytes': path.stat().st_size, 'created_at': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()} for path in sorted(folder.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True) if path.is_file() and path.name != '.gitkeep']


def backup_path(app, filename):
    folder = Path(app.config['BACKUP_FOLDER']).resolve()
    candidate = (folder / str(filename)).resolve()
    if candidate.parent != folder or not candidate.is_file(): return None
    return candidate


def verify_backup(app, filename):
    path = backup_path(app, filename)
    if not path: return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'filename': path.name, 'size_bytes': path.stat().st_size, 'sha256': digest, 'valid': path.stat().st_size > 0}


def restore_backup(app, filename):
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not uri.startswith('sqlite:///') or uri.endswith(':memory:'):
        raise RuntimeError('Automatic restore is available for SQLite. Use pg_restore or mysql client for remote databases.')
    source = backup_path(app, filename)
    if not source: raise FileNotFoundError('Backup file not found.')
    target = Path(uri.replace('sqlite:///', '', 1))
    if not target.is_absolute(): target = Path(app.root_path).parent / target
    safety = backup_database(app)
    shutil.copy2(source, target)
    return {'restored': source.name, 'target': str(target), 'safety_backup': safety['filename'], 'restored_at': datetime.now(timezone.utc).isoformat()}
