from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
import re, json
from myapp.models import Dreamreal, Login
from myapp.forms import LoginForm, DreamrealForm
import datetime
from django.core.cache import cache
from django.shortcuts import render
from django.core.mail import send_mail
# Create your views here.

def send_email(request):
    send_mail(
        'Subject here',
        'Here is the message.',
        'eliste5638@gmail.com',
        ['eliste5638@gmail.com'],
        )
    return HttpResponse("<h1>Email Sented</h1>")

def my_view(request):
    cache_key = 'my_cache_key'
    cache_time = 1800  # 30 minutes
    data = cache.get(cache_key)
    if not data:
        data = 'This is the cached data'
        cache.set(cache_key, data, cache_time)
    return render(request, 'index.html', {'data': data})

def login_view(request):

    if request.method == "POST":
        host_account = request.POST.get("user")
        host_password = request.POST.get("password")
        
        if Login.objects.filter(username=host_account, password=host_password):
          
            res=""
            # Read a specific entry:
            sorex = Dreamreal.objects.get(name=host_account)
            res += "name: "+sorex.name+"\n"
            res += "website: "+sorex.website+"\n"
            res += "phonenumber: "+str(sorex.phonenumber)+"\n"
            res += "email: "+sorex.mail+"\n"
            
            request.session['username']= host_account
            request.session['msg']=res
            
            response =render(request, 'loggin.html', {"msg": res})
            response.set_cookie('last_connection', datetime.datetime.now())

            return response
        else:
            return render(request, 'index.html', {"data": "invalid user or password"})
    elif 'username' in request.session and 'last_connection' in request.COOKIES:
        last_connection = request.COOKIES['last_connection']
        last_connection_time = datetime.datetime.strptime(last_connection[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.datetime.now() - last_connection_time).seconds < 10:
            res = request.session['msg']
            return render(request, 'loggin.html', {"msg": res})
        
    return render(request, 'index.html')

def logout(request):
    del request.session['username']
    return render(request, 'index.html')


def validate_password(request):
    password_rule = re.compile(
        r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^A-Za-z0-9])(?=.*\d).{8,}$"
    )
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            password = data.get("password", "")
            if password_rule.match(password):
                return JsonResponse({"valid": True})
            else:
                return JsonResponse({"valid": False})
        except Exception as e:
            return JsonResponse({"valid": False, "error": str(e)})
    return JsonResponse({"valid": False, "error": "404"})


def register(request):
    Loginform = LoginForm()
    Dreamrealform = DreamrealForm()
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        website = request.POST.get("website")
        mail = request.POST.get("mail")
        phonenumber = request.POST.get("phonenumber")
        
        if Login.objects.filter(username=username):
            return render(request,"register.html",{'msg':"User already exists"})
        elif username and password :
            Dreamrealform = Dreamreal(name=username,
                                    website=website,
                                    mail=mail,
                                    phonenumber=phonenumber
                                    )
            Dreamrealform.save()
            Loginform = Login(username=username,
                                  password=password
                                  )
            Loginform.save()

            
            return render(request,"register.html",{'msg':"Register Success"})
        else:
            return render(request,"register.html",{'msg':"User or password is empty"})
    return render(request,"register.html")

def dreamreal(request):
    form = DreamrealForm()
    return render(request, 'dreamreal.html', locals())

def crudops(request):
    # Creating an entry

    dreamreal = Dreamreal(
        website="www.google.com",
        mail="alvin@google.com.com",
        name="alvin",
        phonenumber="0911222333"
    )

    dreamreal.save()

    # Read ALL entries
    objects = Dreamreal.objects.all()
    res = 'Printing all Dreamreal entries in the DB : <br>'

    for elt in objects:
        res += elt.name + "<br>"

    # Read a specific entry:
    sorex = Dreamreal.objects.get(name="alvin")
    res += 'Printing One entry <br>'
    res += sorex.name

    # Delete an entry
    res += '<br> Deleting an entry <br>'
    sorex.delete()

    #Update
    dreamreal = Dreamreal(
        website="www.google.com",
        mail="alvin@google.com.com",
        name="alvin",
        phonenumber="0911222444"
    )

    dreamreal.save()
    res += 'Updating entry<br>'

    dreamreal = Dreamreal.objects.get(name='alvin')
    dreamreal.name = 'mary'
    dreamreal.save()

    return HttpResponse(res)
