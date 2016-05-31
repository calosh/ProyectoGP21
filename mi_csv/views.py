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
    #print cadena
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


def index(request):
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