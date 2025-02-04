from flask import Flask, render_template, request, redirect, url_for, flash, session
import hashlib
import os

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # Chave secreta para sessões

# Dados de usuário (simulando um banco de dados)
usuarios = {"admin": hashlib.sha256("admin123".encode('utf-8')).hexdigest()}

# Função para carregar as atas do arquivo
def carregar_atas():
    atas = []
    if os.path.exists("atas.txt"):
        with open("atas.txt", "r") as arquivo:
            linhas = arquivo.readlines()
            i = 0
            while i < len(linhas):
                # Verifica se há linhas suficientes para uma ata completa
                if i + 4 >= len(linhas):
                    break

                titulo = linhas[i].strip().replace("Título: ", "")
                descricao = linhas[i + 1].strip().replace("Descrição: ", "")
                criador = linhas[i + 2].strip().replace("Criador: ", "")
                usuarios_adicionados = linhas[i + 3].strip().replace("Usuários: ", "").split(",")
                tarefas = []

                # Verifica se há tarefas
                j = i + 4
                while j < len(linhas) and not linhas[j].startswith("---"):
                    if linhas[j].startswith("Tarefa: "):
                        descricao_tarefa = linhas[j].strip().replace("Tarefa: ", "")
                        responsavel = linhas[j + 1].strip().replace("Responsável: ", "")
                        status = linhas[j + 2].strip().replace("Status: ", "")
                        tarefas.append({
                            "descricao": descricao_tarefa,
                            "responsavel": responsavel,
                            "status": status
                        })
                        j += 3
                    else:
                        j += 1

                # Verifica se a linha separadora está presente
                if j < len(linhas) and linhas[j].startswith("---"):
                    atas.append({
                        "titulo": titulo,
                        "descricao": descricao,
                        "criador": criador,
                        "usuarios_adicionados": usuarios_adicionados,
                        "tarefas": tarefas
                    })

                # Avança para a próxima ata
                i = j + 1
    return atas

# Função para salvar as atas no arquivo
def salvar_atas(atas):
    with open("atas.txt", "w") as arquivo:
        for ata in atas:
            arquivo.write(f"Título: {ata['titulo']}\n")
            arquivo.write(f"Descrição: {ata['descricao']}\n")
            arquivo.write(f"Criador: {ata['criador']}\n")
            arquivo.write(f"Usuários: {','.join(ata['usuarios_adicionados'])}\n")
            for tarefa in ata["tarefas"]:
                arquivo.write(f"Tarefa: {tarefa['descricao']}\n")
                arquivo.write(f"Responsável: {tarefa['responsavel']}\n")
                arquivo.write(f"Status: {tarefa['status']}\n")
            arquivo.write("-" * 30 + "\n")

# Adiciona a função enumerate ao contexto dos templates
@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)

# Rota para a página de login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha").encode('utf-8')

        if usuario in usuarios and usuarios[usuario] == hashlib.sha256(senha).hexdigest():
            session["usuario"] = usuario
            return redirect(url_for("hub_atas"))  # Redireciona para o Hub de Atas
        else:
            flash("Usuário ou senha incorretos!", "erro")
    return render_template("login.html")

# Rota para a página de cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha").encode('utf-8')
        confirmar_senha = request.form.get("confirmar_senha").encode('utf-8')

        if usuario in usuarios:
            flash("Usuário já existe!", "erro")
        elif senha != confirmar_senha:
            flash("As senhas não coincidem!", "erro")
        else:
            usuarios[usuario] = hashlib.sha256(senha).hexdigest()
            flash("Cadastro realizado com sucesso!", "sucesso")
            return redirect(url_for("login"))

    return render_template("cadastro.html")

# Rota para a página de gerenciamento de cadastros (apenas para admin)
@app.route("/gerenciar_usuarios")
def gerenciar_usuarios():
    if "usuario" not in session or session["usuario"] != "admin":
        flash("Acesso negado! Apenas o administrador pode gerenciar usuários.", "erro")
        return redirect(url_for("hub_atas"))

    return render_template("gerenciar_usuarios.html", usuarios=usuarios)

# Rota para excluir um usuário (apenas para admin)
@app.route("/excluir_usuario/<usuario>")
def excluir_usuario(usuario):
    if "usuario" not in session or session["usuario"] != "admin":
        flash("Acesso negado!", "erro")
        return redirect(url_for("login"))

    if usuario in usuarios:
        del usuarios[usuario]
        flash(f"Usuário {usuario} excluído com sucesso!", "sucesso")
    else:
        flash("Usuário não encontrado!", "erro")

    return redirect(url_for("gerenciar_usuarios"))

# Rota para a página principal de atas
@app.route("/atas", methods=["GET", "POST"])
def atas():
    if "usuario" not in session:
        flash("Acesso negado! Faça login para continuar.", "erro")
        return redirect(url_for("login"))

    if request.method == "POST":
        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao")

        if titulo and descricao:
            atas = carregar_atas()
            nova_ata = {
                "titulo": titulo,
                "descricao": descricao,
                "criador": session["usuario"],
                "usuarios_adicionados": [session["usuario"]],  # O criador é automaticamente adicionado
                "tarefas": []  # Inicialmente sem tarefas
            }
            atas.append(nova_ata)
            salvar_atas(atas)
            flash("Ata criada com sucesso!", "sucesso")
            return redirect(url_for("hub_atas"))
        else:
            flash("Preencha o título e a descrição!", "erro")

    return render_template("atas.html")

@app.route("/adicionar_usuario/<int:index>", methods=["POST"])
def adicionar_usuario(index):
    if "usuario" not in session:
        flash("Acesso negado! Faça login para continuar.", "erro")
        return redirect(url_for("login"))

    atas = carregar_atas()

    # Verifica se o índice é válido
    if index < 0 or index >= len(atas):
        flash("Ata inválida!", "erro")
        return redirect(url_for("atas"))

    # Verifica se o usuário logado é o criador da ata
    if session["usuario"] != atas[index]["criador"]:
        flash("Somente o criador da ata pode adicionar membros!", "erro")
        return redirect(url_for("atas"))

    usuario_adicionado = request.form.get("usuario_adicionado")

    if usuario_adicionado and usuario_adicionado in usuarios:
        if usuario_adicionado not in atas[index]["usuarios_adicionados"]:
            atas[index]["usuarios_adicionados"].append(usuario_adicionado)
            salvar_atas(atas)
            flash(f"Usuário {usuario_adicionado} adicionado à ata!", "sucesso")
        else:
            flash(f"Usuário {usuario_adicionado} já está na ata!", "erro")
    else:
        flash("Usuário inválido!", "erro")

    return redirect(url_for("atas"))

# Rota para adicionar usuários a uma ata
@app.route("/adicionar_tarefa/<int:index>", methods=["POST"])
def adicionar_tarefa(index):
    if "usuario" not in session:
        flash("Acesso negado! Faça login para continuar.", "erro")
        return redirect(url_for("login"))

    atas = carregar_atas()

    # Verifica se o índice é válido
    if index < 0 or index >= len(atas):
        flash("Ata inválida!", "erro")
        return redirect(url_for("atas"))

    # Verifica se o usuário logado é o criador da ata
    if session["usuario"] != atas[index]["criador"]:
        flash("Somente o criador da ata pode adicionar tarefas!", "erro")
        return redirect(url_for("atas"))

    descricao_tarefa = request.form.get("descricao_tarefa")
    responsavel_tarefa = request.form.get("responsavel_tarefa")

    if descricao_tarefa and responsavel_tarefa:
        nova_tarefa = {
            "descricao": descricao_tarefa,
            "responsavel": responsavel_tarefa,
            "status": "pendente"
        }
        atas[index]["tarefas"].append(nova_tarefa)
        salvar_atas(atas)
        flash("Tarefa adicionada com sucesso!", "sucesso")
    else:
        flash("Preencha a descrição e o responsável da tarefa!", "erro")

    return redirect(url_for("atas"))

# Rota para editar uma ata
@app.route("/editar/<int:index>", methods=["GET", "POST"])
def editar_ata(index):
    if "usuario" not in session:
        return redirect(url_for("login"))

    atas = carregar_atas()

    if index < 0 or index >= len(atas):
        flash("Ata inválida!", "erro")
        return redirect(url_for("atas"))

    if request.method == "POST":
        novo_titulo = request.form.get("titulo")
        nova_descricao = request.form.get("descricao")

        if novo_titulo and nova_descricao:
            atas[index]["titulo"] = novo_titulo
            atas[index]["descricao"] = nova_descricao
            salvar_atas(atas)
            flash("Ata editada com sucesso!", "sucesso")
            return redirect(url_for("atas"))
        else:
            flash("Preencha o título e a descrição!", "erro")

    return render_template("editar_ata.html", ata=atas[index], index=index)

# Rota para excluir uma ata
@app.route("/excluir/<int:index>")
def excluir_ata(index):
    if "usuario" not in session:
        return redirect(url_for("login"))

    atas = carregar_atas()

    if index < 0 or index >= len(atas):
        flash("Ata inválida!", "erro")
    else:
        atas.pop(index)
        salvar_atas(atas)
        flash("Ata excluída com sucesso!", "sucesso")

    return redirect(url_for("atas"))

# Rota para atualizar o status de uma tarefa
@app.route("/atualizar_status/<int:index_ata>/<int:index_tarefa>", methods=["POST"])
def atualizar_status(index_ata, index_tarefa):
    if "usuario" not in session:
        flash("Acesso negado! Faça login para continuar.", "erro")
        return redirect(url_for("login"))

    atas = carregar_atas()

    # Verifica se o índice da ata é válido
    if index_ata < 0 or index_ata >= len(atas):
        flash("Ata inválida!", "erro")
        return redirect(url_for("atas"))

    # Verifica se o índice da tarefa é válido
    if index_tarefa < 0 or index_tarefa >= len(atas[index_ata]["tarefas"]):
        flash("Tarefa inválida!", "erro")
        return redirect(url_for("atas"))

    # Verifica se o usuário logado é o responsável pela tarefa
    if session["usuario"] != atas[index_ata]["tarefas"][index_tarefa]["responsavel"]:
        flash("Somente o responsável pela tarefa pode atualizar o status!", "erro")
        return redirect(url_for("atas"))

    novo_status = request.form.get("status")

    if novo_status in ["pendente", "em análise", "finalizado"]:
        atas[index_ata]["tarefas"][index_tarefa]["status"] = novo_status
        salvar_atas(atas)
        flash("Status da tarefa atualizado com sucesso!", "sucesso")
    else:
        flash("Status inválido!", "erro")

    return redirect(url_for("atas"))

@app.route("/hub_atas")
def hub_atas():
    if "usuario" not in session:
        flash("Acesso negado! Faça login para continuar.", "erro")
        return redirect(url_for("login"))

    atas = carregar_atas()

    # Filtrar atas: somente as que o usuário criou ou foi adicionado
    atas_filtradas = [
        ata for ata in atas
        if ata["criador"] == session["usuario"] or session["usuario"] in ata["usuarios_adicionados"]
    ]

    return render_template("hub_atas.html", atas=atas_filtradas)

@app.route("/detalhes_ata/<int:index>", methods=["GET", "POST"])
def detalhes_ata(index):
    if "usuario" not in session:
        flash("Acesso negado! Faça login para continuar.", "erro")
        return redirect(url_for("login"))

    atas = carregar_atas()

    # Verifica se o índice é válido
    if index < 0 or index >= len(atas):
        flash("Ata inválida!", "erro")
        return redirect(url_for("hub_atas"))

    ata = atas[index]

    # Verifica se o usuário logado tem acesso à ata
    if session["usuario"] != ata["criador"] and session["usuario"] not in ata["usuarios_adicionados"]:
        flash("Acesso negado! Você não tem permissão para visualizar esta ata.", "erro")
        return redirect(url_for("hub_atas"))

    # Lógica para adicionar usuários à ata
    if request.method == "POST" and "usuario_adicionado" in request.form:
        usuario_adicionado = request.form.get("usuario_adicionado")
        if usuario_adicionado and usuario_adicionado in usuarios:
            if usuario_adicionado not in ata["usuarios_adicionados"]:
                ata["usuarios_adicionados"].append(usuario_adicionado)
                salvar_atas(atas)
                flash(f"Usuário {usuario_adicionado} adicionado à ata!", "sucesso")
            else:
                flash(f"Usuário {usuario_adicionado} já está na ata!", "erro")
        else:
            flash("Usuário inválido!", "erro")

    # Lógica para adicionar tarefas à ata
    if request.method == "POST" and "descricao_tarefa" in request.form:
        descricao_tarefa = request.form.get("descricao_tarefa")
        responsavel_tarefa = request.form.get("responsavel_tarefa")
        if descricao_tarefa and responsavel_tarefa:
            nova_tarefa = {
                "descricao": descricao_tarefa,
                "responsavel": responsavel_tarefa,
                "status": "pendente"
            }
            ata["tarefas"].append(nova_tarefa)
            salvar_atas(atas)
            flash("Tarefa adicionada com sucesso!", "sucesso")
        else:
            flash("Preencha a descrição e o responsável da tarefa!", "erro")

    return render_template("detalhes_ata.html", ata=ata, index=index, usuarios=usuarios.keys())

@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "usuario" not in session:
        flash("Acesso negado! Faça login para continuar.", "erro")
        return redirect(url_for("login"))

    usuario = session["usuario"]

    if request.method == "POST":
        nova_senha = request.form.get("nova_senha")
        confirmar_senha = request.form.get("confirmar_senha")

        if nova_senha and confirmar_senha:
            if nova_senha == confirmar_senha:
                usuarios[usuario] = hashlib.sha256(nova_senha.encode('utf-8')).hexdigest()
                flash("Senha atualizada com sucesso!", "sucesso")
            else:
                flash("As senhas não coincidem!", "erro")
        else:
            flash("Preencha todos os campos!", "erro")

    return render_template("perfil.html", usuario=usuario)

# Rota para logout
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)