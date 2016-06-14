# -*- coding: utf-8 -*-
from django.shortcuts import render
# Create your views here.

from django.http import HttpResponse
from django.core.files import File

import urllib2
import csv
import codecs
import re

import json
from bs4 import BeautifulSoup
from urllib import urlopen

#from translate import Translator
from textblob import TextBlob


import nltk
from nltk.wsd import lesk
from nltk.corpus import wordnet as wn
from nltk.corpus import sentiwordnet as swn
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import TweetTokenizer



def eliminarMenciones(cadena):
    bandera = True
    while(bandera):
        posicion = cadena.find("@")
        if posicion!=-1:
            cad = cadena[posicion]+cadena[posicion+1]
            may = cadena[posicion+1]
            may = may.capitalize()

            cadena = cadena.replace(cad,may)
        else:
            bandera=False
    cadena = cadena.replace("#", "")
    cadena = cadena.replace("\n", "")
    return cadena

def eliminar_emoticons(text):
    # http://stackoverflow.com/questions/26568722/remove-unicode-emoji-using-re-in-python
    try:
        # Wide UCS-4 build
        emoji_pattern = re.compile(u'['
            u'\U0001F300-\U0001F64F'
            u'\U0001F680-\U0001F6FF'
            u'\u2600-\u26FF\u2700-\u27BF]+', 
            re.UNICODE)
    except re.error:
        # Narrow UCS-2 build
        emoji_pattern = re.compile(u'('
            u'\ud83c[\udf00-\udfff]|'
            u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
            u'[\u2600-\u26FF\u2700-\u27BF])+', 
            re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    return text

def eliminar_urls(text):
    url_patron = re.compile("(?P<url>https?://[^\s]+)")
    text = re.sub(url_patron, '', text)
    return text

def normalizar_palabras(text):
    # http://stackoverflow.com/questions/10982240/how-can-i-remove-duplicate-letters-in-strings
    return re.sub(r'(\w)\1+', r'\1', text)

def normalizar_risas(text):
    texto = normalizar_palabras(text)
    return re.sub(r'(j[aeiou]|j)+','jaja', texto, flags=re.I)


def url_lista(request):
    return render(request, "lista.html")


def index_normalizacion(request):
    res = HttpResponse(content_type='text/csv')
    res['Content-Disposition'] = 'attachment; filename=listado.csv'
    writer = csv.writer(res)
    writer.writerow(['id','Tweets','Usuario','Numero Favoritos','Numero Retweets','Nombre'])

    if request.POST and request.FILES:

        csvfile = request.FILES['csv_file']
        dialect = csv.Sniffer().sniff(codecs.EncodedFile(csvfile, "utf-8").read(1024))
        csvfile.open()
        # https://docs.python.org/3/library/csv.html#csv.reader
        # https://slaptijack.com/programming/python-csv-error-on-new-line-character-in-unquoted-field/
        reader = csv.reader(codecs.EncodedFile(csvfile, "utf-8"), delimiter=',', dialect=dialect)
        rows = list(reader)
        #print rows
        cont = 0
        for i in rows:
            twett = ""
            twett= twett.join(i[6])
            twett = normalizar_risas(twett)
            usuario = ""
            usuario= usuario.join(i[18])
            nombre = ""
            nombre = nombre.join(i[31])
            retweet_count=0
            try:
                datosjson = ""
                datosjson= datosjson.join(i[32])
                datosjson = json.loads(datosjson)
                entities = datosjson['entities']
                id_tweet = i[0]
                favorite_count = datosjson['favorite_count']
                retweet_count = i[11]
            except Exception:
                id_tweet = i[0]
                retweet_count = i[11]
                favorite_count= 0

            # Si RT o via @ o # esta al principio se elimina el twett
            if "RT" in twett[0:3] or "via @" in twett or twett[0]=="#":
                pass
            else:
                # Eliminio emoticons
                twett = eliminar_emoticons(twett)
                # Si el twett tiene http y el campo de la base de datos url es diferente de vacio
                if "http" in twett and i[24]!="":
                    #response = urllib2.urlopen(i[24])
                    #html = response.read()
                    url = i[24]
                    # http://stackoverflow.com/questions/22004093/python-beautifulsoup-picking-webpages-same-codes-working-on-and-off
                    soup = BeautifulSoup(urlopen(url),"html.parser")
                    body = soup.find('body')
                    # Elimino la url del tweet
                    twett=eliminarMenciones(twett)
                    twett=eliminar_urls(twett)
                    # Si se encuentra una coincidencia del twett con el contenido de la url
                    if twett in body:
                        pass
                    else:
                        cont=cont+1;
                        print "%d %s" %(cont, twett)
                        # Se impimer el twett
                        writer.writerow([id_tweet,twett,usuario, favorite_count, retweet_count, nombre.encode('utf8')])
                        
                # Si hay una url en el twett pero no en la base de datos
                elif "http" in twett:
                    # Buscamos la url en el twett
                    try:
                        url = re.search("(?P<url>https?://[^\s]+)", twett).group("url")
                        # Si se encuentra ' en una url la elimina
                        if "'" in url:
                            url = url.replace("'","")

                        #response = urllib2.urlopen(url)
                        #html = response.read()
                        soup = BeautifulSoup(urlopen(url),"html.parser")
                        body = soup.find('body')
                        # Elimino la url del tweet
                        twett=eliminar_urls(twett)
                        twett=eliminarMenciones(twett)
                        cont=cont+1;
                        print "%d %s" %(cont, twett)

                        if twett in body:
                            pass
                        else:
                            writer.writerow([id_tweet,twett,usuario, favorite_count, retweet_count, nombre.encode('utf8')])
                    # Si no se encuentra la url en el twett
                    except Exception:
                        twett=eliminar_urls(twett)
                        twett=eliminarMenciones(twett)
                        cont=cont+1;
                        print "%d %s" %(cont, twett)
                        writer.writerow([id_tweet,twett,usuario, favorite_count, retweet_count, nombre.encode('utf8')])

                else:
                    # Se imprimer el twett
                    twett=eliminar_urls(twett)
                    twett=eliminarMenciones(twett)
                    cont=cont+1;
                    print "%d %s" %(cont, twett)
                    writer.writerow([id_tweet,twett,usuario, favorite_count, retweet_count, nombre.encode('utf8')])
        return res

    return render(request, "index.html", locals())


def index_sentiwordnet(request):
    res = HttpResponse(content_type='text/csv')
    res['Content-Disposition'] = 'attachment; filename=listado.csv'
    writer = csv.writer(res)
    #writer.writerow(['id','Tweets','Usuario','Numero Favoritos','Numero Retweets','Nombre'])
    # 'POS','ROOT','Positivity score','Negativity score','Objectivity score'
    writer.writerow(['Tweet Original','Tweet Traducido','POS','ROOT','Positivity Score','Negativity Score','Objectivity Score'])

    if request.POST and request.FILES:
        #http://www.thuydienthacba.com/questions/4576059/getting-type-error-while-opening-an-uploaded-csv-file
        csvfile = request.FILES['csv_file'].open()  # http://stackoverflow.com/questions/10617286/getting-type-error-while-opening-an-uploaded-csv-file
        #portfolio = csv.DictReader(paramFile)
        portfolio = csv.DictReader(request.FILES['csv_file'].file)

        #print(gs.translate('hello world', 'de'))
        for i in portfolio:
            twett = ""
            twett= twett.join(i['Tweets']).decode('utf8')
            #translation = translator.translate(twett)
            print twett

            b = TextBlob(twett)
            traduccion = ""
            traduccion = traduccion.join(b.translate(to="en"))
            tokens = nltk.word_tokenize(traduccion)
            print traduccion
            print type(traduccion)
            tagged = nltk.pos_tag(tokens)
            #print tagged

            stemmer = SnowballStemmer("english")
            # Tokenizar
            tknzr = TweetTokenizer()
            text_token = tknzr.tokenize(traduccion)
            text_token2 = []

            # Raiz de cada palabra en text_token2
            for i in text_token:
                aux = stemmer.stem(i)
                text_token2.append(aux)

            print text_token2
            print tokens

            cont = 0
            pos_score = 0
            neg_score = 0
            obj_score = 0
            for i in text_token2:
                # si la raiz existe en el diccionario
                n = (lesk(text_token2, i, 'n'))
                if n:
                    x = n.name()
                    #print wn.synset(x).definition()
                    breakdown = swn.senti_synset(x)
                    pos_score = pos_score + breakdown.pos_score()
                    neg_score = neg_score + breakdown.neg_score()
                    obj_score = obj_score + breakdown.obj_score()
                    cont = cont+1
                elif n==None:
                    # Buscanos la palabra original en el diccionario
                    try:
                        n = (lesk(text_token2, text_token[cont], 'n'))
                        x = n.name()
                        breakdown = swn.senti_synset(x)
                        pos_score = pos_score + breakdown.pos_score()
                        neg_score = neg_score + breakdown.neg_score()
                        obj_score = obj_score + breakdown.obj_score()

                        cont = cont + 1
                    except AttributeError:
                        cont = cont + 1
                else:
                    # La palabara no existe en el diccionario
                    cont = cont + 1

            print "La positividad es: %f" %pos_score
            print "La negatividad es: %f" %neg_score
            print "La objetividad es: %f" %obj_score
            # ,json.dumps(tagged),json.dumps(text_token2),pos_score,neg_score,obj_score
            writer.writerow([twett.encode('utf-8'),traduccion.encode('utf-8'), json.dumps(tagged),json.dumps(text_token2),pos_score,neg_score,obj_score])
        return res

    return render(request, "index2.html", locals())