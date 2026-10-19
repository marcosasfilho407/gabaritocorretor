import io
import json
import os
import base64
import cv2
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CONSTANTES E ARQUIVOS DE PERSISTÊNCIA EM DISCO
# ---------------------------------------------------------
ARQUIVO_GABARITOS_JSON = "gabaritos_oficiais.json"
ARQUIVO_HISTORICO_JSON = "historico_correcoes.json"
ARQUIVO_ALUNOS_TXT = "todososalunosporturma.txt"

# ---------------------------------------------------------
# FUNÇÃO DE OBTENÇÃO DA IMAGEM DE FUNDO (BASE64)
# ---------------------------------------------------------
def obter_imagem_fundo_base64():
    """Procura a imagem do projeto no diretório e converte para Base64."""
    candidatos = [
        "Gemini_Generated_Image_vktbzrvktbzrvktb.jfif",
        "background.jfif",
        "background.jpg",
        "background.png",
        "jt_background.jfif",
        "input_file_8.png"
    ]
    for c in candidatos:
        if os.path.exists(c):
            try:
                with open(c, "rb") as f:
                    data = f.read()
                    b64 = base64.b64encode(data).decode("utf-8")
                    ext = "jpeg" if c.endswith((".jpg", ".jpeg", ".jfif")) else "png"
                    return f"data:image/{ext};base64,{b64}"
            except Exception:
                pass
    return None

# ---------------------------------------------------------
# ESTILIZAÇÃO CSS COM CORES DO SÍMBOLO JT E IMAGEM DE FUNDO
# ---------------------------------------------------------
def aplicar_estilo_jt():
    bg_base64 = obter_imagem_fundo_base64()
    
    if bg_base64:
        bg_css = f"""
            background: linear-gradient(rgba(5, 9, 20, 0.88), rgba(8, 15, 32, 0.94)), url('{bg_base64}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        bg_css = """
            background: linear-gradient(135deg, #050811 0%, #0a1122 50%, #0d1830 100%);
        """

    st.markdown(f"""
        <style>
        /* Fundo Geral */
        .stApp {{
            {bg_css}
            color: #E2E8F0;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}

        /* Ocultar barra superior padrão do Streamlit */
        header[data-testid="stHeader"] {{
            background: rgba(0, 0, 0, 0);
        }}

        /* Cabeçalho JT Personalizado */
        .jt-header-container {{
            background: linear-gradient(135deg, rgba(16, 26, 50, 0.85) 0%, rgba(8, 14, 28, 0.95) 100%);
            border: 2px solid #FFB800;
            box-shadow: 0 0 25px rgba(30, 80, 255, 0.4), inset 0 0 15px rgba(255, 42, 75, 0.2);
            border-radius: 18px;
            padding: 20px 28px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 22px;
            backdrop-filter: blur(12px);
        }}

        .jt-logo-emblem {{
            background: linear-gradient(145deg, #1E50FF, #0B2580);
            border: 3px solid #FFB800;
            box-shadow: 0 0 15px #1E50FF, 0 0 30px rgba(255, 42, 75, 0.6);
            border-radius: 14px;
            width: 72px;
            height: 72px;
            min-width: 72px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 38px;
            font-weight: 900;
            color: #FFB800;
            text-shadow: 2px 2px 4px #000000;
            letter-spacing: -1px;
        }}

        .jt-header-title {{
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(90deg, #FFFFFF 0%, #60A5FA 50%, #FFB800 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.2;
        }}

        .jt-header-subtitle {{
            font-size: 13px;
            color: #FF2A4B;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 4px;
            text-shadow: 0 0 8px rgba(255, 42, 75, 0.5);
        }}

        /* Estilização das Abas (Tabs) */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
            background-color: rgba(10, 16, 32, 0.7);
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 184, 0, 0.3);
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 48px;
            border-radius: 8px;
            color: #94A3B8;
            font-weight: 600;
            background-color: transparent;
            border: none;
        }}

        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #1E50FF 0%, #0B2580 100%) !important;
            color: #FFB800 !important;
            border: 1px solid #FFB800 !important;
            box-shadow: 0 0 12px rgba(30, 80, 255, 0.6);
        }}

        /* Botões Customizados */
        .stButton > button {{
            background: linear-gradient(90deg, #1E50FF 0%, #2B60FF 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid #FFB800 !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(30, 80, 255, 0.4) !important;
            transition: all 0.3s ease !important;
        }}

        .stButton > button:hover {{
            box-shadow: 0 0 20px rgba(255, 184, 0, 0.7), 0 0 12px rgba(30, 80, 255, 0.9) !important;
            transform: translateY(-2px) !important;
            border-color: #FFFFFF !important;
        }}

        /* Cards e Expander */
        [data-testid="stExpander"] {{
            background: rgba(15, 23, 42, 0.75) !important;
            border: 1px solid rgba(30, 80, 255, 0.4) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px);
        }}

        /* Métricas */
        [data-testid="stMetricValue"] {{
            color: #FFB800 !important;
            font-weight: 800 !important;
            text-shadow: 0 0 10px rgba(255, 184, 0, 0.4);
        }}

        [data-testid="stMetricLabel"] {{
            color: #94A3B8 !important;
            font-weight: 600 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# DADOS DOS ESTUDANTES EMBUTIDOS (FALLBACK)
# ---------------------------------------------------------
DADOS_ALUNOS_EMBUTIDOS = """Turma,Número,Matrícula,Nome
1º A,1,3256964,ADRIAN VINICIUS GONÇALVES OLIVEIRA
1º A,2,3976582,ANA ALICE TRINDADE SALES DE LIMA
1º A,3,3989573,ARTHUR GUSMAO SILVA CAMPELO
1º A,4,3987728,CAMILA SOARES RODRIGUES DA SILVA
1º A,5,3866482,DANIEL HOPPER SILVA
1º A,6,4027565,GABRIEL VASCONCELOS NERI DE OLIVEIRA
1º A,7,3691845,GEOVANA SANTOS DE ARRUDA
1º A,8,3365165,ISABELLE BEATRIZ FERREIRA DE MOURA
1º A,9,3826902,JADE GONÇALVES GOMES DE ARAÚJO
1º A,10,3412410,JEOVÁ MARQUES DA SILVA
1º A,11,3333047,JOÃO GABRIEL MAGALHÃES BARBOSA SOUSA
1º A,12,3975623,JOÃO GUILHERME DE ARAUJO BRITO
1º A,13,3227248,JOÃO MIGUEL RODRIGUES DE LIMA
1º A,14,3728069,JOÃO VICTOR SILVA DE SANTANA
1º A,15,4025548,JOAO VICTOR ZEFERINO MELCHIADES
1º A,16,3291140,KAUAN RICARDO QUEIROZ BARROS DAS SILVA
1º A,17,3162247,KELLY CAROLINE DA SILVA
1º A,18,3912701,KEMILY RAISSA ALVES DE MEDEIROS
1º A,19,3238444,LAYZA ROBERTA SOUZA DA SILVA
1º A,20,4047958,LEANDERSON ALBUQUERQUE DE FRANCA
1º A,21,3801114,LORENA CASTANHEIRA PESSOA
1º A,22,3159545,LUANA VITORIA SANTOS DOS REIS
1º A,23,4024507,MANOEL MITCHELL RIBEIRO DE FRANÇA
1º A,24,3957876,MARIA LUIZA LIMA MEDEIROS DE OLIVEIRA
1º A,25,3482155,MAYARA VICTORIA DOS SANTOS
1º A,26,4004761,MIGUEL NASCIMENTO SILVA
1º A,27,3161190,NYCOLLE EMANUELLE SILVA MARQUES
1º A,28,4001287,PEDRO HENRIQUE SANTOS DE SOUZA
1º A,29,3161678,POLLYANA MAIARA SOARES DA SILVA
1º A,30,3138181,RAFAEL FERRAZ DE LIMA FERREIRA
1º A,31,3267784,THIALY JAMILLE NASCIMENTO DOS SANTOS
1º A,32,3137791,WEDJA DE CARVALHO SILVA
1º A,33,3272284,WESLEY GABRIEL CONCEICAO SILVESTRE DE LUNA
1º A,34,2956174,YASMIM RAKELLY ALMEIDA DA SILVA
1º A,35,3958277,HEITOR GUILHERME ANSELMO DO NASCIMENTO
1º A,36,3612880,ALVARO JOSE DE SOUSA IEDON
1º A,37,4072034,ALINE DE SOUZA BORBA
1º A,38,3983736,GRAZIELE VICTORIA CARNEIRO SANTIAGO
1º B,1,,ANA BEATRIZ MOREIRA GOMES
1º B,2,,ANA KAROLINE ALVES DA SILVA
1º B,3,,ANA LUISA DE ALMEIDA ALBUQUERQUE
1º B,4,,ANA MARIA COUTINHO
1º B,5,,ANNA CLARA GONÇALO CAMELO SILVA
1º B,6,,ARTHUR DA SILVA LEAL
1º B,7,,BARBARA MARIA BATISTA PEDROZA
1º B,8,,BIANCA AVELINA DE SA AMORIM
1º B,9,,BIANCA REGINA RÉGIS DA SILVA
1º B,10,,BRUNA ALMEIDA PEREIRA DOS SANTOS
1º B,11,,DEYVISON ROSEMBERGUE SILVA DE BARROS
1º B,12,,EDGAR AUGUSTO ALBUQUERQUE CAVALCANTI
1º B,13,,FILIPE MONTEIRO GUIMARÃES DE ANDRADE
1º B,14,,GABRIEL FRANCISCO MARQUES LOPES
1º B,15,,GABRIELLY VITORIA PAZ DA SILVA
1º B,17,,ISABELLE VITORIA MARTINS DA SILVA
1º B,18,,JOANNA MIKELLY BARBOSA DO CARMO
1º B,19,,JONAS TYAGO NASCIMENTO DA SILVA
1º B,20,,JOSE LUCAS VASCONSELO DE SOUZA
1º B,21,,KAYLANNE VICTORIA GUIMARAES DA SILVA
1º B,22,,LÍCIA MARIA GOMES MARQUES
1º B,23,,LUIS FELIPE FRANÇA ALVES DE LIMA
1º B,24,,MARIA EDUARDA DE AGUIAR
1º B,25,,MARIA LETICIA TAVARES DE MELO E SOUZA
1º B,26,,MARIA LUIZA DE SOUZA HERCULANO
1º B,27,,MARIA VITORIA DA SILVA VIEIRA DE SOUZA
1º B,28,,MARIANA REGINA DE LIMA MORAIS DE PAIVA
1º B,29,,MARTA BEATRIZ MARIA DA SILVA
1º B,30,,MATHEUS GABRIEL CARNEIRO DA SILVA
1º B,32,,OTTO CÂNDIDO DOS SANTOS COSTA
1º B,33,,PHAMELA ELLEN BARBOSA DE LIMA
1º B,34,,RAFAEL VICTOR DE LIMA PETRÍCIO
1º B,35,,TALITA FERNANDA VALENÇA LOURENÇO DO NASCIMENTO
1º B,36,,THAMYRES RODRIGUES DE FRAGA
1º B,37,,VINICIWS EDWARDO DA SILVA INACIO
1º B,38,,WILLIAN LEANDRO CONCEICAO SILVESTRE DE LUNA
1º B,39,,YASMIM GABRIELLY FERREIRA DA SILVA
1º B,41,,BIANCA BEATRIZ DE MOURA SOARES
1º B,42,,SYMON HENRIQUE DE LIMA
1º B,43,,ERNESTO NOBRE LINS
1º C,1,,ALLYCIA PEREIRA GOMES DA SILVA
1º C,2,,ANA JULLYA NUNES CLAUDINO DE MORAES
1º C,3,,ANA LUIZA DE ARRUDA PROTETOR
1º C,4,,ANDRESSA CAROLINE DA SILVA MELO
1º C,5,,ARTHU GABRYEL OLEGARIO ARCANJO
1º C,6,,CAUA VICTOR GONCALVES DE SOUZA SANTOS
1º C,7,,CECILIA OTAVIANO DE BARROS FERREIRA
1º C,8,,CECILIA VITORIA BRITO DA SILVA
1º C,9,,ELLEN PATRICIA DIAS DA SILVA
1º C,10,,FELIPE GABRIEL DE PAULA SOUZA
1º C,11,,GABRIEL SULLYVAN MELO PRAGANA
1º C,12,,GABRYELL JOSÉ BARROS DE MEDEIROS
1º C,13,,GUILHERME FERNANDES DINIZ
1º C,14,,HELIANA SILVA FERRAZ NOGUEIRA
1º C,15,,HIGOR RAFAEL VIEIRA DO NASCIMENTO
1º C,16,,ISADORA RAQUEL SOUZA MEDEIROS ARAUJO FERREIRA
1º C,17,,JULIA LIENDRY DO NASCIMENTO ALVES
1º C,18,,KARYN ESTHER GOMES DA SILVA
1º C,19,,KAUAN RAFAEL MARQUES DA SILVA
1º C,20,,LUANNA COSMO CABRAL
1º C,21,,LUCAS ARN DE LIMA PEIXOTO
1º C,22,,MANUELA DE BARROS ALBUQUERQUE
1º C,23,,MARIA ALICE COELHO MAGALHAES
1º C,24,,MARIA EDUARDA DIONIZIO DE MELO SILVA
1º C,25,,MARIA SOFIA ALICE DA SILVA
1º C,26,,MARIA SOPHIA DANTAS DE SOUZA
1º C,27,,MARIANNY CRISTINE ALVES LIMA
1º C,28,,NAETE ISABELLY DA SILVA SANTOS
1º C,29,,NICOLE CRISTIANE LIMA DOS PRAZERES
1º C,30,,REBEKA BARBOSA DE LIMA DA SILVA
1º C,31,,RENE IAN ALVES LEITE
1º C,32,,SALATIEL SANTOS DA SILVA
1º C,33,,SARAH PEREIRA DO NASCIMENTO
1º C,34,,TIAGO HENRIQUE VENTURA LUNA
1º C,35,,VICTOR GABRYELL DE ANDRADE GONÇALVES
1º C,36,,VIVIANE PATRICIA DA SILVA
1º C,37,,YAGO VYNYCYUS DA SILVA VIEIRA
1º C,38,,YASMIN CRISTINE ALVES DA SILVA
2º A,1,,ALICE VITORIA DA SILVA BARROS
2º A,2,,ANA HELOISA DE OLIVEIRA SILVA
2º A,3,,BEATRIZ MOURA PEREIRA MELO
2º A,4,,CAIO MIQUEAS RIBEIRO DA SILVA
2º A,5,,DANIEL MARQUES PROGENIO DA SILVA
2º A,6,,DIOGO LUIZ DOS SANTOS DA SILVA CAVALCANTI
2º A,7,,EDUARDA VITORIA FELIX DE FRANÇA
2º A,8,,GABRIEL PHELIPE DE ANDRADE FERRAZ
2º A,9,,HELOISA GABRIELLY XAVIER SANTOS
2º A,10,,ISABELLE VITORIA ALVES REIS
2º A,11,,JOAO PEDRO NIELS DA GUARDA
2º A,12,,JOSE RYAN MONTEIRO DOS SANTOS
2º A,14,,KAIKY LUAN SANTOS SILVA
2º A,15,,KAILANNY CRISTINA SILVA MUNIZ
2º A,16,,KAUÃ VICTOR CARVALHO DE ANDRADE
2º A,17,,KAUANE GABRIELLY DA SILVA CRISOSTOMO
2º A,18,,LETICIA BARRETO CAVALCANTI DE ALBUQUERQUE
2º A,20,,MANUEL CARLOS BARBOSA DA SILVA NETO
2º A,21,,MARIA EDUARDA BERNARDO DA SILVA
2º A,22,,MARIA EDUARDA DA SILVA SANTOS
2º A,23,,MARIANA NAVARRO TORRES OLIVEIRA
2º A,24,,MARYANA VITORIA MARQUES DA SILVA
2º A,25,,MATHEUS HENRIQUE OLIVEIRA PERES DOS SANTOS
2º A,26,,NATALIA DE ARAUJO DA SILVA
2º A,27,,NICOLAS RENAN BARBOSA FARIAS
2º A,28,,NICOLLY DOS SANTOS GALINDO CARNEIRO
2º A,29,,OLEGARIO GUSTAVO LIMA FREITAS AYRES
2º A,30,,PAULO FERNANDO SANTOS DO AMARAL JUNIOR
2º A,31,,PAULO RICARDO BRITO DE OLIVEIRA
2º A,33,,YASMIN PAULINO DOS SANTOS
2º A,34,,YASMINI ALICIA SOUZA DE ARRUDA
2º A,35,,LUARA DA SILVA GUEDES
2º B,3,,ANTONIO PEDRO HERCULANO NETO
2º B,4,,BIANCA ALEXANDRE SANTOS DE FRANÇA
2º B,5,,CARLOS EDUARDO DE OLIVEIRA
2º B,7,,CAUA VITOR RIBEIRO DE OLIVEIRA
2º B,8,,DANIEL DAVI SANTOS FERREIRA
2º B,9,,DANILO RIBEIRO BEZERRA LEAL
2º B,10,,DAYLLA ELLEN SILVA RAMOS
2º B,11,,DEBORA SANTIAGO DA SILVA
2º B,12,,ERIKE TRAJANO ALVES
2º B,13,,FERNANDO EMERSON JANUARIO PEREIRA
2º B,14,,GABRIELLE DE MACEDO LOPES
2º B,15,,GRAZIELLA MAYZA TORRES DOS SANTOS
2º B,16,,GUILHERME DE LUNA CYSNEIROS
2º B,17,,HULISSES PIMENTEL DO NASCIMENTO
2º B,18,,ISADORA FERNANDA BARRETO LIRA
2º B,19,,LARA DANTAS GUERRA
2º B,20,,LETICIA VITORIA BARROS BRITO
2º B,21,,LUCAS ANDRADE MOURA
2º B,22,,MARIA CLARA DA SILVA VIEIRA DE SOUZA
2º B,23,,MARIA HELOIZA BEZERRA DA SILVA
2º B,24,,MARIA LAURA MARQUES BRAZ
2º B,25,,MARIA LUIZA RAQUEL DA SILVA DE ANDRADE
2º B,26,,MARIA SOPHIA SANTANA FERREIRA
2º B,27,,MIGUEL OLIVEIRA DA SILVA
2º B,28,,NICOLLE DOS SANTOS SILVA
2º B,29,,NIELLY FERNANDA BARUK DE SENA
2º B,30,,RIANA LETICIA MACIEL DE ALMEIDA
2º B,31,,SABRINA FIALHO SALES
2º B,32,,TIAGO ALEXANDRE DA SILVA
2º B,33,,VICTOR HENRIQUE SOARES MANOEL ALBINO
2º B,34,,WALTER FELIPE CASTANHA BENÍCIO DE LIMA
2º B,35,,YURI CABRAL DA SILVA
2º B,36,,CAYLANNE VICTORYA SANTOS DA SILVA
2º C,1,,ALANA REINALDO DA PAIXÃO DE OLIVEIRA
2º C,2,,AMARINA ALBERTINA DA SILVA
2º C,3,,ANA BEATRIZ DA SILVA PAIXAO
2º C,5,,CLARA LAVINEA MARQUES DA SILVA
2º C,6,,ELLIONAY NATIELLE LIMA DA COSTA
2º C,7,,EMILLY VITÓRIA ARAÚJO DE LIMA
2º C,8,,EMILY RANGEL RODRIGUES FEITOSA
2º C,10,,GABRIELLA MAYARA TORRES DOS SANTOS
2º C,11,,GABRIELLA NICOLLY RIBEIRO MUNIZ
2º C,12,,GLEYDSON ALEXSSANDRO DA SILVA SANTOS
2º C,13,,GUILHERME FERREIRA FIDELIS DE AZEVEDO
2º C,14,,GUSTAVO HENRIQUE BARBOSA DE MELO
2º C,15,,ISABELLE BEATRIZ SANTANA DOS SANTOS
2º C,17,,JOAO LUCAS SOARES PONTES DE SOUZA
2º C,18,,JOSE ERICK DA SILVA BARBOSA
2º C,19,,JULIA DA SILVA
2º C,20,,JULIA GABRIELA OLIVEIRA FALCÃO
2º C,21,,JULIA THAMIRES FERREIRA GOMES
2º C,24,,MARIA CECILIA DA SILVA PINTO ALVES DOS SANTOS
2º C,25,,MARIA CLARA ALVES DE CARVALHO
2º C,26,,MARIA CLARA COELHO
2º C,27,,MARIA EDUARDA DA SILVA VICENTE
2º C,28,,MARIA EDUARDA DOS SANTOS AMARAL
2º C,29,,MATHEUS GABRIEL SILVA DE SANTANA
2º C,30,,NATASHA MELISSA EVARISTO DA COSTA SILVA
2º C,31,,NAUANY PEREIRA RODRIGUES DA SILVA
2º C,32,,OLEGARIO GUILHERME LIMA FREITAS AYRES
2º C,33,,PEDRO MARLON MOURA DE MELO
2º C,34,,RYVANI RAYSSA FERREIRA DOS SANTOS
2º C,35,,STEPHANE FERNANDA DOS SANTOS OLIVEIRA
2º C,36,,THAMYRES EMANUELLY CABRAL DE LIMA
2º C,38,,ESTHER STHEFANNY SILVA SIQUEIRA
2º D,1,,ADRIEL NUNES DOS SANTOS
2º D,2,,ADRIELLY CAMILY BATISTA DA COSTA
2º D,3,,ANA PATRICIA DA CUNHA SILVA
2º D,4,,CAMILLY VITORIA DA SILVA CORREA
2º D,5,,CAUA PEREIRA MUNIZ PAIVA
2º D,6,,CAUAN DE LIMA PINHEIRO LACERDA
2º D,7,,DANIEL MENEZES DE OLIVEIRA SILVA
2º D,8,,DAVI SOBREIRA DIAS
2º D,9,,DEBORA HELOISA LIMA DA CUNHA
2º D,10,,JOAO ESCOBAR DE MENEZES FERREIRA
2º D,11,,JOAO GABRIEL MORAIS DO NASCIMENTO
2º D,12,,JOÃO VICTOR DE LIRA GOMES
2º D,13,,JOAO VICTOR FERREIRA DO LIVRAMENTO
2º D,14,,JOSE ROBERTO SANTOS DE MELO
2º D,15,,LAISA BELEM NUNES CAVALCANTE
2º D,16,,MARCELO CABRAL DA SILVA
2º D,17,,MARIA CLARA PONCIANO GUIMARAES
2º D,18,,MARIA ELIZA MARTINS DE ARAUJO
2º D,21,,THAYSA ELLEN FERREIRA BASTOS
2º D,22,,VICTOR GABRIEL SANTOS DE MIRANDA
3º A,1,,ALICIA ELLEN MARQUES DA SILVA
3º A,2,,ALICYA THIFANNY SOUZA SILVA
3º A,3,,AMANDA MANUELLE ARRUDA LIMA
3º A,4,,ARCANJO MARNY DA COSTA PETER
3º A,5,,ARIANNY MONALYSA MONTEIRO VITAL
3º A,6,,CAUANE GRAZYELLY GOMES DA SILVA
3º A,7,,EDUARDO HENRIQUE CARNEIRO DA SILVA
3º A,8,,ESTEVO PEREIRA DA SILVA ALVES
3º A,9,,EULALIA MARIA DA CONCEIÇAO NASCIMENTO
3º A,10,,GABRIEL CRISTYAN CORDEIRO DE FREITAS
3º A,11,,GEOVANA BERNARDO SOARES
3º A,12,,GIOVANNA DE JESUS REIS
3º A,13,,GLEYBSON CORREIA DA SILVA
3º A,14,,HERIBERTO SILVA FERRAZ NOGUEIRA
3º A,15,,HEVERTON WENDELL CONCEIÇAO PEREIRA
3º A,16,,INGRID LUIZA DA SILVA PEREIRA
3º A,17,,IRIS GABRIELY SILVA DE OLIVEIRA
3º A,18,,JOANA GEOVANA AZEVEDO GUEDES LEITE
3º A,19,,JOAO ANTONIO RODRIGUES NOBRE
3º A,21,,KYWANY EYSHELLA EPHRAIM DE OLIVEIRA
3º A,22,,LARA SOPHIA DE ANDRADE MELO
3º A,23,,LUIZA GUIMARAES PASCOAL
3º A,24,,MARIA CLARA DA SILVA LEAO
3º A,25,,MARIA EDUARDA CORREIA DE LIMA
3º A,26,,MARIA EDUARDA MARINHO DE AGUIAR
3º A,27,,MARIANE BEATRIZ BARBOSA DE MELO
3º A,28,,MAYSA BARBOSA DA SILVA
3º A,31,,NETHILIE SOARES DE MELO
3º A,32,,NICOLAS RAPHAEL GOMES DE BARROS
3º A,33,,RIQUELME GOMES DA SILVA
3º A,34,,SAVIO GABRIEL OLIVEIRA GOMES
3º A,35,,SOPHIA LIMA CHAVES
3º A,36,,SUELLEN FELIPE DE ALBUQUERQUE
3º A,37,,VITORIA MOURA DO CANTO FERREIRA
3º A,38,,WILLIAM EDUARDO SILVA BARBOSA DE LIMA
3º A,39,,CAMILLA GABRIELE FILGUEIRA CARVALHO DE SOUZA
3º A,40,,MARIANA DE SOUZA BORBA
3º B,2,,ALLEX VICTOR DA SILVA NUNES
3º B,4,,CARLOS DANIEL MENESES DE OLIVEIRA MORAES
3º B,5,,CAUANY DE ANDRADE GIL RODRIGUES
3º B,6,,CHRYSTIAN RODRIGUES CORREIA DE SANTANA
3º B,7,,EDUARDO ANDRADE DE ASSIS
3º B,8,,ELOANNY LAUREN ALMEIDA DA SILVA
3º B,9,,ESTHEFANY NICOLY VALENTIM DA SILVA
3º B,10,,ESTHER CAMILI CAVALCANTI DE FARIAS
3º B,11,,EWELLYN THAUANE FERREIRA DOS SANTOS
3º B,12,,GABRIELLE SOFFIA GOMES GUILHERMINO
3º B,13,,HENRIQUE SIQUEIRA DA SILVA NETO
3º B,14,,JAMILLY KAYLANE ALVES DA SILVA
3º B,15,,JOANA DA SILVA ALMEIDA
3º B,16,,JOAO VICTOR DA SILVA GONÇALVES
3º B,17,,JULIA FRANCIELY PRAZERES DE SANTANA PEREIRA
3º B,18,,KARLA LETTICIA CARVALHO SILVA FERREIRA
3º B,19,,LARA LETICIA BORBA GONÇALVES
3º B,20,,LARA NATALYA DA SILVA BARROS
3º B,22,,LUIS GABRIEL FELIX COELHO
3º B,23,,MARIA ISABELA MARQUES OLIVEIRA DOS SANTOS
3º B,24,,MARIA LUIZA DA SILVA PROCOPIO
3º B,25,,MARIA LUIZA DOS SANTOS SILVA
3º B,26,,MARIA LUIZE QUEIROZ FERREIRA DE LIMA
3º B,27,,MARIA LUYZA BARBOSA MOURA
3º B,29,,MARIANA GOMES DA SILVA
3º B,30,,MATEUS ELOI PEREIRA DE PAULA
3º B,31,,MATHEUS GOMES DE SOUZA DOS SANTOS
3º B,32,,MAYZA TAVARES DE SANTANA
3º B,33,,MIGUEL FRUCTUOSO NUNES
3º B,34,,MOISES PATRICIO VIEIRA
3º B,35,,NICOLLY STEFANIE RODRIGUES FARIAS
3º B,36,,VITORIA RAKELLY DE SANTANA TAVARES
3º B,37,,YHANNA LAURA SANTANA DE ANDRADE
3º B,38,,BEATRIZ PRAZERES DE PONTES
3º C,1,,ANNA BEATRIZ DA SILVA GOMES
3º C,2,,ARTHUR JOSE DUARTE DE SOUZA
3º C,3,,BARBARA LUIZA GOMES DA COSTA
3º C,4,,CAYO VICTOR DA SILVA SANTOS
3º C,5,,CECILIA BARBOSA CALDAS
3º C,7,,DANIEL PATRICIO PINHEIRO DE SOUSA
3º C,8,,DAVI MUNIZ DO NASCIMENTO JUNIOR
3º C,9,,DOUGLAS LUCAS DE AZEVEDO NUNES DA SILVA
3º C,10,,ESTER NOELLY ALEXANDRINA DA SILVA
3º C,11,,GABRIEL DELGADO MOREIRA DE ALBUQUERQUE
3º C,12,,GABRIELA VITORIA MARIA DA SILVA
3º C,13,,GEOVANE DA SILVA CORDEIRO
3º C,14,,IASMYM ELLEN MORAIS SANTOS PESSOA
3º C,15,,JULIA CAMILLY DA SILVA COSTA
3º C,16,,KAUA WILLIAN FRANCA DA SILVA
3º C,17,,LETICIA DE ALBUQUERQUE PESSOA MELO
3º C,18,,MARIA BEATRIZ TRINDADE VITOR LIMA
3º C,19,,MARIA CLARA CRUZ DE MEDEIROS SOARES DA SILVA
3º C,20,,MARIA CLARA FONTES DA SILVA PINHEIRO
3º C,21,,MARIA GABRIELLY DO MONTE PEREIRA
3º C,22,,MARILIA BEATRIZ DA CONCEICAO XAVIER
3º C,23,,MATEUS EDMAR VICENTE DE FREITAS
3º C,24,,MIGUEL LUCAS ALBUQUERQUE DA SILVA
3º C,25,,PEDRO HENRIQUE CAVALCANTI RAMALHO
3º C,26,,RAFAEL TORRES DOS SANTOS
3º C,27,,RAISSA GABRIELLY VENTURA LUNA
3º C,28,,RAPHAEL LOPES DA SILVA
3º C,29,,RAQUEL BEATRIZ LIMA DA SILVA
3º C,30,,RENATO JUNE CAVALCANTE LIMA FILHO
3º C,31,,SOFIA LARISSA SILVA SANTOS
3º C,32,,TALYSSON RIBEIRO LIMA
3º C,33,,THYAGO HENRIQUE DOS SANTOS BEZERRA
3º C,34,,VITOR GABRIEL DOS SANTOS VIEIRA DA SILVA
3º C,35,,WALLISON DANTAS RAMOS DA SILVA
3º C,36,,YTALO MENDES DA SILVA
3º C,37,,MARIA JULIA DA SILVA ARRUDA"""

# ---------------------------------------------------------
# GABARITOS BASE DE CADA ANO/SÉRIE
# ---------------------------------------------------------
GABARITO_1ANO_BASE = {
    1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "A", 7: "B", 8: "C", 9: "D", 10: "E",
    11: "A", 12: "B", 13: "C", 14: "D", 15: "E", 16: "A", 17: "B", 18: "C", 19: "D", 20: "E",
    21: "A", 22: "B", 23: "C", 24: "D", 25: "A", 26: "B", 27: "C", 28: "D", 29: "E", 30: "A",
    31: "A", 32: "B", 33: "C", 34: "D", 35: "E", 36: "A", 37: "B", 38: "C", 39: "D", 40: "E"
}

GABARITO_2ANO_BASE = {
    1: "B", 2: "C", 3: "D", 4: "E", 5: "A", 6: "B", 7: "C", 8: "D", 9: "E", 10: "A",
    11: "B", 12: "C", 13: "D", 14: "E", 15: "A", 16: "B", 17: "C", 18: "D", 19: "E", 20: "A",
    21: "B", 22: "C", 23: "D", 24: "E", 25: "B", 26: "C", 27: "D", 28: "E", 29: "A", 30: "B",
    31: "B", 32: "C", 33: "D", 34: "E", 35: "A", 36: "B", 37: "C", 38: "D", 39: "E", 40: "A"
}

GABARITO_3ANO_BASE = {
    1: "C", 2: "D", 3: "E", 4: "A", 5: "B", 6: "C", 7: "D", 8: "E", 9: "A", 10: "B",
    11: "C", 12: "D", 13: "E", 14: "A", 15: "B", 16: "C", 17: "D", 18: "E", 19: "A", 20: "B",
    21: "C", 22: "D", 23: "E", 24: "A", 25: "C", 26: "D", 27: "E", 28: "A", 29: "B", 30: "C",
    31: "C", 32: "D", 33: "E", 34: "A", 35: "B", 36: "C", 37: "D", 38: "E", 39: "A", 40: "B"
}

GABARITOS_MULTI_ANO_DEFAULT = {
    "1º Ano": GABARITO_1ANO_BASE.copy(),
    "2º Ano": GABARITO_2ANO_BASE.copy(),
    "3º Ano": GABARITO_3ANO_BASE.copy(),
}

DISCIPLINAS_MAP = {
    "Filosofia (01-05)": range(1, 6),
    "História (06-10)": range(6, 11),
    "Geografia (11-15)": range(11, 16),
    "Sociologia (16-20)": range(16, 21),
    "Educação Física (21-24)": range(21, 25),
    "Inglês (25-30)": range(25, 31),
    "Português (31-40)": range(31, 41),
}

# ---------------------------------------------------------
# PERSISTÊNCIA EM DISCO (JSON)
# ---------------------------------------------------------
def salvar_gabaritos_em_disco(gabaritos_dict):
    try:
        with open(ARQUIVO_GABARITOS_JSON, "w", encoding="utf-8") as f:
            json.dump(gabaritos_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar gabaritos no arquivo: {e}")

def carregar_gabaritos_do_disco():
    if os.path.exists(ARQUIVO_GABARITOS_JSON):
        try:
            with open(ARQUIVO_GABARITOS_JSON, "r", encoding="utf-8") as f:
                dados_json = json.load(f)

            gabaritos_carregados = {}
            for ano, gab in dados_json.items():
                gabaritos_carregados[ano] = {int(q): str(r) for q, r in gab.items()}
            return gabaritos_carregados
        except Exception:
            pass

    salvar_gabaritos_em_disco(GABARITOS_MULTI_ANO_DEFAULT)
    return {
        "1º Ano": GABARITO_1ANO_BASE.copy(),
        "2º Ano": GABARITO_2ANO_BASE.copy(),
        "3º Ano": GABARITO_3ANO_BASE.copy(),
    }

def salvar_historico_em_disco(historico_list):
    try:
        with open(ARQUIVO_HISTORICO_JSON, "w", encoding="utf-8") as f:
            json.dump(historico_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar histórico no arquivo: {e}")

def carregar_historico_do_disco():
    if os.path.exists(ARQUIVO_HISTORICO_JSON):
        try:
            with open(ARQUIVO_HISTORICO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def carregar_estudantes():
    if os.path.exists(ARQUIVO_ALUNOS_TXT):
        try:
            df = pd.read_csv(ARQUIVO_ALUNOS_TXT)
        except Exception:
            df = pd.read_csv(io.StringIO(DADOS_ALUNOS_EMBUTIDOS))
    else:
        df = pd.read_csv(io.StringIO(DADOS_ALUNOS_EMBUTIDOS))

    turmas = {}
    for turma, group in df.groupby("Turma", sort=False):
        alunos = []
        for _, row in group.iterrows():
            num = str(int(row["Número"])) if pd.notna(row["Número"]) and str(row["Número"]).strip() != "" else ""
            mat = str(int(row["Matrícula"])) if pd.notna(row["Matrícula"]) and str(row["Matrícula"]).strip() != "" else ""
            nome = str(row["Nome"]).strip()
            alunos.append({"numero": num, "matricula": mat, "nome": nome})
        turmas[str(turma).strip()] = alunos

    return turmas

def obter_ano_da_turma(turma):
    if "1º" in turma or "1" in turma:
        return "1º Ano"
    elif "2º" in turma or "2" in turma:
        return "2º Ano"
    elif "3º" in turma or "3" in turma:
        return "3º Ano"
    return "1º Ano"

def obter_disciplina(q):
    for disc, q_range in DISCIPLINAS_MAP.items():
        if q in q_range:
            return disc
    return "Desconhecida"

# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="EREM Joaquim Távora - Corretor OMR",
    layout="wide",
    page_icon="📌",
)

# Aplica o tema visual JT
aplicar_estilo_jt()

# Inicializações da Sessão
if "gabaritos_oficiais" not in st.session_state:
    st.session_state["gabaritos_oficiais"] = carregar_gabaritos_do_disco()

if "historico" not in st.session_state:
    st.session_state["historico"] = carregar_historico_do_disco()

if "dados_turmas" not in st.session_state:
    st.session_state["dados_turmas"] = carregar_estudantes()

# ---------------------------------------------------------
# CABEÇALHO COM EMBLEMA JT
# ---------------------------------------------------------
st.markdown("""
    <div class="jt-header-container">
        <div class="jt-logo-emblem">JT</div>
        <div>
            <div class="jt-header-title">Corretor de Cartão-Resposta OMR</div>
            <div class="jt-header-subtitle">EREM JOAQUIM TÁVORA • SIMULADO TRIMESTRAL</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# VISÃO COMPUTACIONAL ADAPTATIVA (PAISAGEM E RETRATO)
# ---------------------------------------------------------
def auto_orientar_e_retificar_completo(imagem, largura=1200, altura=800):
    """
    Detecta as 4 âncoras pretas nos cantos do cartão-resposta.
    Suporta fotos em MODO PAISAGEM ou MODO RETRATO e rotações de 90°, 180° e 270°.
    """
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray_enhanced, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 8
    )

    cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    h_img, w_img = imagem.shape[:2]

    candidatos = []
    for c in cnts:
        area = cv2.contourArea(c)
        if 30 < area < (w_img * h_img * 0.05):
            x, y, w, h = cv2.boundingRect(c)
            aspect = float(w) / h
            extent = area / float(w * h)
            if 0.55 <= aspect <= 1.45 and extent > 0.50:
                cx = int(x + w / 2.0)
                cy = int(y + h / 2.0)
                candidatos.append((cx, cy, area, x, y, w, h))

    if len(candidatos) < 4:
        if h_img > w_img:
            imagem = cv2.rotate(imagem, cv2.ROTATE_90_CLOCKWISE)
        return cv2.resize(imagem, (largura, altura))

    tl = min(candidatos, key=lambda c: c[0] + c[1])
    tr = max(candidatos, key=lambda c: c[0] - c[1])
    br = max(candidatos, key=lambda c: c[0] + c[1])
    bl = min(candidatos, key=lambda c: c[0] - c[1])

    pts_origem = np.array([[tl[0], tl[1]], [tr[0], tr[1]], [br[0], br[1]], [bl[0], bl[1]]], dtype="float32")

    dist_top = np.linalg.norm(pts_origem[0] - pts_origem[1])
    dist_left = np.linalg.norm(pts_origem[0] - pts_origem[3])

    if dist_left > dist_top:
        pts_destino = np.array([[0, 0], [altura - 1, 0], [altura - 1, largura - 1], [0, largura - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(pts_origem, pts_destino)
        warped = cv2.warpPerspective(imagem, M, (altura, largura))
        warped = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        pts_destino = np.array([[0, 0], [largura - 1, 0], [largura - 1, altura - 1], [0, altura - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(pts_origem, pts_destino)
        warped = cv2.warpPerspective(imagem, M, (largura, altura))

    if warped.shape[0] != altura or warped.shape[1] != largura:
        warped = cv2.resize(warped, (largura, altura))

    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    top_region = warped_gray[10:120, 100:1100]
    bot_region = warped_gray[680:790, 100:1100]

    top_edges = np.sum(cv2.Canny(top_region, 50, 150))
    bot_edges = np.sum(cv2.Canny(bot_region, 50, 150))

    if top_edges > bot_edges * 1.15:
        warped = cv2.rotate(warped, cv2.ROTATE_180)

    return warped

# ---------------------------------------------------------
# ALGORITMO OMR DE ALTA PRECISÃO (SUPORTE PARCIAL E COMPLETO)
# ---------------------------------------------------------
def ler_respostas_40_questoes(img_warped, gabarito_oficial=None, limiar_preenchimento=35.0, q_range_permitido=None):
    """
    Analisa o interior das bolinhas (% Fill Ratio).
    Se q_range_permitido for informado (ex: range(1, 21)), processa apenas aquele intervalo de questões.
    """
    if q_range_permitido is None:
        q_range_permitido = range(1, 41)

    gray = cv2.cvtColor(img_warped, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray_proc = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray_proc, (3, 3), 0)

    img_annotated = img_warped.copy()

    opcoes = ["A", "B", "C", "D", "E"]
    respostas_aluno = {}

    largura_total = 1200
    altura_total = 800

    blocos = [
        (1, 5, 0, 0.285, 0.535),    # Filosofia (Q01 - Q05)
        (6, 10, 0, 0.625, 0.935),   # História (Q06 - Q10)
        (11, 15, 1, 0.285, 0.535),  # Geografia (Q11 - Q15)
        (16, 20, 1, 0.625, 0.935),  # Sociologia (16 - 20)
        (21, 24, 2, 0.285, 0.485),  # Ed. Física (21 - 24)
        (25, 30, 2, 0.585, 0.935),  # Inglês (25 - 30)
        (31, 40, 3, 0.285, 0.935),  # Português (31 - 40)
    ]

    for q_start, q_end, col_idx, y_start_ratio, y_end_ratio in blocos:
        num_questoes_bloco = q_end - q_start + 1
        col_x_start = col_idx * (largura_total / 4.0)
        col_w = largura_total / 4.0

        b_start_x = col_x_start + col_w * 0.25
        b_end_x = col_x_start + col_w * 0.93
        b_step = (b_end_x - b_start_x) / 5.0

        y_top_bloco = altura_total * y_start_ratio
        y_bot_bloco = altura_total * y_end_ratio

        x_block_start = int(col_x_start)
        x_block_end = int(col_x_start + col_w)
        y_block_start = int(y_top_bloco - 15)
        y_block_end = int(y_bot_bloco + 15)

        roi_block = blurred[y_block_start:y_block_end, x_block_start:x_block_end]
        if roi_block.size == 0:
            continue
        _, thresh_block = cv2.threshold(roi_block, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        for row in range(num_questoes_bloco):
            num_questao = q_start + row

            # Se a questão atual não estiver no intervalo permitido para a foto, ignora
            if num_questao not in q_range_permitido:
                continue

            y_center = y_top_bloco + (row + 0.5) * ((y_bot_bloco - y_top_bloco) / float(num_questoes_bloco))

            taxas_preenchimento = []
            coords_opcoes = []

            for opt_idx in range(5):
                bx = b_start_x + (opt_idx + 0.5) * b_step
                by = y_center

                ix, iy = int(bx), int(by)
                win_r = 3
                crop_win = gray_proc[max(0, iy - win_r):min(altura_total, iy + win_r + 1),
                                     max(0, ix - win_r):min(largura_total, ix + win_r + 1)]
                
                if crop_win.size > 0:
                    min_loc = np.unravel_index(np.argmin(crop_win), crop_win.shape)
                    best_bx = (ix - win_r) + min_loc[1]
                    best_by = (iy - win_r) + min_loc[0]
                else:
                    best_bx, best_by = ix, iy

                mask_inner = np.zeros_like(roi_block, dtype=np.uint8)
                rel_cx = int(best_bx - x_block_start)
                rel_cy = int(best_by - y_block_start)

                cv2.circle(mask_inner, (rel_cx, rel_cy), 7, 255, -1)

                pix_marcados = cv2.countNonZero(cv2.bitwise_and(thresh_block, mask_inner))
                total_pix_mask = cv2.countNonZero(mask_inner)

                fill_ratio = (pix_marcados / float(total_pix_mask)) * 100.0 if total_pix_mask > 0 else 0.0

                taxas_preenchimento.append(fill_ratio)
                coords_opcoes.append((int(best_bx), int(best_by)))

            max_idx = int(np.argmax(taxas_preenchimento))
            max_val = taxas_preenchimento[max_idx]

            outras_taxas = [t for i, t in enumerate(taxas_preenchimento) if i != max_idx]
            segunda_maior = max(outras_taxas) if outras_taxas else 0.0

            if max_val >= limiar_preenchimento and (max_val - segunda_maior) >= 12.0:
                resp_detectada = opcoes[max_idx]
                idx_marcado = max_idx
            else:
                resp_detectada = "Branco/Nulo"
                idx_marcado = -1

            respostas_aluno[num_questao] = resp_detectada
            gab_correto = gabarito_oficial.get(num_questao) if gabarito_oficial else None

            for opt_idx, (bx, by) in enumerate(coords_opcoes):
                opcao_letra = opcoes[opt_idx]

                if opt_idx == idx_marcado:
                    if gab_correto and opcao_letra == gab_correto:
                        cor = (0, 255, 0)
                    elif gab_correto and opcao_letra != gab_correto:
                        cor = (0, 0, 255)
                    else:
                        cor = (0, 255, 255)
                    cv2.circle(img_annotated, (bx, by), 11, cor, -1)
                elif gab_correto and opcao_letra == gab_correto and resp_detectada != gab_correto:
                    cv2.circle(img_annotated, (bx, by), 11, (255, 0, 0), 2)

    return respostas_aluno, img_annotated

# ---------------------------------------------------------
# ABAS DE NAVEGAÇÃO DO APLICATIVO
# ---------------------------------------------------------
tab_correcao, tab_gabarito, tab_estudantes, tab_relatorio = st.tabs([
    "📷 Corrigir Prova",
    "📝 Gabaritos Oficiais por Ano/Disciplina",
    "👥 Estudantes por Turma",
    "📊 Resultados da Turma",
])

# ---------------------------------------------------------
# ABA 1: CORRIGIR PROVA (FOTO ÚNICA OU DUAS FOTOS)
# ---------------------------------------------------------
with tab_correcao:
    st.header("Captura ou Upload do Cartão de Respostas")

    col_info, col_cam = st.columns([1, 2])

    with col_info:
        st.subheader("Identificação do Estudante")

        dados_turmas = st.session_state["dados_turmas"]
        lista_turmas = list(dados_turmas.keys())

        turma_selecionada = st.selectbox(
            "Selecione a Turma:",
            options=lista_turmas,
            index=0 if lista_turmas else 0,
        )

        ano_estudante = obter_ano_da_turma(turma_selecionada)
        alunos_da_turma = dados_turmas.get(turma_selecionada, [])

        opcoes_alunos = []
        for a in alunos_da_turma:
            label = f"Nº {a['numero']} - {a['nome']}" if a["numero"] else f"{a['nome']}"
            opcoes_alunos.append(label)

        if opcoes_alunos:
            aluno_idx = st.selectbox(
                "Selecione o Aluno:",
                range(len(opcoes_alunos)),
                format_func=lambda i: opcoes_alunos[i],
            )
            aluno_obj = alunos_da_turma[aluno_idx]

            nome_aluno = aluno_obj["nome"]
            num_aluno = aluno_obj["numero"]
            mat_aluno = aluno_obj["matricula"]
        else:
            nome_aluno = st.text_input("Nome do Aluno:")
            num_aluno = ""
            mat_aluno = ""

        with st.expander("📄 Ficha do Aluno e Gabarito Vinculado", expanded=True):
            st.markdown(f"**Nome:** {nome_aluno}")
            st.markdown(f"**Turma:** {turma_selecionada} | **Nº Chamada:** {num_aluno if num_aluno else 'N/A'}")
            st.info(f"🎯 **Gabarito Oficial Aplicado:** {ano_estudante}")

        st.divider()
        st.subheader("Ajustes da Leitura OMR")
        sensibilidade_omr = st.slider(
            "Limiar de Preenchimento (% Mínima de Tinta)",
            min_value=15.0,
            max_value=60.0,
            value=35.0,
            step=1.0,
            help="Defina a porcentagem mínima de tinta/lápis para considerar a bolinha marcada."
        )

    with col_cam:
        modo_fotos = st.radio(
            "Modo de Captura:",
            ["📸 Foto Única (Cartão Completo)", "📸 Duas Fotos Complementares (Metade 1 + Metade 2)"],
            horizontal=True,
        )

        origem = st.radio(
            "Fonte da Imagem:",
            ["Câmera", "Enviar Arquivo (Upload)"],
            horizontal=True,
        )

        img_input_1 = None
        img_input_2 = None

        if modo_fotos == "📸 Foto Única (Cartão Completo)":
            if origem == "Câmera":
                foto = st.camera_input("Posicione o cartão de respostas (Modo Paisagem ou Retrato)")
                if foto:
                    img_input_1 = foto
            else:
                upload_img = st.file_uploader(
                    "Envie uma foto do cartão de respostas completo",
                    type=["png", "jpg", "jpeg"],
                    key="up_unica"
                )
                if upload_img:
                    img_input_1 = upload_img
        else:
            st.caption("📌 **Tire duas fotos aproximadas:** Foto 1 para Q01-20 (Filosofia, História, Geografia, Sociologia) e Foto 2 para Q21-40 (Ed. Física, Inglês, Português).")
            c_f1, c_f2 = st.columns(2)

            with c_f1:
                st.markdown("**Foto 1 - Metade 1 (Q01 a Q20)**")
                if origem == "Câmera":
                    foto1 = st.camera_input("Foto da Metade 1 (Q01-20)", key="cam_m1")
                    if foto1:
                        img_input_1 = foto1
                else:
                    up1 = st.file_uploader("Upload Metade 1 (Q01-20)", type=["png", "jpg", "jpeg"], key="up_m1")
                    if up1:
                        img_input_1 = up1

            with c_f2:
                st.markdown("**Foto 2 - Metade 2 (Q21 a Q40)**")
                if origem == "Câmera":
                    foto2 = st.camera_input("Foto da Metade 2 (Q21-40)", key="cam_m2")
                    if foto2:
                        img_input_2 = foto2
                else:
                    up2 = st.file_uploader("Upload Metade 2 (Q21-40)", type=["png", "jpg", "jpeg"], key="up_m2")
                    if up2:
                        img_input_2 = up2

    # Processamento da Correção
    pode_processar = False
    if modo_fotos == "📸 Foto Única (Cartão Completo)" and img_input_1 is not None:
        pode_processar = True
    elif modo_fotos != "📸 Foto Única (Cartão Completo)" and img_input_1 is not None and img_input_2 is not None:
        pode_processar = True

    if pode_processar:
        if not nome_aluno:
            st.warning("⚠️ Por favor, selecione ou informe o nome do aluno.")
        else:
            gabaritos_todos = st.session_state["gabaritos_oficiais"]
            gabarito = gabaritos_todos.get(ano_estudante, gabaritos_todos.get("1º Ano", {}))

            if modo_fotos == "📸 Foto Única (Cartão Completo)":
                file_bytes = np.asarray(bytearray(img_input_1.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                img_warped = auto_orientar_e_retificar_completo(img)
                respostas_aluno, img_annotated_1 = ler_respostas_40_questoes(
                    img_warped, gabarito, limiar_preenchimento=sensibilidade_omr, q_range_permitido=range(1, 41)
                )
                img_annotated_2 = None
            else:
                # Foto 1 (Q01 a Q20)
                file_bytes_1 = np.asarray(bytearray(img_input_1.read()), dtype=np.uint8)
                img1 = cv2.imdecode(file_bytes_1, cv2.IMREAD_COLOR)
                warped1 = auto_orientar_e_retificar_completo(img1)

                resp1, img_annotated_1 = ler_respostas_40_questoes(
                    warped1, gabarito, limiar_preenchimento=sensibilidade_omr, q_range_permitido=range(1, 21)
                )

                # Foto 2 (Q21 a Q40)
                file_bytes_2 = np.asarray(bytearray(img_input_2.read()), dtype=np.uint8)
                img2 = cv2.imdecode(file_bytes_2, cv2.IMREAD_COLOR)
                warped2 = auto_orientar_e_retificar_completo(img2)

                resp2, img_annotated_2 = ler_respostas_40_questoes(
                    warped2, gabarito, limiar_preenchimento=sensibilidade_omr, q_range_permitido=range(21, 41)
                )

                respostas_aluno = {}
                respostas_aluno.update(resp1)
                respostas_aluno.update(resp2)

            acertos_por_disc = {}
            total_por_disc = {
                "Filosofia (01-05)": 5, "História (06-10)": 5, "Geografia (11-15)": 5,
                "Sociologia (16-20)": 5, "Educação Física (21-24)": 4,
                "Inglês (25-30)": 6, "Português (31-40)": 10
            }

            detalhes = []
            total_acertos = 0

            for q in range(1, 41):
                resp = respostas_aluno.get(q, "Branco/Nulo")
                gab = gabarito.get(q, "-")
                correto = (resp == gab)
                disc = obter_disciplina(q)

                if disc not in acertos_por_disc:
                    acertos_por_disc[disc] = 0

                if correto:
                    acertos_por_disc[disc] += 1
                    total_acertos += 1

                detalhes.append({
                    "Questão": q,
                    "Disciplina": disc,
                    "Resposta Aluno": resp,
                    "Gabarito": gab,
                    "Status": "✅ Acertou" if correto else "❌ Errou",
                })

            nota = (total_acertos / 40.0) * 10.0

            st.divider()
            st.subheader("Resumo do Desempenho")

            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Acertos", f"{total_acertos} / 40")
            m2.metric("Nota Final", f"{nota:.2f} / 10.0")
            m3.metric("Estudante / Turma", f"{nome_aluno} ({turma_selecionada} - {ano_estudante})")

            cols_disc = st.columns(len(acertos_por_disc))
            for i, (d_nome, d_acertos) in enumerate(acertos_por_disc.items()):
                tot = total_por_disc.get(d_nome, 5)
                cols_disc[i].metric(d_nome.split(" ")[0], f"{d_acertos}/{tot}")

            if st.button("💾 Salvar Resultado no Histórico", type="primary"):
                registro = {
                    "Série": ano_estudante,
                    "Turma": turma_selecionada,
                    "Nº": num_aluno,
                    "Matrícula": mat_aluno,
                    "Aluno": nome_aluno,
                    "Total Acertos": total_acertos,
                    "Nota Final": round(nota, 2),
                }
                for d_nome, d_acertos in acertos_por_disc.items():
                    registro[d_nome.split(" ")[0]] = f"{d_acertos}/{total_por_disc.get(d_nome, 5)}"

                st.session_state["historico"].append(registro)
                salvar_historico_em_disco(st.session_state["historico"])
                st.success(f"Resultado de {nome_aluno} salvo com sucesso!")

            col_img, col_det = st.columns(2)
            with col_img:
                st.subheader("Imagens Processadas (Overlay OMR)")
                if img_annotated_2 is None:
                    st.image(img_annotated_1, channels="BGR", use_container_width=True)
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Metade 1 (Q01-20)")
                        st.image(img_annotated_1, channels="BGR", use_container_width=True)
                    with c2:
                        st.caption("Metade 2 (Q21-40)")
                        st.image(img_annotated_2, channels="BGR", use_container_width=True)

                st.caption("🟢 Verde = Acerto | 🔴 Vermelho = Erro | 🔵 Azul = Gabarito Correto")

            with col_det:
                st.subheader("Detalhamento por Questão")
                st.dataframe(pd.DataFrame(detalhes), height=380, use_container_width=True)

# ---------------------------------------------------------
# ABA 2: GABARITOS OFICIAIS POR ANO E DISCIPLINA
# ---------------------------------------------------------
with tab_gabarito:
    st.header("Cadastrar e Gerenciar Gabaritos Oficiais")
    st.caption("Defina as respostas corretas por Ano/Série e por Disciplina. Salvas em disco permanentemente.")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        ano_gab_sel = st.selectbox(
            "Selecione o Ano / Série para Editar:",
            ["1º Ano", "2º Ano", "3º Ano"],
            index=0,
        )

    with col_s2:
        disc_filtro = st.selectbox(
            "Filtrar por Disciplina:",
            ["Todas as Disciplinas"] + list(DISCIPLINAS_MAP.keys()),
            index=0,
        )

    st.divider()
    col_df_gab, col_act_gab = st.columns([2, 1])

    gabarito_ano_atual = st.session_state["gabaritos_oficiais"].get(ano_gab_sel, {})

    with col_act_gab:
        st.subheader("Ações do Gabarito")
        if st.button(f"🔄 Restaurar Padrão do {ano_gab_sel}"):
            st.session_state["gabaritos_oficiais"][ano_gab_sel] = GABARITOS_MULTI_ANO_DEFAULT[ano_gab_sel].copy()
            salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"])
            st.success(f"Gabarito padrão do {ano_gab_sel} restaurado e salvo!")
            st.rerun()

        if st.button("🔄 Restaurar Todos os Anos"):
            st.session_state["gabaritos_oficiais"] = {
                "1º Ano": GABARITO_1ANO_BASE.copy(),
                "2º Ano": GABARITO_2ANO_BASE.copy(),
                "3º Ano": GABARITO_3ANO_BASE.copy(),
            }
            salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"])
            st.success("Todos os gabaritos foram restaurados para o padrão e salvos!")
            st.rerun()

        st.divider()
        st.subheader("Importar via Arquivo")
        arquivo_gab_up = st.file_uploader(
            f"Upload de Gabarito para o {ano_gab_sel} (CSV ou XLSX)",
            type=["csv", "xlsx"],
        )
        if arquivo_gab_up:
            try:
                df_up_g = pd.read_csv(arquivo_gab_up) if arquivo_gab_up.name.endswith(".csv") else pd.read_excel(arquivo_gab_up)
                if "Questão" in df_up_g.columns and "Gabarito" in df_up_g.columns:
                    nuevo_dic = dict(zip(df_up_g["Questão"][:40], df_up_g["Gabarito"][:40]))
                    st.session_state["gabaritos_oficiais"][ano_gab_sel].update(nuevo_dic)
                    salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"])
                    st.success(f"Gabarito do {ano_gab_sel} atualizado e salvo no arquivo!")
                    st.rerun()
                else:
                    st.error("O arquivo precisa conter as colunas 'Questão' e 'Gabarito'.")
            except Exception as err_g:
                st.error(f"Erro ao carregar arquivo: {err_g}")

    with col_df_gab:
        st.subheader(f"Tabela de Respostas ({ano_gab_sel})")

        if disc_filtro == "Todas as Disciplinas":
            questoes_exibidas = list(range(1, 41))
        else:
            questoes_exibidas = list(DISCIPLINAS_MAP[disc_filtro])

        dados_tabela_gab = [
            {
                "Questão": q,
                "Disciplina": obter_disciplina(q),
                "Gabarito": gabarito_ano_atual.get(q, "A"),
            }
            for q in questoes_exibidas
        ]

        df_gab_editor = pd.DataFrame(dados_tabela_gab)

        df_gab_modificado = st.data_editor(
            df_gab_editor,
            column_config={
                "Questão": st.column_config.NumberColumn("Questão", disabled=True),
                "Disciplina": st.column_config.TextColumn("Disciplina", disabled=True),
                "Gabarito": st.column_config.SelectboxColumn(
                    "Resposta Correta",
                    options=["A", "B", "C", "D", "E"],
                    required=True,
                ),
            },
            hide_index=True,
            height=450,
            use_container_width=True,
        )

        if st.button("💾 Salvar Alterações na Tabela", type="primary"):
            for _, row_g in df_gab_modificado.iterrows():
                q_num = int(row_g["Questão"])
                g_val = str(row_g["Gabarito"])
                st.session_state["gabaritos_oficiais"][ano_gab_sel][q_num] = g_val

            salvar_gabaritos_em_disco(st.session_state["gabaritos_oficiais"])
            st.success(f"Gabarito do {ano_gab_sel} salvo permanentemente no disco!")

# ---------------------------------------------------------
# ABA 3: GERENCIAR ESTUDANTES POR TURMA
# ---------------------------------------------------------
with tab_estudantes:
    st.header("Lista de Estudantes Cadastrados por Turma")

    turmas_map = st.session_state["dados_turmas"]
    t_sel = st.selectbox("Visualizar Turma:", list(turmas_map.keys()), key="sel_turma_view")

    alunos_t = turmas_map.get(t_sel, [])
    if alunos_t:
        df_alunos_view = pd.DataFrame(alunos_t)
        df_alunos_view.columns = ["Número", "Matrícula", "Nome do Estudante"]
        st.dataframe(df_alunos_view, use_container_width=True, height=450)
        st.caption(f"Total de {len(alunos_t)} estudantes matriculados na turma {t_sel}.")
    else:
        st.info("Nenhum estudante cadastrado nesta turma.")

    st.divider()
    st.subheader("📤 Importar Nova Lista de Alunos (TXT ou CSV)")
    arquivo_alunos_up = st.file_uploader(
        "Upload da planilha de alunos (Colunas: Turma, Número, Matrícula, Nome)",
        type=["txt", "csv"],
    )
    if arquivo_alunos_up:
        try:
            df_novos = pd.read_csv(arquivo_alunos_up)
            if "Turma" in df_novos.columns and "Nome" in df_novos.columns:
                novas_turmas = {}
                for turma_k, group_k in df_novos.groupby("Turma", sort=False):
                    alunos_k = []
                    for _, r in group_k.iterrows():
                        num_k = str(int(r["Número"])) if "Número" in r and pd.notna(r["Número"]) and str(r["Número"]).strip() != "" else ""
                        mat_k = str(int(r["Matrícula"])) if "Matrícula" in r and pd.notna(r["Matrícula"]) and str(r["Matrícula"]).strip() != "" else ""
                        nome_k = str(r["Nome"]).strip()
                        alunos_k.append({"numero": num_k, "matricula": mat_k, "nome": nome_k})
                    novas_turmas[str(turma_k).strip()] = alunos_k

                st.session_state["dados_turmas"] = novas_turmas
                st.success("Lista de estudantes atualizada com sucesso!")
                st.rerun()
            else:
                st.error("O arquivo deve conter pelo menos as colunas 'Turma' e 'Nome'.")
        except Exception as err:
            st.error(f"Erro ao importar arquivo: {err}")

# ---------------------------------------------------------
# ABA 4: RESULTADOS DA TURMA
# ---------------------------------------------------------
with tab_relatorio:
    st.header("Relatório Geral das Correções")

    if len(st.session_state["historico"]) == 0:
        st.info("Nenhum cartão foi corrigido e salvo ainda.")
    else:
        df_hist = pd.DataFrame(st.session_state["historico"])
        st.dataframe(df_hist, use_container_width=True)

        csv = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar Planilha de Notas (CSV)",
            data=csv,
            file_name="resultados_simulado_trimestral.csv",
            mime="text/csv",
        )

        if st.button("🗑️ Limpar Histórico"):
            st.session_state["historico"] = []
            salvar_historico_em_disco([])
            st.rerun()