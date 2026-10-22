#!/usr/bin/env python3
"""Local extraction helper; never prints key material."""
import argparse, pathlib, re, subprocess, sys, tempfile, shutil, time, datetime, os

HEX32 = re.compile(r'^[0-9a-fA-F]{32}$')

def say(s):
    stamp=datetime.datetime.now().strftime('%H:%M:%S')
    # Completion marker intentionally has a stable prefix for the macOS interface.
    if s.startswith('EXTRACCIÓN COMPLETA: '): print(s, flush=True)
    else: print(f'[{stamp}] {s}', flush=True)

def safe_output(raw):
    """Display diagnostics without leaking hex key values or command-line titlekeys."""
    result=[]
    for line in raw.splitlines():
        line=re.sub(r'(?i)(--titlekey\s*[=:]\s*)[0-9a-f]{32}',r'\1[OCULTA]',line)
        line=re.sub(r'(?i)(\b(?:title\s*key|encrypted\s*titlekey|decrypted\s*titlekey|master\s*key|key\s*value)\s*[:=]\s*)[0-9a-f]{32,}',r'\1[OCULTA]',line)
        line=re.sub(r'(?i)(key\s*\()[0-9a-f]{32,}(\))',r'\1[OCULTA]\2',line)
        # Hide long standalone hex strings, retaining IDs of exactly 32 digits only in curated logs.
        line=re.sub(r'(?i)\b[0-9a-f]{32,}\b','[HEX OCULTO]',line)
        result.append(line[:400])
    return result


def validate_key_file(path, kind='prod'):
    """Validate key file structure without printing or persisting secret values."""
    if not path.is_file():
        raise ValueError(f'No existe el archivo de claves: {path}')
    if path.suffix.lower() != '.keys':
        raise ValueError(f'El archivo {kind}.keys debe tener extensión .keys.')
    if path.stat().st_size == 0:
        raise ValueError(f'El archivo {kind}.keys está vacío.')
    if path.stat().st_size > 5_000_000:
        raise ValueError(f'El archivo {kind}.keys supera el tamaño esperado (5 MB).')
    content=path.read_text(encoding='utf-8-sig',errors='replace')
    found=0
    for raw in content.splitlines():
        line=raw.strip()
        if not line or line.startswith(('#',';','//')): continue
        if '=' not in line: continue
        name,value=(v.strip() for v in line.split('=',1))
        if kind=='title':
            if HEX32.fullmatch(name) and HEX32.fullmatch(value): found+=1
        else:
            if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',name) and re.fullmatch(r'[0-9a-fA-F]{32,128}',value) and len(value)%2==0:
                found+=1
    if kind=='prod' and path.name.lower()=='title.keys':
        raise ValueError('Seleccionaste title.keys donde corresponde prod.keys.')
    if kind=='title' and path.name.lower()=='prod.keys':
        raise ValueError('Seleccionaste prod.keys donde corresponde title.keys.')
    if found == 0:
        if kind=='title':
            raise ValueError('title.keys no contiene pares Rights ID = clave de 32 dígitos hexadecimales. ¿Seleccionaste prod.keys por error?')
        raise ValueError('prod.keys no contiene entradas de claves válidas (nombre = valor hexadecimal). ¿Seleccionaste title.keys por error?')
    return found

def cleaned_keys(path, dest):
    skipped=[]; lines=[]
    for line in path.read_text(encoding='utf-8-sig', errors='replace').splitlines():
        stripped=line.strip()
        if '=' in stripped and not stripped.startswith(('#',';')):
            name,value=(v.strip() for v in stripped.split('=',1))
            if name.startswith(('master_kek_source_', 'mariko_master_kek_source_')) and not HEX32.fullmatch(value):
                skipped.append(name); continue
        lines.append(line)
    dest.write_text('\n'.join(lines)+'\n'); dest.chmod(0o600)
    say(f'Claves preparadas en copia temporal. Entradas incompatibles omitidas: {len(skipped)}')
    for name in skipped: say('  Omitida entrada incompatible: '+name)

def run_hactool(exe, args, label='Operación hactool'):
    # Never log the full command: --titlekey is sensitive.
    safe_args=[]
    for arg in args:
        if arg.startswith('--titlekey='): safe_args.append('--titlekey=[OCULTA]')
        else: safe_args.append(arg)
    say('INICIO: '+label)
    say('  Argumentos: '+ ' '.join(safe_args))
    start=time.monotonic()
    p=subprocess.run([str(exe), '--disablekeywarns', '--suppresskeys', *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
    elapsed=time.monotonic()-start
    say(f'  Resultado: código {p.returncode}; duración {elapsed:.2f} s')
    for line in safe_output(p.stdout): say('  stdout | '+line)
    for line in safe_output(p.stderr): say('  stderr | '+line)
    if p.returncode:
        raise RuntimeError(f'{label} falló (código {p.returncode}). Consulta las líneas stdout/stderr del registro.')
    return p.stdout

def title_for(path, rights):
    for line in path.read_text(encoding='utf-8-sig', errors='replace').splitlines():
        if '=' not in line or line.lstrip().startswith(('#',';')): continue
        name, val=(v.strip() for v in line.split('=',1))
        if name.lower()==rights.lower() and HEX32.fullmatch(val): return val
    return None

def ticket_for(container_dir, rights):
    """Read standard Switch ticket fields, never exposing key material."""
    for ticket in sorted(container_dir.rglob('*.tik')):
        try:
            data = ticket.read_bytes()
            if len(data) < 0x2B0:
                continue
            ticket_rights = data[0x2A0:0x2B0].hex()
            if ticket_rights.lower() != rights.lower():
                continue
            encrypted_titlekey = data[0x180:0x190]
            if len(encrypted_titlekey) != 16:
                continue
            return encrypted_titlekey.hex()
        except OSError:
            continue
    return None

def nca_info(exe, keypath, nca):
    """Inspect header without -i (which fails on some encrypted sections).

    A nonzero status is not fatal if hactool printed a usable header.
    """
    cmd=[str(exe), '--disablekeywarns', '--suppresskeys', '-k',str(keypath), '-t','nca',str(nca)]
    proc=subprocess.run(cmd, capture_output=True, text=True, errors='replace')
    output=proc.stdout+'\n'+proc.stderr
    c=re.search(r'Content Type:\s*(\w+)',output,re.I)
    r=re.search(r'Rights ID:\s*([0-9a-fA-F]{32})',output,re.I)
    if not c:
        say('ADVERTENCIA: No se pudo identificar '+nca.name+' (código '+str(proc.returncode)+').')
        for line in safe_output(proc.stderr)[:4]: say('  stderr | '+line)
    return (c.group(1).lower() if c else None, r.group(1) if r else None)

def extract_nca(exe, keys, titlefile, nca, output, container_dir=None, info=None):
    typ, rights = info if info is not None else nca_info(exe,keys,nca)
    say('NCA identificado: '+str(typ or 'desconocido'))
    if typ!='program': raise RuntimeError('El NCA seleccionado no es de tipo Program.')
    args=['-k',str(keys)]
    if rights and int(rights,16)!=0:
        tk=title_for(titlefile,rights) if titlefile else None
        if tk:
            say('Clave encontrada en title.keys (valor oculto).')
        elif container_dir:
            tk=ticket_for(container_dir,rights)
            if tk: say('Clave obtenida del ticket del contenedor (valor oculto).')
        if not tk:
            raise RuntimeError('No se encontró una clave de título correspondiente en title.keys ni en el ticket.')
        args.append('--titlekey='+tk)
    exefs=output/'ExeFS'; romfs=output/'RomFS'
    exefs.mkdir(parents=True,exist_ok=True); romfs.mkdir(parents=True,exist_ok=True)
    say('Extrayendo ExeFS y RomFS…')
    run_hactool(exe,[*args,'-t','nca',f'--exefsdir={exefs}',f'--romfsdir={romfs}',str(nca)],label='Extraer ExeFS y RomFS')
    a=sum(p.is_file() for p in exefs.rglob('*')); b=sum(p.is_file() for p in romfs.rglob('*'))
    say(f'Archivos ExeFS: {a} | RomFS: {b}')
    if a==0 or b==0: raise RuntimeError('Extracción incompleta: ExeFS o RomFS está vacío.')

def main():
    p=argparse.ArgumentParser()
    for flag in ('hactool','input','destination','prod'): p.add_argument('--'+flag,required=True)
    p.add_argument('--title',default=''); p.add_argument('--mode',choices=['auto','nca','pfs0'],default='auto')
    p.add_argument('--keep-nca',action='store_true')
    a=p.parse_args()
    exe=pathlib.Path(a.hactool).expanduser(); src=pathlib.Path(a.input).expanduser(); dest=pathlib.Path(a.destination).expanduser(); prod=pathlib.Path(a.prod).expanduser()
    title=pathlib.Path(a.title).expanduser() if a.title else None
    for f in [exe,src,prod,*([title] if title else [])]:
        if not f.is_file(): raise RuntimeError('No existe el archivo requerido: '+str(f))
    say('Versión extractor: 3.7.0')
    say('Archivo seleccionado: '+str(src))
    say('Modo solicitado: '+a.mode)
    say('Destino seleccionado: '+str(dest))
    say('prod.keys seleccionado: '+str(prod))
    say('title.keys seleccionado: '+(str(title) if title else 'No seleccionado; se intentará ticket'))
    if src.suffix.lower() not in (['.nca'] if a.mode=='nca' else ['.nsp'] if a.mode=='pfs0' else ['.nsp','.xci','.nca']):
        raise RuntimeError('Extensión de archivo de juego incompatible con el modo elegido.')
    say('Validación de extensión: OK ('+src.suffix.lower()+')')
    say(f'Validación prod.keys: OK ({validate_key_file(prod,kind="prod")} entradas)')
    if title: say(f'Validación title.keys: OK ({validate_key_file(title,kind="title")} entradas)')
    dest.mkdir(parents=True,exist_ok=True)
    output=dest/(src.stem+'_extraido'); output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='hactoolgui_keys_') as tmp:
        keys=pathlib.Path(tmp)/'prod.keys'; cleaned_keys(prod,keys)
        mode=a.mode
        if mode=='auto': mode='nca' if src.suffix.lower()=='.nca' else ('xci' if src.suffix.lower()=='.xci' else 'pfs0')
        if mode in ('pfs0','xci'):
            ncas=output/'NCAs'; ncas.mkdir(exist_ok=True)
            if mode=='xci':
                say('Extrayendo partición secure de XCI…')
                run_hactool(exe,['-k',str(keys),'-t','xci',f'--securedir={ncas}',str(src)],label='Extraer partición secure XCI')
            else:
                say('Extrayendo contenedor NSP/PFS0, incluyendo tickets si existen…')
                run_hactool(exe,['-k',str(keys),'-t','pfs0',f'--outdir={ncas}',str(src)],label='Extraer NSP/PFS0')
            found=sorted(ncas.rglob('*.nca'))
            say(f'Archivos NCA encontrados: {len(found)}')
            if not found: raise RuntimeError('No se encontraron archivos NCA en el contenedor.')
            if a.mode=='pfs0': say('Extracción NCA completada.')
            else:
                programs=[]
                for nca in found:
                    typ,rights=nca_info(exe,keys,nca)
                    say(f'{nca.name}: {typ or "desconocido"}')
                    if typ=='program': programs.append((nca,(typ,rights)))
                if not programs: raise RuntimeError('No se identificó ningún NCA de tipo Program. Comprueba las claves y la versión de hactool.')
                errors=[]; success=False
                for program, info in programs:
                    try:
                        extract_nca(exe,keys,title,program,output,ncas,info=info)
                        success=True
                        break
                    except RuntimeError as exc:
                        errors.append(str(exc))
                        say('ADVERTENCIA: NCA no extraíble; probando siguiente Program: '+str(exc))
                if not success: raise RuntimeError('Ningún NCA Program pudo extraerse: '+'; '.join(errors))
                if not a.keep_nca:
                    shutil.rmtree(ncas)
                    say('NCA intermedios eliminados (opción desactivada).')
        else:
            extract_nca(exe,keys,title,src,output)
    say('EXTRACCIÓN COMPLETA: '+str(output))

if __name__=='__main__':
    try: main()
    except Exception as e:
        say('ERROR: '+str(e)); sys.exit(1)
