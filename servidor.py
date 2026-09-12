#!/usr/bin/env python3
import asyncio
from tcp import Servidor
import re

ARGS_ESPERADOS = {
    "NICK": 1,
    "PING": 1,
    "PRIVMSG": 2,
    "JOIN": 1,
    "PART": 1,
}

NICKS =[]

def liberar_nick(conexao):
    if conexao.nick in NICKS:
        NICKS.remove(conexao.nick)


def sanitize_string_data(dados):
    return dados.decode("utf-8").strip()

# Valida nome de usuários e canais
def validar_nome(nome):
    return re.match(br'^[a-zA-Z][a-zA-Z0-9_-]*$', nome) is not None

#funcao handler para quando o usuario nao usar um dos comandos definidos
def stupid_user():
    print("Available commands: NICK, PING, PRIVMSG, JOIN, PART")

#funcao handler para NICK
def nick(conexao, novo_nick):
    print("NICKS:", NICKS)

    #verificacao do nick
    if not validar_nome(novo_nick.encode("utf-8")):
        print(":server 432 ", conexao.nick, novo_nick, " :Erroneous nickname")
        return

    #verificacao se ja existe
    if novo_nick in NICKS:
        print(":server 433 ", conexao.nick, novo_nick, ":Nickname is already in use")
        return

    #logs do server
    print(":server 001 ", novo_nick, " :Welcome")
    print(":server 422 ", novo_nick, " :MOTD File is missing")

    liberar_nick(conexao)          # libera o nick antigo
    NICKS.append(novo_nick)        # reserva o nick novo
    conexao.nick = novo_nick       # atualiza o estado da conexão

#funcao handler para PING
def ping(payload):
    print(payload)

#funcao handler para PRIVMSG
def privmsg(receiver,msg):
    print(receiver,msg)

#funcao handler para JOIN
def join(channel):
    print(channel)

#funcao handler para PART
def part(channel):
    print(channel)

# Separa os tipos de mensagem e direciona para cada handler
# command: tipo de comando nick,ping ...
# rest: string[]
def message_protocol(conexao,command, rest):

    esperado = ARGS_ESPERADOS.get(command)

    if esperado is None or len(rest) < esperado:
        return stupid_user()


    cases = {
        "NICK": lambda: nick(conexao,rest[0]),
        "PING": lambda: ping(rest[0]),
        "PRIVMSG": lambda: privmsg(rest[0],rest[1]),
        "JOIN": lambda: join(rest[0]),
        "PART": lambda: part(rest[0]),
    }

    # cases.get(command, stupid_user) retorna a função associada,
    # ou a função stupid_user se a chave não existir
    return cases.get(command, stupid_user)()


def sair(conexao):
    print(conexao, 'conexão fechada')
    
    if conexao.nick != b'*':
        liberar_nick(conexao)

    conexao.fechar()


def dados_recebidos(conexao, dados):
    if dados == b'':
        return sair(conexao)

    #strip para tirar o \r\n no final do ultimo argumento
    string_data = sanitize_string_data(dados)
    
    #divide a string em no máximo 3 partes, permitindo até 3 argumentos em 1 comando
    words = string_data.split(maxsplit=2)

    if not words:
        return stupid_user()

    command = words[0]
    rest = words[1:]

    message_protocol(conexao,command,rest)


def conexao_aceita(conexao):
    print(conexao, 'nova conexão')

    conexao.nick = b'*'

    conexao.registrar_recebedor(dados_recebidos)


servidor = Servidor(6667)
servidor.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()
