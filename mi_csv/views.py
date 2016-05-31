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


def index(request):
    res = HttpResponse(content_type='text/csv')
    res['Content-Disposition'] = 'attachment; filename=listado.csv'
    writer = csv.writer(res)
    writer.writerow(['id','Tweets','Usuario','Numero Favoritos','Numero Retweets','Nombre'])

    if request.POST and request.FILES:

        csvfile = request.FILES['csv_file']
        dialect = csv.Sniffer().sniff(codecs.EncodedFile(csvfile, "utf-8").read(1024))
        csvfile.open()
        reader = csv.reader(codecs.EncodedFile(csvfile, "utf-8"), delimiter=',', dialect=dialect)
        rows = list(reader)
        #print rows[0]
        cont = 0
        for i in rows:
            twett = ""
            twett= twett.join(i[6])
            usuario = ""
            usuario= usuario.join(i[15])
            nombre = ""
            try:
                datosjson = ""
                datosjson= datosjson.join(i[32])
                datosjson = json.loads(datosjson)
                entities = datosjson['entities']
                user_mentions = entities['user_mentions']
                id_tweet = datosjson['id']
                favorite_count = datosjson['favorite_count']
                retweet_count = datosjson['retweet_count']
                aux= user_mentions[0]
                nombre = aux['name']
            except IndexError:
                # Algunos campos del json no tienen informacion
                nombre = "S/N"
            except Exception:
                id_tweet = 0
                favorite_count= 0
                retweet_count = 0


            # Si RT o via @ o # esta al principio se elimina el twett
            if "RT" in twett[0:3] or "via @" in twett or twett[0]=="#":
                pass
            else:
                # Eliminio emoticons
                twett = eliminar_emoticons(twett)
                # Si el twett tiene http y el campo de la base de datos url es diferente de vacio
                if "http" in twett and i[24]!="":
                    response = urllib2.urlopen(i[24])
                    html = response.read()
                    # Si se encuentra una coincidencia del twett con el contenido de la url
                    if twett[3:20] in html:
                        pass
                    else:
                        # Elimino la url del tweet
                        twett=eliminarMenciones(twett)
                        twett=eliminar_urls(twett)
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

                        response = urllib2.urlopen(url)
                        html = response.read()

                        if twett[3:20] in html:
                            pass
                        else:
                            # Elimino la url del tweet
                            twett=eliminar_urls(twett)
                            twett=eliminarMenciones(twett)
                            cont=cont+1;
                            print "%d %s" %(cont, twett)
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