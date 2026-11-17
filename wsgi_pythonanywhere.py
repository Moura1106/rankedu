# Arquivo WSGI para o PythonAnywhere.
# Copie este conteúdo para o arquivo WSGI da aba "Web" e troque SEU_USUARIO
# pelo seu nome de usuário no PythonAnywhere.
import sys

PASTA_APP = "/home/SEU_USUARIO/rankedu/app"
if PASTA_APP not in sys.path:
    sys.path.insert(0, PASTA_APP)

from app import create_app  # noqa: E402

application = create_app()
