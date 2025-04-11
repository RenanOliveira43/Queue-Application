# Usa uma imagem base com Python
FROM python:3.13-slim-bookworm

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia tudo do diretório atual (onde você está rodando o docker build) para o /app do container
COPY . .

# Instala as dependências
RUN pip install twisted

# Expõe a porta do servidor
EXPOSE 5678

# Comando para rodar o servidor
CMD ["python", "queueManager.py"]
