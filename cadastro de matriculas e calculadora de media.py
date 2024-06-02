import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3

class DBError(sqlite3.Error):
    pass

class DB:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as error:
            raise DBError(f"Erro ao conectar ao banco de dados: {error}")

    def close(self):
        if self.conn:
            self.conn.close()

    def create_table_alunos(self):
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Aluno (
                matricula INTEGER PRIMARY KEY,
                nome TEXT, 
                av1 REAL,
                av2 REAL,
                media REAL,
                UNIQUE(matricula)
            )
            """)
            self.conn.commit()
        except sqlite3.Error as error:
            raise DBError(f"Erro ao criar a tabela 'alunos': {error}")

    def add_aluno(self, matricula, nome, av1, av2, media):
        try:
            if self.search_matricula(matricula, True):
                raise DBError(f"Já existe um aluno com a matrícula {matricula}")
            self.cursor.execute(
                "INSERT INTO Aluno (matricula, nome, av1, av2, media) VALUES (?, ?, ?, ?, ?)",
                (matricula, nome, av1, av2, media)
            )
            self.conn.commit()
        except sqlite3.Error as error:
            raise DBError(f"Erro ao adicionar aluno: {error}")

    def search_aluno(self, matricula):
        try:
            if not self.search_matricula(matricula, True):
                raise DBError('Aluno não existe')
            self.cursor.execute("SELECT * FROM Aluno WHERE matricula = ?", (matricula,))
            aluno_existente = self.cursor.fetchone()
            return aluno_existente
        except sqlite3.Error as error:
            raise DBError(f"Erro ao procurar aluno: {error}")

    def search_matricula(self, matricula, return_bool=False):
        try:
            self.cursor.execute("SELECT matricula FROM Aluno WHERE matricula = ?", (matricula,))
            matricula = self.cursor.fetchone()
            if not return_bool:
                return matricula is not None
            return matricula
        except sqlite3.Error:
            raise DBError('Erro ao procurar matrícula')

    def search_matriculas(self):
        try:
            self.cursor.execute("SELECT matricula FROM Aluno")
            matriculas = self.cursor.fetchall()
            return matriculas
        except sqlite3.Error as error:
            raise DBError(f'Erro ao procurar matrículas: {error}')

class App(tk.Tk):
    def __init__(self, title, database: DB):
        super().__init__()
        self.title(title)
        self.minsize(width=300, height=200)
        self.entry_vars = dict()
        self.db = database
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.start()

    def widget(self, labelText):
        label = tk.Label(self, text=labelText)
        label.pack()
        entry_var = tk.StringVar()
        self.entry_vars[labelText] = entry_var
        label_entry = tk.Entry(self, textvariable=entry_var)
        label_entry.pack(pady=6)

    def button(self, text, parent_frame, action):
        btn = tk.Button(parent_frame, text=text, command=action, padx=15, pady=6)
        btn.pack(side="left")

    def errorMsg(self, msg):
        messagebox.showerror('Error', msg)

    def infoMsg(self, title, msg):
        messagebox.showinfo(title=title, message=msg)

    def cadastrar(self):
        matricula = self.entry_vars['Matricula'].get()
        nome = self.entry_vars['Nome'].get()
        av1 = self.entry_vars['Av1'].get()
        av2 = self.entry_vars['Av2'].get()
        if not matricula or not nome or not av1 or not av2:
            self.errorMsg("Error: Alguns campos estão vazios.")
            return
        try:
            matricula = int(matricula)
            if int(matricula) <= 0:
                self.errorMsg("Error: Matricula não pode ser menor ou igual a zero")
                return
            av1 = float(av1)
            av2 = float(av2)
            media = round((av1 + av2) / 2, 2)
            self.db.add_aluno(matricula, nome, av1, av2, media)
            self.infoMsg('Sucesso', f'Aluno cadastrado com sucesso')
        except ValueError:
            self.errorMsg('Error: Campos "Matricula", "Av1" e "Av2" devem ser numéricos')
            return
        except DBError as error:
            self.errorMsg(str(error))

    def start(self):
        self.widget('Matricula')
        self.widget('Nome')
        self.widget('Av1')
        self.widget('Av2')
        casdastro_btn_Frame = tk.Frame(self)
        casdastro_btn_Frame.pack(pady=10)
        self.button('Cadastrar', parent_frame=casdastro_btn_Frame, action=self.cadastrar)
        self.button('Ver Alunos', parent_frame=casdastro_btn_Frame, action=self.janela_verAlunos)
        self.db.connect()
        self.db.create_table_alunos()

    def janela_verAlunos(self):
        nova_janela = JanelaFilha(self, 'Ver alunos cadastrados', self.db)
        nova_janela.mainloop()

    def on_closing(self):
        self.db.close()
        self.destroy()

class JanelaFilha(tk.Toplevel):
    def __init__(self, master, title, database):
        super().__init__(master)
        self.title(title)
        self.minsize(width=300, height=200)
        self.db = database
        self.result = None
        self.start()

    def start(self):
        self.select('Selecione uma matrícula')

    def select(self, labelTxt):
        label = tk.Label(self, text=labelTxt)
        label.pack()
        current_var = tk.StringVar()
        selecionar = ttk.Combobox(self, textvariable=current_var)
        selecionar['values'] = tuple(valor for tupla in self.db.search_matriculas() for valor in tupla)
        selecionar['state'] = 'readonly'
        selecionar.bind('<<ComboboxSelected>>', self.ver_aluno)
        selecionar.pack(fill=tk.X, padx=5, pady=5)
        self.result = tk.Label(self, text='')
        self.result.pack()

    def ver_aluno(self, event):
        selected_value = int(event.widget.get())
        aluno = self.db.search_aluno(selected_value)
        matricula, nome, av1, av2, media = aluno
        self.result.config(text=f'Matrícula: {matricula}\nNome: {nome}\nAv1: {av1}\nAv2: {av2}\nMédia: {media}')

db = DB('alunos.db')
app = App('Cadastro de Alunos', db)
app.mainloop()
app.db.close()
