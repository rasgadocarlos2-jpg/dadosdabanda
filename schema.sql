CREATE TABLE chaves_api (
	id SERIAL NOT NULL, 
	chave_hash VARCHAR(64) NOT NULL, 
	email VARCHAR(200) NOT NULL, 
	criada_em TIMESTAMP WITH TIME ZONE NOT NULL, 
	ativa BOOLEAN NOT NULL, 
	limite_por_minuto INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (chave_hash)
);

CREATE TABLE execucoes_recolha (
	id SERIAL NOT NULL, 
	conector VARCHAR(60) NOT NULL, 
	iniciada_em TIMESTAMP WITH TIME ZONE NOT NULL, 
	terminada_em TIMESTAMP WITH TIME ZONE, 
	estado VARCHAR(20) NOT NULL, 
	mensagem TEXT, 
	novas INTEGER NOT NULL, 
	revistas INTEGER NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE fontes (
	id VARCHAR(40) NOT NULL, 
	nome VARCHAR(120) NOT NULL, 
	url VARCHAR(300) NOT NULL, 
	estado_autorizacao VARCHAR(20) NOT NULL, 
	licenca TEXT, 
	notas TEXT, 
	PRIMARY KEY (id)
);

CREATE TABLE series (
	id VARCHAR(60) NOT NULL, 
	fonte_id VARCHAR(40) NOT NULL, 
	codigo VARCHAR(60) NOT NULL, 
	nome VARCHAR(200) NOT NULL, 
	unidade VARCHAR(40) NOT NULL, 
	periodicidade VARCHAR(20) NOT NULL, 
	url_consulta VARCHAR(500), 
	PRIMARY KEY (id), 
	FOREIGN KEY(fonte_id) REFERENCES fontes (id)
);

CREATE TABLE observacoes (
	id SERIAL NOT NULL, 
	serie_id VARCHAR(60) NOT NULL, 
	periodo VARCHAR(10) NOT NULL, 
	valor FLOAT NOT NULL, 
	recolhido_em TIMESTAMP WITH TIME ZONE NOT NULL, 
	hash_bruto VARCHAR(64), 
	PRIMARY KEY (id), 
	UNIQUE (serie_id, periodo, recolhido_em), 
	FOREIGN KEY(serie_id) REFERENCES series (id)
);

CREATE INDEX ix_observacoes_serie_id ON observacoes (serie_id);

