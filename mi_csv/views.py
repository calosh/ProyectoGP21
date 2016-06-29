# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from django.shortcuts import render
# Create your views here.

from django.http import HttpResponse
from django.core.files import File

import urllib
import urllib2
import csv
import codecs
import re

import json
#import simplejson as json

from bs4 import BeautifulSoup
from urllib import urlopen

from nltk.tokenize import TweetTokenizer
from diccionario import palabras

tknzr = TweetTokenizer()
def reemplazarAbbrPorPalabra(text):
    tokens = tknzr.tokenize(text)
    for i in palabras:
        for j in palabras[i]:
            #print j
            aux = " "+j
            aux2 = j+" "
            if j in tokens:
                text = text.replace(j,i)
                break
    return text

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
    cadena = cadena.replace("\n", " ")
    cadena = cadena.replace("-", " ")
    return cadena

def eliminarUltimoHastag(text):
    try:
        i = len(text)-1
        j=0
        cadena = ""
        lista = []
        while j<=i and text[i]!=" ":
            lista.append(text[i])
            i-=1
        cadena = cadena.join(lista)
        if cadena[-1]=="#":
            return 1
        else:
            return 0
    except IndexError:
        print "IndexError "
        return 1
    except Exception:
        print "Otro Error Desconocido"
        return 1

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
    text = reemplazarAbbrPorPalabra(text)
    # http://stackoverflow.com/questions/10982240/how-can-i-remove-duplicate-letters-in-strings
    # text = re.sub(r'(\w)\1+', r'\1', text) # NOrmalizar Palabras gooool-->gol
    
    # http://stackoverflow.com/questions/16453522/how-can-i-detect-laughing-words-in-a-string/16453690#16453690
    # Normalizar risas jajajaj o ejejej --> jaja
    return re.sub(r'\b(?:(a|e|i|o|u)*(?:ja|je|ji|jo|ju)+j?|(?:j+(a|e|i|o|u)+)+j+)\b','jaja',text, flags=re.I)

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
            try:
                twett= twett.join(i[6])
                twett = normalizar_palabras(twett)
            except IndexError, e:
                continue
            
            usuario = ""
            try:
                usuario= usuario.join(i[18])
            except IndexError:
                usuario = "S/U"

            nombre = ""
            try:
                nombre = nombre.join(i[31])
            except IndexError:
                nombre = "S/N"
              
            try:
                datosjson = ""
                datosjson= datosjson.join(i[32])
                datosjson = json.loads(datosjson)
                entities = datosjson['entities']
                id_tweet = i[0]
                favorite_count = datosjson['favorite_count']
            except Exception:
                id_tweet = i[0]
                favorite_count= 0

            retweet_count=0
            try:
                retweet_count = i[11]
            except IndexError:
                retweet_count = 0

            # Si no existe twett
            if len(twett)<5:
                # twett vacio, fijamos twett = "via @" para terminar el proceso
                twett = "vía @"

            # Si RT o via @ o # esta al principio se elimina el twett Vía Gcgisela
            if "RT" in twett[0:3] or "via @" in twett or "vía @" in twett or "Vía @" in twett or twett[0]=="#" or eliminarUltimoHastag(twett)==1:
                pass
            else:
                # Eliminio emoticons
                #twett = eliminar_emoticons(twett)
                # Si el twett tiene http y el campo de la base de datos url es diferente de vacio
                if "http" in twett and i[24]!="":
                    #response = urllib2.urlopen(i[24])
                    #html = response.read()
                    url = i[24]
                    # http://stackoverflow.com/questions/22004093/python-beautifulsoup-picking-webpages-same-codes-working-on-and-off
                    soup = BeautifulSoup(urlopen(url),"html.parser")
                    title = soup.find('title')
                    body = soup.find('body')

                    # Elimino la url del tweet
                    twett=eliminar_urls(twett)
                    twett=eliminarMenciones(twett)
                    # Si se encuentra una coincidencia del twett con el contenido de la url
                    busqueda_tweet = body.find(twett)
                    busqueda_tweet2 = title.find(twett)
                    if busqueda_tweet!=-1 or busqueda_tweet2!=-1:
                        pass
                    else:
                        cont=cont+1;
                        #twett=normalizar_risas(twett)
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

                        busqueda_tweet = body.find(twett)
                        busqueda_tweet2 = title.find(twett)
                        if busqueda_tweet!=-1 or busqueda_tweet2!=-1:
                            pass
                        else:
                            cont=cont+1;
                            print "%d %s" %(cont, twett)
                            #twett=normalizar_risas(twett)
                            writer.writerow([id_tweet,twett,usuario, favorite_count, retweet_count, nombre.encode('utf8')])
                    # Si no se encuentra la url en el twett
                    except Exception:
                        twett=eliminar_urls(twett)
                        twett=eliminarMenciones(twett)
                        cont=cont+1;
                        print "%d %s" %(cont, twett)
                        #twett=normalizar_risas(twett)
                        writer.writerow([id_tweet,twett,usuario, favorite_count, retweet_count, nombre.encode('utf8')])

                else:
                    # Se imprimer el twett
                    twett=eliminar_urls(twett)
                    twett=eliminarMenciones(twett)
                    cont=cont+1;
                    print "%d %s" %(cont, twett)
                    #twett=normalizar_risas(twett)
                    writer.writerow([id_tweet,twett,usuario, favorite_count, retweet_count, nombre.encode('utf8')])
        return res

    return render(request, "index.html", locals())

def opener(s):
    params = {}
    params['input']=s
    params['kaf']='true'
    params = urllib.urlencode(params)
    f = urllib.urlopen("http://localhost:9293/", params)

    # pos-tagger
    s = f.read()
    params = {}
    params['input']=s
    params['kaf']='true'
    params = urllib.urlencode(params)
    f = urllib.urlopen("http://localhost:9294/", params)

    # polarity-tagger
    s = f.read()
    params = {}
    params['input']=s
    params['kaf']='true'
    params = urllib.urlencode(params)
    f = urllib.urlopen("http://localhost:9295/", params)

    # opinion-detector-basic
    s = f.read()
    params = {}
    params['input']=s
    params['kaf']='true'
    params = urllib.urlencode(params)
    f = urllib.urlopen("http://localhost:9296/", params)

    # kaf2json
    s = f.read()
    params = {}
    params['input']=s
    params['kaf']='true'
    params = urllib.urlencode(params)
    f = urllib.urlopen("http://localhost:9297/", params)

    lista_opener = f.read()
    lista=json.loads(lista_opener)
    #print lista['opinions']
    #print lista['sentiments']
    return lista


def index_sentiwordnet(request):
    res = HttpResponse(content_type='text/csv')
    res['Content-Disposition'] = 'attachment; filename=listado.csv'
    writer = csv.writer(res)
    #writer.writerow(['id','Tweets','Usuario','Numero Favoritos','Numero Retweets','Nombre'])
    # 'POS','ROOT','Positivity score','Negativity score','Objectivity score'
    writer.writerow(['Tweet Original','Polaridad'])

    if request.POST and request.FILES:
        #http://www.thuydienthacba.com/questions/4576059/getting-type-error-while-opening-an-uploaded-csv-file
        csvfile = request.FILES['csv_file'].open()  # http://stackoverflow.com/questions/10617286/getting-type-error-while-opening-an-uploaded-csv-file
        #portfolio = csv.DictReader(paramFile)
        portfolio = csv.DictReader(request.FILES['csv_file'].file)

        #print(gs.translate('hello world', 'de'))
        for i in portfolio:
            twett = ""
            twett= twett.join(i['Tweets'])
            #translation = translator.translate(twett)
            print twett

            s = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <KAF xml:lang="es" version="2.1">
                  <raw>"""+twett+"""</raw>
                </KAF>"""

            lista_opener = opener(s)
            polaridad = ""
            try:
                print lista_opener['sentiments']
                polaridad = json.dumps(lista_opener['sentiments']).decode('utf-8')
            except KeyError:
                polaridad = ""
            
            #polaridad = lista_opener['sentiments']
            #print polaridad['polarity']
            writer.writerow([twett.encode('utf-8'),polaridad])
        return res

    return render(request, "index2.html", locals())