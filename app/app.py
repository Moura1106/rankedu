"""
app.py — As TELAS do sistema (Flask). Cada rota corresponde a um caso
de uso do DIAGRAMA DE CASOS DE USO (Fase 2, seção 2a):

  UC01/UC02  /ranking                     consultar e filtrar o ranking
  UC03/UC04  /oferta/<id>, /curso/<id>    detalhes da oferta e pitch do curso
  UC05       /cadastro                    cadastrar-se como empresário
  UC06       /login, /logout              fazer login
  UC07       /oferta/<id>/avaliar         avaliar oferta (diagrama de sequência)
  UC08–UC10  /admin/instituicoes|cursos|ofertas   manter cadastros
  UC11       /admin                       moderar avaliações

Para rodar:  python app.py   e abrir http://localhost:5000
"""
from __future__ import annotations

import os
import secrets
import sqlite3
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for

import db
from controllers import AvaliacaoController, RegraNegocioErro
from models import (Administrador, Curso, Empresario, Instituicao, Modalidade, TipoInstituicao,
                    gerar_hash_senha)
from ranking import Ranking
from repositorios import (CursoRepositorio, InstituicaoRepositorio, OfertaRepositorio,
                          UsuarioRepositorio)


def chave_secreta() -> str:
    """Chave que assina o cookie de login. É gerada uma vez, aleatória, e guardada
    em app/.chave_secreta (fora do Git), para cada instalação ter a sua."""
    arquivo = db.PASTA_APP / ".chave_secreta"
    if not arquivo.exists():
        arquivo.write_text(secrets.token_hex(32), encoding="utf-8")
    return arquivo.read_text(encoding="utf-8").strip()


def create_app(caminho_banco: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("RANKEDU_SECRET") or chave_secreta()
    app.config["BANCO"] = caminho_banco or str(db.BANCO_PADRAO)
    db.garantir_banco(app.config["BANCO"])

    # ------------------------------------------------ infraestrutura
    def conexao() -> sqlite3.Connection:
        if "conexao" not in g:
            g.conexao = db.conectar(app.config["BANCO"])
        return g.conexao

    @app.teardown_appcontext
    def fechar_conexao(_erro):
        c = g.pop("conexao", None)
        if c is not None:
            c.close()

    def usuario_logado():
        if "usuario_id" not in session:
            return None
        return UsuarioRepositorio(conexao()).buscar(session["usuario_id"])

    @app.context_processor
    def disponibilizar_usuario():
        return {"usuario": usuario_logado()}

    def exige_perfil(classe):
        """Bloqueia a rota para quem não está logado com o perfil certo."""
        def decorador(funcao):
            @wraps(funcao)
            def envoltorio(*args, **kwargs):
                usuario = usuario_logado()
                if usuario is None:
                    flash("Faça login para continuar.", "aviso")
                    return redirect(url_for("login", proximo=request.path))
                if not isinstance(usuario, classe):
                    abort(403)
                return funcao(*args, **kwargs)
            return envoltorio
        return decorador

    def inteiro_ou_none(valor: str | None) -> int | None:
        return int(valor) if valor not in (None, "") else None

    # ------------------------------------------------ UC01 / UC02
    @app.route("/")
    def inicio():
        return redirect(url_for("ranking"))

    @app.route("/ranking")
    def ranking():
        cursos = CursoRepositorio(conexao()).listar()
        curso_id = request.args.get("curso", type=int) or (cursos[0].id if cursos else None)
        filtros = {
            "tipo": request.args.get("tipo") or None,
            "uf": request.args.get("uf") or None,
            "modalidade": request.args.get("modalidade") or None,
        }
        ofertas = OfertaRepositorio(conexao()).listar(curso_id) if curso_id else []
        lista = Ranking.gerar(ofertas, **filtros)
        return render_template("ranking.html", cursos=cursos, curso_id=curso_id, filtros=filtros,
                               ofertas=lista, ufs=InstituicaoRepositorio(conexao()).ufs(),
                               modalidades=list(Modalidade), tipos=list(TipoInstituicao))

    # ------------------------------------------------ UC03 / UC04
    @app.route("/oferta/<int:oferta_id>")
    def oferta(oferta_id: int):
        o = OfertaRepositorio(conexao()).buscar(oferta_id)
        if o is None:
            abort(404)
        return render_template("oferta.html", oferta=o, ranking=Ranking)

    @app.route("/curso/<int:curso_id>")
    def curso(curso_id: int):
        c = CursoRepositorio(conexao()).buscar(curso_id)
        if c is None:
            abort(404)
        return render_template("curso.html", curso=c)

    # ------------------------------------------------ UC05 / UC06
    @app.route("/cadastro", methods=["GET", "POST"])
    def cadastro():
        if request.method == "POST":
            f = request.form
            campos = [f.get(k, "").strip() for k in ("nome", "email", "senha", "empresa", "cargo")]
            nome, email, senha, empresa, cargo = campos
            if not all(campos):
                flash("Preencha todos os campos (empresa e cargo são obrigatórios — RN05).", "erro")
            elif len(senha) < 6:
                flash("A senha deve ter pelo menos 6 caracteres.", "erro")
            else:
                novo = Empresario(None, nome, email, gerar_hash_senha(senha), empresa, cargo)
                try:
                    UsuarioRepositorio(conexao()).cadastrar_empresario(novo)
                except sqlite3.IntegrityError:
                    flash("Já existe uma conta com esse e-mail.", "erro")
                else:
                    session["usuario_id"] = novo.id
                    flash(f"Bem-vindo(a), {novo.nome}! Você já pode avaliar ofertas.", "ok")
                    return redirect(url_for("ranking"))
        return render_template("cadastro.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            u = UsuarioRepositorio(conexao()).buscar_por_email(request.form.get("email", ""))
            if u and u.autenticar(request.form.get("senha", "")):
                session["usuario_id"] = u.id
                flash(f"Olá, {u.nome}!", "ok")
                destino = request.args.get("proximo", "")
                if not destino.startswith("/"):   # evita redirecionar para outro site
                    destino = url_for("painel_admin") if isinstance(u, Administrador) else url_for("ranking")
                return redirect(destino)
            flash("E-mail ou senha inválidos.", "erro")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("ranking"))

    # ------------------------------------------------ UC07
    @app.route("/oferta/<int:oferta_id>/avaliar", methods=["GET", "POST"])
    @exige_perfil(Empresario)
    def avaliar(oferta_id: int):
        controller = AvaliacaoController(conexao())
        o = OfertaRepositorio(conexao()).buscar(oferta_id)
        if o is None:
            abort(404)
        usuario = usuario_logado()
        if request.method == "POST":
            notas = (request.form.get("nota_empregabilidade"), request.form.get("nota_preparo"),
                     request.form.get("nota_soft_skills"))
            try:
                mensagem = controller.avaliar(usuario, oferta_id, notas, request.form.get("comentario"))
            except RegraNegocioErro as erro:
                flash(str(erro), "erro")
            else:
                flash(mensagem, "ok")
                return redirect(url_for("oferta", oferta_id=oferta_id))
        anterior = controller.avaliacoes.buscar_do_usuario(usuario.id, oferta_id)
        return render_template("avaliar.html", oferta=o, anterior=anterior)

    # ------------------------------------------------ UC11
    @app.route("/admin")
    @exige_perfil(Administrador)
    def painel_admin():
        controller = AvaliacaoController(conexao())
        ofertas = {o.id: o for o in OfertaRepositorio(conexao()).listar()}
        return render_template("admin/moderacao.html", pendentes=controller.pendentes(), ofertas=ofertas)

    @app.post("/admin/avaliacoes/<int:avaliacao_id>/<acao>")
    @exige_perfil(Administrador)
    def moderar(avaliacao_id: int, acao: str):
        if acao not in ("aprovar", "rejeitar"):
            abort(404)
        AvaliacaoController(conexao()).moderar(usuario_logado(), avaliacao_id, acao == "aprovar")
        flash("Avaliação aprovada." if acao == "aprovar" else "Avaliação rejeitada.", "ok")
        return redirect(url_for("painel_admin"))

    # ------------------------------------------------ UC08 – instituições
    @app.route("/admin/instituicoes", methods=["GET", "POST"])
    @exige_perfil(Administrador)
    def admin_instituicoes():
        repo = InstituicaoRepositorio(conexao())
        if request.method == "POST":
            f = request.form
            try:
                repo.salvar(Instituicao(inteiro_ou_none(f.get("id")), f["nome"].strip(),
                                        f.get("sigla", "").strip() or None, TipoInstituicao(f["tipo"]),
                                        f["cidade"].strip(), f["uf"].strip().upper(),
                                        f.get("site", "").strip() or None))
            except (sqlite3.IntegrityError, ValueError, KeyError):
                flash("Dados inválidos: confira os campos obrigatórios.", "erro")
            else:
                flash("Instituição salva.", "ok")
            return redirect(url_for("admin_instituicoes"))
        editar = repo.buscar(request.args.get("editar", type=int) or 0)
        return render_template("admin/instituicoes.html", itens=repo.listar(), editar=editar,
                               tipos=list(TipoInstituicao))

    @app.post("/admin/instituicoes/<int:id_>/remover")
    @exige_perfil(Administrador)
    def remover_instituicao(id_: int):
        try:
            InstituicaoRepositorio(conexao()).remover(id_)
            flash("Instituição removida.", "ok")
        except sqlite3.IntegrityError:
            flash("Não é possível remover: a instituição tem ofertas cadastradas (ON DELETE RESTRICT).", "erro")
        return redirect(url_for("admin_instituicoes"))

    # ------------------------------------------------ UC09 – cursos
    @app.route("/admin/cursos", methods=["GET", "POST"])
    @exige_perfil(Administrador)
    def admin_cursos():
        repo = CursoRepositorio(conexao())
        if request.method == "POST":
            f = request.form
            try:
                repo.salvar(Curso(inteiro_ou_none(f.get("id")), f["nome"].strip(), f["area"].strip(),
                                  f["pitch_texto"].strip(), f.get("pitch_video_url", "").strip() or None))
            except (sqlite3.IntegrityError, KeyError):
                flash("Dados inválidos ou curso já existente.", "erro")
            else:
                flash("Curso salvo.", "ok")
            return redirect(url_for("admin_cursos"))
        editar = repo.buscar(request.args.get("editar", type=int) or 0)
        return render_template("admin/cursos.html", itens=repo.listar(), editar=editar)

    @app.post("/admin/cursos/<int:id_>/remover")
    @exige_perfil(Administrador)
    def remover_curso(id_: int):
        try:
            CursoRepositorio(conexao()).remover(id_)
            flash("Curso removido.", "ok")
        except sqlite3.IntegrityError:
            flash("Não é possível remover: o curso tem ofertas cadastradas (ON DELETE RESTRICT).", "erro")
        return redirect(url_for("admin_cursos"))

    # ------------------------------------------------ UC10 – ofertas
    @app.route("/admin/ofertas", methods=["GET", "POST"])
    @exige_perfil(Administrador)
    def admin_ofertas():
        repo = OfertaRepositorio(conexao())
        if request.method == "POST":
            f = request.form
            try:
                repo.salvar(int(f["instituicao_id"]), int(f["curso_id"]), Modalidade(f["modalidade"]).value,
                            inteiro_ou_none(f.get("conceito_enade")), inteiro_ou_none(f.get("cpc")),
                            float(f.get("mensalidade") or 0), inteiro_ou_none(f.get("id")))
            except (sqlite3.IntegrityError, ValueError, KeyError):
                flash("Dados inválidos: notas de 1 a 5, mensalidade ≥ 0 e sem oferta repetida.", "erro")
            else:
                flash("Oferta salva.", "ok")
            return redirect(url_for("admin_ofertas"))
        editar = repo.buscar(request.args.get("editar", type=int) or 0)
        return render_template("admin/ofertas.html", itens=repo.listar(), editar=editar,
                               instituicoes=InstituicaoRepositorio(conexao()).listar(),
                               cursos=CursoRepositorio(conexao()).listar(), modalidades=list(Modalidade))

    @app.post("/admin/ofertas/<int:id_>/remover")
    @exige_perfil(Administrador)
    def remover_oferta(id_: int):
        OfertaRepositorio(conexao()).remover(id_)
        flash("Oferta removida (e suas avaliações, por CASCADE).", "ok")
        return redirect(url_for("admin_ofertas"))

    # ------------------------------------------------ filtro de template
    @app.template_filter("nota")
    def formatar_nota(valor):
        return "—" if valor is None else f"{valor:.2f}".replace(".", ",")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
