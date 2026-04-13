from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
DRAFTS_FOLDER = 'rascunhos'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DRAFTS_FOLDER, exist_ok=True)


def listar_rascunhos():
    rascunhos = []

    for arquivo in os.listdir(DRAFTS_FOLDER):
        if arquivo.endswith('.json'):
            caminho = os.path.join(DRAFTS_FOLDER, arquivo)

            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            rascunhos.append({
                'id': arquivo.replace('.json', ''),
                'titulo': dados.get('titulo_relatorio', 'Relatório sem título'),
                'chassi': dados.get('chassi', ''),
                'modelo': dados.get('modelo', ''),
                'proprietario': dados.get('proprietario', ''),
                'data_relatorio': dados.get('data_relatorio', ''),
                'ultima_edicao': dados.get('ultima_edicao', ''),
                'num_fotos': len(dados.get('fotos', []))
            })

    rascunhos.sort(key=lambda x: x.get('ultima_edicao', ''), reverse=True)
    return rascunhos


def carregar_rascunho(relatorio_id):
    caminho = os.path.join(DRAFTS_FOLDER, f'{relatorio_id}.json')

    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {}


def salvar_rascunho(relatorio_id, dados):
    caminho = os.path.join(DRAFTS_FOLDER, f'{relatorio_id}.json')

    dados['ultima_edicao'] = datetime.now().strftime('%d/%m/%Y %H:%M')

    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def formatar_data(data_str):
    if not data_str:
        return ''
    try:
        dt = datetime.strptime(data_str[:16], '%Y-%m-%dT%H:%M')
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return data_str


@app.route('/')
def dashboard():
    rascunhos = listar_rascunhos()
    return render_template('dashboard.html', rascunhos=rascunhos)


@app.route('/novo')
def novo_relatorio():
    relatorio_id = str(uuid.uuid4())

    rascunho = {
        'relatorio_id': relatorio_id,
        'data_relatorio': datetime.now().strftime('%Y-%m-%dT%H:%M'),
        'tecnicos': ['']
    }

    return render_template('index.html', rascunho=rascunho)


@app.route('/editar/<relatorio_id>')
def editar_relatorio(relatorio_id):
    rascunho = carregar_rascunho(relatorio_id)

    if not rascunho:
        return redirect(url_for('dashboard'))

    return render_template('index.html', rascunho=rascunho)


@app.route('/salvar_rascunho', methods=['POST'])
def salvar_draft():
    relatorio_id = request.form.get('relatorio_id') or str(uuid.uuid4())

    tecnicos = [t for t in request.form.getlist('tecnicos[]') if t.strip()]

    data_relatorio = request.form.get('data_relatorio', '')
    titulo_relatorio = 'Relatório de Campo'

    if data_relatorio:
        try:
            data_obj = datetime.strptime(data_relatorio[:10], '%Y-%m-%d')
            chassi = request.form.get('chassi') or 'S/N'
            titulo_relatorio = f"Relatório de Campo - {chassi} - {data_obj.strftime('%d-%m-%Y')}"
        except Exception:
            pass

    # Fotos existentes (que não foram removidas)
    fotos_existentes = request.form.getlist('fotos_existentes')

    dados = {
        'relatorio_id': relatorio_id,
        'titulo_relatorio': titulo_relatorio,
        'chassi': request.form.get('chassi', ''),
        'modelo': request.form.get('modelo', ''),
        'proprietario': request.form.get('proprietario', ''),
        'cidade': request.form.get('cidade', ''),
        'data_relatorio': data_relatorio,
        'tecnicos': tecnicos,
        'informacao': request.form.get('informacao', ''),
        'situacao': request.form.get('situacao', ''),
        'servico': request.form.get('servico', ''),
        'fotos': fotos_existentes
    }

    arquivos = request.files.getlist('fotos')

    for arquivo in arquivos:
        if arquivo and arquivo.filename:
            nome = secure_filename(arquivo.filename)
            nome_unico = datetime.now().strftime('%Y%m%d%H%M%S%f') + '_' + nome
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
            arquivo.save(caminho)
            dados['fotos'].append(nome_unico)

    salvar_rascunho(relatorio_id, dados)

    return redirect(url_for('editar_relatorio', relatorio_id=relatorio_id))


@app.route('/excluir_rascunho/<relatorio_id>', methods=['POST'])
def excluir_rascunho(relatorio_id):
    caminho = os.path.join(DRAFTS_FOLDER, f'{relatorio_id}.json')

    if os.path.exists(caminho):
        # Remove fotos associadas ao rascunho
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        for foto in dados.get('fotos', []):
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto)
            if os.path.exists(foto_path):
                os.remove(foto_path)

        os.remove(caminho)

    return redirect(url_for('dashboard'))


@app.route('/gerar_relatorio', methods=['POST'])
def gerar_relatorio():
    relatorio_id = request.form.get('relatorio_id') or str(uuid.uuid4())

    dados = carregar_rascunho(relatorio_id)

    if not dados:
        return redirect(url_for('dashboard'))

    titulo_relatorio = dados.get('titulo_relatorio', 'Relatório de Campo')
    fotos_salvas = dados.get('fotos', [])

    # Formata data para exibição
    dados['data_formatada'] = formatar_data(dados.get('data_relatorio', ''))

    return render_template(
        'relatorio.html',
        dados=dados,
        fotos=fotos_salvas,
        titulo_relatorio=titulo_relatorio
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
