#/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import os
import shutil
import glob
import re
import paramiko
import StringIO
import logging
import time
import datetime
from datetime import date,timedelta
from MongoOps import MongoOps

log = logging.getLogger(__name__)

class UtilOps:

	def __init__(self):
		pass

	def ssh_pub_key(self,key_file):
		# coded by Saito
		key = paramiko.RSAKey(filename=key_file)
		pub = "{0} {1} autogenerated"
		pub = pub.format(key.get_name(), key.get_base64())
		return pub

	def CriarParDeChaves(self,Aluno):
		"""
			Método que cria um par de chaves contendo chave pública e chave privada, a chave é gerada utilizando o comando ssh-keygen, caso a chave já exista ela não é sobrescrita.
			
			:param Aluno: Aluno é uma string contendo o email do aluno
		
			:returns: Esse método retorna um dicionário com duas Keys. ChavePublica e ChavePrivada.
		"""
		try:
			log.info("[+] Gerando par de chaves")
			key_file = "/opt/4linux/chaves/%s"%Aluno
			key = paramiko.RSAKey.generate(bits=2048)
			key.write_private_key_file(key_file)

			out = StringIO.StringIO()
			key.write_private_key(out)

			pub = self.ssh_pub_key(key_file)
			fpub = open(key_file+".pub","w")
			fpub.write(pub)
			fpub.close()	

			with open("/opt/4linux/chaves/%s.pub"%Aluno) as f:
				ChavePublica = f.read()
			f.close()
			with open("/opt/4linux/chaves/%s"%Aluno) as f:
				ChavePrivada = f.read()
			f.close()
			log.info("[+] Par de chaves gerado com sucesso")
			return {"ChavePublica":ChavePublica, "ChavePrivada":ChavePrivada}
		except Exception as e:
			log.error("[-] Erro ao gerar par de chaves do ssh %s",e)
			return False

	def RemoverParDeChaves(self,Aluno):
		try:
			log.info("[+] Removendo chaves")
			for c in glob.glob("/opt/4linux/chaves/%s*"%aluno):
				log.info("[+] Removendo %s"%c)
				os.remove(c)
		except Exception as e:
			log.error("[-] Falha ao remover as chaves %s",e)

	def PaginaDefault(self,aluno):
		"""
			Método que cria uma index no ambiente live do aluno

			:param aluno: aluno precisa ser uma string que contem o username do aluno no gitlab, que atualmente é o id do cr4	

			:returns: Esse método não possui valor de retorno
		"""
		log.info("[+] Criando Pagina Default")

		if os.path.exists("/var/www/html/%s"%aluno):
			for d in glob.glob("/var/www/html/%s*"%aluno):
				shutil.rmtree(d)

		if not os.path.exists("/var/www/html/%s"%aluno):
			os.mkdir("/var/www/html/%s/"%aluno)

		os.symlink("/var/www/html/padrao/site","/var/www/html/%s/site"%aluno)
		for d in glob.glob("/var/www/html/%s*"%aluno):
			os.system("chmod 775 %s"%d)

	def RemoverPaginaDefault(self,aluno):
		try:
			if os.path.exists("/var/www/html/%s"%aluno):
				for d in glob.glob("/var/www/html/%s*"%aluno):
					log.info("[+] Removendo diretorio %s"%d)
					shutil.rmtree(d)
				log.info("[+] Pagina removida")
			else:
				log.warning("[!] Pagina nao existe")
		except Exception as e:
			log.error("[-] Falha ao remover pagina default %s",e)

	def GerarListaPdf(self,lista):
		try:
			mo = MongoOps()
			curso = mo.BuscarTurma({"_id":int(lista['idturma'])})
			if curso.count():
				for c in curso:
					nome_curso = c['curso']['nome']
					data_inicio = c['DataInicio']
					data_fim = c['DataFim']
			else:
				return {"status":"1","messsage":"Turma nao encontrada"}

			res = mo.ListarPresenca(lista['idturma'])
			if res.count():
				json_alunos = {}
				lista_alunos = []
				json_alunos['Turma'] = lista['idturma']
				json_alunos['Curso'] = nome_curso
				json_alunos['Data'] = "%s a %s"%(data_inicio,data_fim)
				json_alunos['alunos'] = []
				for r in res:
					lista_alunos.append(r['nome'])
					for l in r['lista']:
						if l['status'] == 1:
							l['status'] = 'OK'
						#lista_alunos.append(l['hora'])
						lista_alunos.append(str(l['data'])+" "+str(l['status']))
					json_alunos['alunos'].append(lista_alunos)
					lista_alunos = []
			else:
				return {"status":"1","message":"Nao foi encontrada nenhuma lista de presenca"}
		except Exception as e:
			logging.error("[-] Ocorreu um erro ao gerar a lista de presenca %s",e)
			return {"status":"1","message":"Ocorreu um erro ao gerar a lista de presenca %s"%e}
					
		
		dataini = datetime.datetime.strptime(data_inicio,"%d/%m/%Y")
		datafim = datetime.datetime.strptime(data_fim,"%d/%m/%Y")
		data = dataini
		lista_datas = []
		while data < datafim:
			data += timedelta(days=1)
			lista_datas.append(str(data.date().strftime("%d/%m")))

		print json_alunos['alunos']

		return {"status":"0",
				"DataInicio":dataini.date().strftime("%d/%m/%Y"),
				"DataFim":datafim.date().strftime("%d/%m/%Y"),
				"Datas":lista_datas,
				"Alunos":json_alunos['alunos'],
				"Curso":json_alunos['Curso'],
				"Turma":json_alunos['Turma']}
