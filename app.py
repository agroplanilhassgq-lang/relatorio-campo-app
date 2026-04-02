
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
DRAFT_FILE = 'rascunho.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def carregar_rascunho():
    if os.path.exists(DRAFT_FILE):
        with open(DRAFT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_rascunho(dados):
    with open(DRAFT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    rascunho = carregar_rascunho()

    if not rascunho.get('data_relatorio'):
        rascunho['data_relatorio'] = datetime.now().strftime('%Y-%m-%dT%H:%M')

    return render_template('index.html', rascunho=rascunho)

@app.route('/salvar_rascunho', methods=['POST'])
def salvar_draft():
    tecnicos = request.form.getlist('tecnicos[]')

    dados = {
        'chassi': request.form.get('chassi'),
        'modelo': request.form.get('modelo'),
        'proprietario': request.form.get('proprietario'),
        'cidade': request.form.get('cidade'),
        'data_relatorio': request.form.get('data_relatorio'),
        'tecnicos': tecnicos,
        'informacao': request.form.get('informacao'),
        'situacao': request.form.get('situacao'),
        'servico': request.form.get('servico')
    }

    salvar_rascunho(dados)
    return redirect(url_for('index'))

@app.route('/gerar_relatorio', methods=['POST'])
def gerar_relatorio():
    tecnicos = request.form.getlist('tecnicos[]')

    dados = {
        'chassi': request.form.get('chassi'),
        'modelo': request.form.get('modelo'),
        'proprietario': request.form.get('proprietario'),
        'cidade': request.form.get('cidade'),
        'data_relatorio': request.form.get('data_relatorio'),
        'tecnicos': [t for t in tecnicos if t.strip()],
        'informacao': request.form.get('informacao'),
        'situacao': request.form.get('situacao'),
        'servico': request.form.get('servico')
    }

    salvar_rascunho(dados)

    data_obj = datetime.strptime(dados['data_relatorio'][:10], '%Y-%m-%d')
    titulo_relatorio = f"Relatório de Campo - {dados['chassi']} - {data_obj.strftime('%d-%m-%Y')}"

    fotos_salvas = []
    arquivos = request.files.getlist('fotos')

    for arquivo in arquivos:
        if arquivo and arquivo.filename:
            nome = secure_filename(arquivo.filename)
            nome_unico = datetime.now().strftime('%Y%m%d%H%M%S%f') + '_' + nome
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
            arquivo.save(caminho)
            fotos_salvas.append(nome_unico)

    return render_template(
        'relatorio.html',
        dados=dados,
        fotos=fotos_salvas,
        titulo_relatorio=titulo_relatorio
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)