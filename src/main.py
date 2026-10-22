#!/usr/bin/env python3
# Hactool GUI cross-platform Qt interface
from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QProcess, QSettings, QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog, QTextEdit,
    QCheckBox, QMessageBox, QGroupBox, QScrollArea, QSizePolicy, QFrame,
)

APP_VERSION = "3.7.0"
ROOT = Path(__file__).resolve().parent.parent

def resource(name):
    return Path(getattr(sys, '_MEIPASS', ROOT)) / name

def engine():
    return resource('src/extract.py')

def bundled_hactool():
    """Resolve hactool bundled by the installer; never download at runtime."""
    platform_name = 'windows' if sys.platform == 'win32' else 'macos' if sys.platform == 'darwin' else 'linux'
    executable = 'hactool.exe' if platform_name == 'windows' else 'hactool'
    candidates = [resource(f'bin/{platform_name}/{executable}')]
    # macOS app bundles and PyInstaller may resolve resources differently.
    if getattr(sys, 'frozen', False):
        candidates.append(Path(sys.executable).resolve().parent / 'bin' / platform_name / executable)
    for candidate in candidates:
        if candidate.is_file() and (sys.platform == 'win32' or os.access(candidate, os.X_OK)):
            return candidate
    raise FileNotFoundError(
        f'No se incluyó hactool para {platform_name} en esta compilación. '
        'Recompila con el binario correspondiente en bin/; no se solicitará al usuario final.'
    )

PALETTES = {
    'Oscuro': dict(bg='#080F23', surface='#101D3B', input='#162747', fg='#F1F7FF', muted='#AFC2E7', border='#314C84', accent='#18C8F7', accentfg='#061428', hover='#348AFF'),
    'Claro': dict(bg='#F4F8FF', surface='#FFFFFF', input='#EDF4FF', fg='#10234A', muted='#526887', border='#B7CBE8', accent='#0879E4', accentfg='#FFFFFF', hover='#0061C4'),
}

def theme_styles(name):
    c = PALETTES[name]
    return f'''
    QWidget {{ background-color:{c['bg']}; color:{c['fg']}; font-size:13px; }}
    QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget {{ background:{c['bg']}; }}
    QLabel {{ background:transparent; }}
    QLabel#subtitle, QLabel#hint {{ color:{c['muted']}; }}
    QLabel#heading {{ color:{c['accent']}; font-size:25px; font-weight:800; }}
    QGroupBox {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:12px; margin-top:14px; padding:16px 12px 12px; font-weight:600; }}
    QGroupBox::title {{ subcontrol-origin:margin; left:14px; padding:0 6px; background:{c['surface']}; }}
    QLineEdit, QComboBox, QTextEdit {{ background:{c['input']}; color:{c['fg']}; border:1px solid {c['border']}; border-radius:7px; padding:7px; selection-background-color:{c['hover']}; selection-color:white; }}
    QLineEdit:disabled, QComboBox:disabled {{ background:{c['surface']}; color:{c['muted']}; }}
    QComboBox::drop-down {{ background:{c['surface']}; border:0; border-left:1px solid {c['border']}; width:25px; border-top-right-radius:7px; border-bottom-right-radius:7px; }}
    QComboBox QAbstractItemView, QListView {{ background:{c['surface']}; color:{c['fg']}; border:1px solid {c['border']}; selection-background-color:{c['hover']}; selection-color:white; outline:0; }}
    QComboBox QAbstractItemView::item {{ padding:7px; min-height:23px; }}
    QPushButton {{ background:{c['surface']}; color:{c['fg']}; border:1px solid {c['border']}; border-radius:8px; padding:8px 12px; font-weight:600; }}
    QPushButton:hover {{ border-color:{c['hover']}; background:{c['input']}; }}
    QPushButton#primary {{ background:{c['accent']}; color:{c['accentfg']}; border:none; }}
    QPushButton#primary:hover {{ background:{c['hover']}; color:white; }}
    QPushButton:disabled {{ color:{c['muted']}; }}
    QScrollArea {{ border:0; }}
    QCheckBox {{ spacing:9px; }}
    QCheckBox::indicator {{ width:16px; height:16px; }}
    QToolTip {{ background:{c['surface']}; color:{c['fg']}; border:1px solid {c['border']}; }}
    QMessageBox {{ background:{c['surface']}; }}
    '''

def theme_palette(name):
    c=PALETTES[name]
    p=QPalette()
    for role,color in [(QPalette.ColorRole.Window,c['bg']),
                       (QPalette.ColorRole.WindowText,c['fg']),
                       (QPalette.ColorRole.Base,c['input']),
                       (QPalette.ColorRole.AlternateBase,c['surface']),
                       (QPalette.ColorRole.Text,c['fg']),
                       (QPalette.ColorRole.Button,c['surface']),
                       (QPalette.ColorRole.ButtonText,c['fg']),
                       (QPalette.ColorRole.Highlight,c['hover']),
                       (QPalette.ColorRole.HighlightedText,'#FFFFFF'),
                       (QPalette.ColorRole.ToolTipBase,c['surface']),
                       (QPalette.ColorRole.ToolTipText,c['fg'])]:
        p.setColor(role,QColor(color))
    return p

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('AlexGarci', 'HactoolGUI')
        self.process = None
        self.completed = False
        self.setWindowTitle('Hactool GUI — ALEX GARCI')
        self.setWindowIcon(QIcon(str(resource('assets/icon.png'))))
        self.resize(960, 740)
        self.setMinimumSize(610, 500)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        self.v = QVBoxLayout(body)
        self.v.setContentsMargins(22, 20, 22, 20)
        self.v.setSpacing(14)
        scroll.setWidget(body)
        self.setCentralWidget(scroll)

        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QIcon(str(resource('assets/icon.png'))).pixmap(62, 62))
        header.addWidget(logo)
        titlecol = QVBoxLayout()
        title = QLabel('Hactool GUI')
        title.setObjectName('heading')
        titlecol.addWidget(title)
        sub = QLabel('Extractor NSP / XCI / NCA · v' + APP_VERSION)
        sub.setObjectName('subtitle')
        titlecol.addWidget(sub)
        header.addLayout(titlecol)
        header.addStretch()
        header.addWidget(QLabel('Tema'))
        self.theme = QComboBox()
        self.theme.addItems(['Sistema','Oscuro','Claro'])
        self.theme.setCurrentText(self.settings.value('theme','Sistema'))
        self.theme.currentTextChanged.connect(self.apply_theme)
        self.theme.setMinimumWidth(105)
        header.addWidget(self.theme)
        about = QPushButton('Acerca de…')
        about.clicked.connect(self.about)
        header.addWidget(about)
        self.v.addLayout(header)

        box = QGroupBox('Extracción')
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        self.mode = QComboBox()
        self.mode.addItem('Automático (NSP / XCI / NCA)', 'auto')
        self.mode.addItem('NSP (solo extraer NCA)', 'pfs0')
        self.mode.addItem('NCA individual', 'nca')
        grid.addWidget(QLabel('Operación'), 0, 0)
        grid.addWidget(self.mode, 0, 1, 1, 2)
        self.inputs = {}
        self.field_status = {}
        self._validation_ready = False
        rows = [('input','Archivo del juego'), ('destination','Carpeta de destino'), ('prod','prod.keys'), ('title','title.keys (opcional)')]
        for r, (key, label) in enumerate(rows, 1):
            grid.addWidget(QLabel(label),r,0)
            field = QLineEdit()
            field.setPlaceholderText('Seleccionar ' + label.lower())
            field.setText(str(self.settings.value('path_'+key,'')))
            field.setAccessibleName(label)
            grid.addWidget(field,r,1)
            btn = QPushButton('Examinar…')
            btn.clicked.connect(lambda _=False, k=key: self.browse(k))
            grid.addWidget(btn,r,2)
            self.inputs[key]=field
            field.editingFinished.connect(lambda k=key: self.validate_selection(k, notify=True))
            field.textChanged.connect(lambda _text, k=key: self.mark_pending(k))
        self.keep = QCheckBox('Conservar archivos NCA intermedios')
        grid.addWidget(self.keep, 5, 0, 1, 3)
        hint = QLabel('Las claves se procesan localmente. No se muestran en el registro. Usa únicamente archivos propios y autorizados.')
        hint.setObjectName('hint')
        hint.setWordWrap(True)
        grid.addWidget(hint,6,0,1,3)
        self.v.addWidget(box)
        self.validation_label = QLabel('Selecciona archivos para validarlos inmediatamente.')
        self.validation_label.setObjectName('hint')
        self.validation_label.setWordWrap(True)
        self.v.addWidget(self.validation_label)
        self._validation_ready = True
        self.mode.currentIndexChanged.connect(lambda _index: self.validate_selection('input', notify=True))

        controls = QHBoxLayout()
        self.start_btn = QPushButton('▶  Extraer')
        self.start_btn.setObjectName('primary')
        self.start_btn.clicked.connect(self.start)
        controls.addWidget(self.start_btn)
        self.cancel_btn = QPushButton('Cancelar')
        self.cancel_btn.clicked.connect(self.cancel)
        self.cancel_btn.setEnabled(False)
        controls.addWidget(self.cancel_btn)
        destbtn = QPushButton('Abrir destino')
        destbtn.clicked.connect(self.open_dest)
        controls.addWidget(destbtn)
        controls.addStretch()
        self.status = QLabel('Listo')
        self.status.setObjectName('subtitle')
        controls.addWidget(self.status)
        self.v.addLayout(controls)

        loghead = QHBoxLayout()
        loghead.addWidget(QLabel('Registro de extracción'))
        loghead.addStretch()
        clear = QPushButton('🗑  Limpiar registro')
        clear.clicked.connect(self.clear_log)
        self.clear_btn=clear
        loghead.addWidget(clear)
        self.v.addLayout(loghead)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont('Menlo' if sys.platform=='darwin' else 'Monospace', 10))
        self.log.setMinimumHeight(190)
        self.log.setPlainText('Selecciona el juego, las claves y el destino para comenzar.\n')
        self.v.addWidget(self.log,1)
        footer=QLabel('Diseño e integración: ALEX GARCI  ·  Motor de extracción: hactool (SciresM y colaboradores)  ·  Python  ·  Qt/PySide6')
        footer.setObjectName('hint')
        footer.setWordWrap(True)
        self.v.addWidget(footer)
        self.apply_theme(self.theme.currentText())

    def apply_theme(self, name):
        self.settings.setValue('theme', name)
        if name=='Sistema':
            # Detect system theme via Qt palette, independent of our custom stylesheet.
            pal=QApplication.style().standardPalette()
            from PySide6.QtGui import QPalette
            color=pal.color(QPalette.ColorRole.Window)
            name='Oscuro' if color.lightness()<128 else 'Claro'
        QApplication.instance().setPalette(theme_palette(name))
        QApplication.instance().setStyleSheet(theme_styles(name))
        for combo in (self.theme, self.mode):
            combo.view().setPalette(theme_palette(name))
            combo.view().setStyleSheet(theme_styles(name))

    def browse(self,key):
        current=self.inputs[key].text()
        if key=='destination':
            value=QFileDialog.getExistingDirectory(self,'Selecciona destino',current or str(Path.home()))
        else:
            filt={'input':'Juegos (*.nsp *.xci *.nca);;Todos (*)','prod':'Archivos de claves (*.keys);;Todos (*)','title':'Archivos de claves (*.keys);;Todos (*)'}[key]
            value,_=QFileDialog.getOpenFileName(self,'Selecciona '+key,current or str(Path.home()),filt)
        if value:
            self.inputs[key].setText(value)
            self.settings.setValue('path_'+key,value)
            self.validate_selection(key, notify=True)

    def mark_pending(self, key):
        if getattr(self, '_validation_ready', False):
            self.field_status.pop(key, None)

    def validate_selection(self, key, notify=False):
        if not getattr(self, '_validation_ready', False): return True
        from extract import validate_key_file
        value = self.inputs[key].text().strip()
        label = {'input':'Juego', 'prod':'prod.keys', 'title':'title.keys', 'destination':'Destino'}[key]
        if not value:
            if key == 'title':
                self.field_status[key] = True
                return True
            self.field_status[key] = False
            return False
        try:
            path = Path(value).expanduser()
            if key == 'destination':
                if path.exists() and not path.is_dir(): raise ValueError('El destino no es una carpeta.')
                detail = 'carpeta seleccionada'
            elif key == 'input':
                if not path.is_file(): raise ValueError('El archivo no existe.')
                allowed={'auto':{'.nsp','.xci','.nca'}, 'pfs0':{'.nsp'}, 'nca':{'.nca'}}[self.mode.currentData()]
                if path.suffix.lower() not in allowed: raise ValueError('El modo seleccionado admite: '+', '.join(sorted(allowed)))
                detail = 'archivo '+path.suffix.lower()+' compatible'
            else:
                other='title' if key=='prod' else 'prod'
                if self.inputs[other].text().strip() and path.resolve() == Path(self.inputs[other].text().strip()).expanduser().resolve():
                    raise ValueError('No puedes usar el mismo archivo para prod.keys y title.keys.')
                count=validate_key_file(path, kind=key)
                detail=f'{count} entradas válidas'
            self.field_status[key]=True
            self.validation_label.setText(f'✓ {label}: {detail}')
            if notify: self.append(f'[VALIDADO] {label}: {detail}.\n')
            self.inputs[key].setToolTip('Validado: '+detail)
            return True
        except (ValueError, OSError) as exc:
            self.field_status[key]=False
            self.validation_label.setText(f'✗ {label}: {exc}')
            self.inputs[key].setToolTip(str(exc))
            if notify:
                self.append(f'[RECHAZADO] {label}: {exc}\n')
                QMessageBox.warning(self, 'Archivo rechazado', f'{label}: {exc}')
            return False

    def append(self,text):
        cursor=self.log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def clear_log(self):
        if not self.process:
            self.log.setPlainText('Registro limpiado.\n')
            self.status.setText('Listo')

    def validation_error(self, heading, message):
        self.append(f"[VALIDACIÓN] {heading}: {message}\n")
        self.status.setText('Revisar selección')
        QMessageBox.warning(self, heading, message)

    def start(self):
        vals={k:v.text().strip() for k,v in self.inputs.items()}
        labels={'input':'archivo del juego','destination':'carpeta de destino','prod':'prod.keys','title':'title.keys'}
        for key in ('input','destination','prod'):
            if not vals[key]:
                self.validation_error('Falta información', f'Selecciona {labels[key]}.')
                return
        for key in ('input','prod','title','destination'):
            if not self.validate_selection(key, notify=True):
                return
        mode=self.mode.currentData()
        ext=Path(vals['input']).suffix.lower()
        allowed={ 'auto':{'.nsp','.xci','.nca'}, 'pfs0':{'.nsp'}, 'nca':{'.nca'} }
        if ext not in allowed.get(mode,set()):
            self.validation_error('Formato incompatible',
                f'Archivo seleccionado: {Path(vals["input"]).name}\n'
                f'Extensión detectada: {ext or "ninguna"}\n'
                f'Extensiones permitidas: {", ".join(sorted(allowed.get(mode,set())))}')
            return
        for key in ('input','prod','title'):
            if vals[key] and not Path(vals[key]).is_file():
                self.validation_error('Archivo inexistente',f'No existe {labels[key]}: {vals[key]}')
                return
        if not Path(vals['destination']).is_dir():
            try:
                Path(vals['destination']).mkdir(parents=True,exist_ok=True)
            except OSError as exc:
                self.validation_error('Destino inaccesible',str(exc))
                return
        try:
            from extract import validate_key_file
            prod_count=validate_key_file(Path(vals['prod']),kind='prod')
            self.append(f'[VALIDACIÓN] prod.keys: OK ({prod_count} entradas reconocidas).\n')
            if vals['title']:
                title_count=validate_key_file(Path(vals['title']),kind='title')
                self.append(f'[VALIDACIÓN] title.keys: OK ({title_count} entradas reconocidas).\n')
            else:
                self.append('[VALIDACIÓN] title.keys: no seleccionado (opcional).\n')
        except (OSError,ValueError) as exc:
            self.validation_error('Claves incompatibles',str(exc))
            return
        self.append(f'[VALIDACIÓN] Juego: OK ({ext}; modo {mode}).\n')
        for key,value in vals.items():
            if value:self.settings.setValue('path_'+key,value)
        try:
            hactool_path = str(bundled_hactool())
        except FileNotFoundError as exc:
            self.append('[ERROR] '+str(exc)+'\n')
            QMessageBox.critical(self, 'Instalación incompleta', str(exc))
            return
        # Run engine via Python interpreter; on PyInstaller use dedicated frozen CLI mode.
        if getattr(sys,'frozen',False):
            executable=sys.executable
            args=['--engine', '--hactool',hactool_path,'--input',vals['input'],'--destination',vals['destination'],'--prod',vals['prod'],'--mode',mode]
        else:
            executable=sys.executable
            args=[str(engine()),'--hactool',hactool_path,'--input',vals['input'],'--destination',vals['destination'],'--prod',vals['prod'],'--mode',mode]
        if vals['title']:args+=['--title',vals['title']]
        if self.keep.isChecked():args+=['--keep-nca']
        self.completed=False
        self._engine_buffer=''
        self.process=QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.clear_btn.setEnabled(False)
        self.status.setText('Extrayendo…')
        self.append('\n=== Nueva extracción ===\n')
        self.process.start(executable,args)

    def read_output(self):
        if self.process:
            chunk=bytes(self.process.readAllStandardOutput()).decode('utf-8',errors='replace')
            self._engine_buffer = getattr(self, '_engine_buffer', '') + chunk
            if 'EXTRACCIÓN COMPLETA:' in self._engine_buffer:self.completed=True
            self._engine_buffer=self._engine_buffer[-4096:]
            self.append(chunk)

    def finished(self,code,status):
        self.read_output()
        self.process=None
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        ok=code==0 and self.completed
        self.status.setText('Completado' if ok else 'Finalizado con error')
        if ok: QMessageBox.information(self,'Extracción completada','Los archivos se extrajeron correctamente.')
        else: QMessageBox.warning(self,'Extracción no completada','Revisa el registro para identificar el error.')

    def process_error(self,error):
        self.append('\nError al iniciar o ejecutar el proceso: '+str(error)+'\n')

    def cancel(self):
        if self.process:self.process.kill()

    def open_dest(self):
        p=self.inputs['destination'].text().strip()
        if p and Path(p).is_dir():QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        else:QMessageBox.information(self,'Destino','Selecciona una carpeta de destino existente.')

    def about(self):
        box=QMessageBox(self)
        box.setWindowTitle('Acerca de Hactool GUI')
        box.setIconPixmap(QIcon(str(resource('assets/icon.png'))).pixmap(70,70))
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(f'<h2>Hactool GUI {APP_VERSION}</h2><p><b>Diseño, interfaz e integración:</b> ALEX GARCI</p>'
                    '<p>Proyecto independiente, aún por publicarse en GitHub.</p>'
                    '<p><b>Créditos de componentes:</b><br>'
                    '<a href="https://github.com/SciresM/hactool">hactool — SciresM y colaboradores</a><br>'
                    '<a href="https://www.python.org/">Python — Python Software Foundation</a><br>'
                    '<a href="https://doc.qt.io/qtforpython-6/">PySide6 / Qt</a><br>'
                    '<a href="https://pyinstaller.org/">PyInstaller</a></p>'
                    '<p>Consulta las licencias originales de cada componente antes de redistribuir.</p>')
        box.exec()


def main():
    # In frozen app, --engine runs the bundled extraction module without loading Qt UI.
    if len(sys.argv)>1 and sys.argv[1]=='--engine':
        sys.argv=[sys.argv[0]]+sys.argv[2:]
        from extract import main as extract_main
        try: extract_main()
        except Exception as exc:
            from extract import say
            say('ERROR: '+str(exc))
            sys.exit(1)
        return
    app=QApplication(sys.argv)
    app.setStyle('Fusion')  # Uniform popups and dark theme on macOS, Windows and Linux
    app.setApplicationName('Hactool GUI')
    app.setOrganizationName('ALEX GARCI')
    app.setWindowIcon(QIcon(str(resource('assets/icon.png'))))
    win=MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__=='__main__':main()
