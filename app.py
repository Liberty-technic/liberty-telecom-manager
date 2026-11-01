
import os, csv, io, secrets, string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, Response, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "CHANGE-ME-before-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///liberty.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(30), default="Aucun")
    subscription_until = db.Column(db.DateTime)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    price_fcfa = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Router(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(80), default="MikroTik L009")
    host = db.Column(db.String(120), default="")

with app.app_context():
    db.create_all()

BASE = """
<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LIBERTY TELECOM MANAGER</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{background:#f3f6fb;color:#17233b}.navbar{background:#102b50}.card{border:0;border-radius:16px;box-shadow:0 5px 20px #102b5010}.btn-primary{background:#087f5b;border-color:#087f5b}.muted{color:#66758b}</style></head>
<body><nav class="navbar navbar-dark"><div class="container"><a class="navbar-brand fw-bold" href="/">LIBERTY TELECOM MANAGER</a>
{% if me %}<span class="text-white">{{me.company}} · <a class="text-white" href="/logout">Déconnexion</a></span>{% endif %}</div></nav>
<main class="container py-4">{% with messages=get_flashed_messages(with_categories=true) %}{% for c,m in messages %}<div class="alert alert-{{c}}">{{m}}</div>{% endfor %}{% endwith %}
{% if me %}<div class="d-flex flex-wrap gap-2 mb-4"><a class="btn btn-sm btn-outline-primary" href="/dashboard">Tableau de bord</a><a class="btn btn-sm btn-outline-primary" href="/tickets">Tickets</a><a class="btn btn-sm btn-outline-primary" href="/routers">Routeurs</a><a class="btn btn-sm btn-outline-primary" href="/plans">Abonnement</a><a class="btn btn-sm btn-outline-primary" href="/help">Aide MikroTik</a></div>{% endif %}
{{body|safe}}</main><footer class="container py-4 text-secondary small">© LIBERTY TELECOM MANAGER — Prototype initial</footer></body></html>
"""

def page(body, **kwargs):
    u = db.session.get(User, session.get("uid")) if session.get("uid") else None
    return render_template_string(BASE, body=render_template_string(body, me=u, **kwargs), me=u)

def login_required(fn):
    @wraps(fn)
    def wrap(*a, **k):
        if not session.get("uid"): return redirect(url_for("login"))
        return fn(*a, **k)
    return wrap

@app.route("/")
def home():
    if session.get("uid"): return redirect("/dashboard")
    return page("""<div class="row align-items-center py-5"><div class="col-lg-7"><span class="badge text-bg-success">Gestion Wi-Fi Zone</span><h1 class="display-5 fw-bold mt-3">Gérez vos Hotspots MikroTik depuis un seul espace.</h1><p class="lead muted">Créez vos tickets, suivez vos routeurs et préparez vos abonnements.</p><a class="btn btn-primary btn-lg me-2" href="/register">Créer mon compte</a><a class="btn btn-outline-secondary btn-lg" href="/login">Connexion</a></div><div class="col-lg-5"><div class="card p-4"><h4>Fonctions</h4><ul><li>Génération de tickets</li><li>Gestion de routeurs</li><li>Offres mensuelles</li><li>Configuration MikroTik guidée</li></ul></div></div></div>""")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        company=request.form.get("company","").strip(); email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        if not company or not email or len(password)<8: flash("Complétez les champs. Mot de passe : 8 caractères minimum.","danger")
        elif User.query.filter_by(email=email).first(): flash("Adresse e-mail déjà utilisée.","danger")
        else:
            u=User(company=company,email=email,password_hash=generate_password_hash(password)); db.session.add(u); db.session.commit(); session["uid"]=u.id; return redirect("/plans")
    return page("""<div class="row justify-content-center"><div class="col-md-6"><div class="card p-4"><h2>Créer un compte</h2><form method="post"><label>Entreprise / Wi-Fi Zone</label><input class="form-control mb-3" name="company" required><label>E-mail</label><input class="form-control mb-3" name="email" type="email" required><label>Mot de passe (8 caractères minimum)</label><input class="form-control mb-3" name="password" type="password" minlength="8" required><button class="btn btn-primary w-100">Créer mon espace</button></form></div></div></div>""")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=User.query.filter_by(email=request.form.get("email","").lower().strip()).first()
        if u and check_password_hash(u.password_hash,request.form.get("password","")): session.clear(); session["uid"]=u.id; return redirect("/dashboard")
        flash("Identifiants incorrects.","danger")
    return page("""<div class="row justify-content-center"><div class="col-md-5"><div class="card p-4"><h2>Connexion</h2><form method="post"><label>E-mail</label><input class="form-control mb-3" name="email" type="email" required><label>Mot de passe</label><input class="form-control mb-3" name="password" type="password" required><button class="btn btn-primary w-100">Se connecter</button></form></div></div></div>""")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    u=db.session.get(User,session["uid"]); count=Ticket.query.filter_by(owner_id=u.id).count(); routers=Router.query.filter_by(owner_id=u.id).count()
    return page("""<h2>Tableau de bord</h2><p class="muted">Bienvenue dans votre espace {{me.company}}.</p><div class="row g-3"><div class="col-md-4"><div class="card p-3"><div class="muted">Tickets générés</div><div class="display-6">{{count}}</div></div></div><div class="col-md-4"><div class="card p-3"><div class="muted">Routeurs</div><div class="display-6">{{routers}}</div></div></div><div class="col-md-4"><div class="card p-3"><div class="muted">Offre</div><div class="h2">{{me.plan}}</div><small>{{me.subscription_until.strftime('%d/%m/%Y') if me.subscription_until else 'Non activée'}}</small></div></div></div>""",count=count,routers=routers)

@app.route("/plans",methods=["GET","POST"])
@login_required
def plans():
    if request.method=="POST":
        name=request.form.get("plan")
        if name in ("Basic","Professionnel","Entreprise"):
            u=db.session.get(User,session["uid"]); u.plan=name; u.subscription_until=datetime.utcnow()+timedelta(days=30); db.session.commit()
            flash("Offre de démonstration activée 30 jours. Paiement réel non branché.","warning"); return redirect("/dashboard")
    return page("""<h2>Abonnements mensuels</h2><div class="row g-3">{% for n,p in [('Basic','5 000'),('Professionnel','10 000'),('Entreprise','15 000')] %}<div class="col-md-4"><div class="card p-4"><h3>{{n}}</h3><div class="display-6">{{p}} <small class="fs-6">FCFA/mois</small></div><form method="post"><input type="hidden" name="plan" value="{{n}}"><button class="btn btn-primary w-100 mt-3">Choisir</button></form></div></div>{% endfor %}</div><div class="alert alert-warning mt-3">Mode démonstration : aucun paiement Mobile Money n'est encaissé.</div>""")

@app.route("/tickets",methods=["GET","POST"])
@login_required
def tickets():
    uid=session["uid"]
    if request.method=="POST":
        try:
            qty=int(request.form["quantity"]); hours=int(request.form["duration"]); price=int(request.form["price"])
            if not 1<=qty<=1000 or hours<1 or price<0: raise ValueError()
        except Exception:
            flash("Valeurs invalides : quantité 1–1000, durée positive, prix positif ou nul.","danger"); return redirect("/tickets")
        alphabet=string.ascii_uppercase+string.digits
        for _ in range(qty):
            db.session.add(Ticket(owner_id=uid,username="".join(secrets.choice(alphabet) for _ in range(8)),password="".join(secrets.choice(string.digits) for _ in range(6)),duration_hours=hours,price_fcfa=price))
        db.session.commit(); flash(f"{qty} tickets générés.","success"); return redirect("/tickets")
    rows=Ticket.query.filter_by(owner_id=uid).order_by(Ticket.id.desc()).limit(200).all()
    return page("""<h2>Générateur de tickets</h2><div class="row g-3"><div class="col-md-4"><div class="card p-4"><form method="post"><label>Quantité (1–1000)</label><input class="form-control mb-3" name="quantity" type="number" min="1" max="1000" value="50"><label>Durée (heures)</label><input class="form-control mb-3" name="duration" type="number" min="1" value="24"><label>Prix (FCFA)</label><input class="form-control mb-3" name="price" type="number" min="0" value="350"><button class="btn btn-primary w-100">Générer</button></form></div></div><div class="col-md-8"><div class="card p-3"><a class="btn btn-outline-primary mb-3 align-self-start" href="/tickets.csv">Exporter CSV</a><div class="table-responsive"><table class="table table-sm"><tr><th>Identifiant</th><th>Mot de passe</th><th>Durée</th><th>Prix</th></tr>{% for t in rows %}<tr><td>{{t.username}}</td><td>{{t.password}}</td><td>{{t.duration_hours}} h</td><td>{{t.price_fcfa}} F</td></tr>{% else %}<tr><td colspan="4">Aucun ticket.</td></tr>{% endfor %}</table></div></div></div></div>""",rows=rows)

@app.route("/tickets.csv")
@login_required
def csv_export():
    rows=Ticket.query.filter_by(owner_id=session["uid"]).all(); out=io.StringIO(); w=csv.writer(out); w.writerow(["Identifiant","Mot de passe","Durée heures","Prix FCFA"])
    for t in rows: w.writerow([t.username,t.password,t.duration_hours,t.price_fcfa])
    return Response("\\ufeff"+out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=liberty_tickets.csv"})

@app.route("/routers",methods=["GET","POST"])
@login_required
def routers():
    uid=session["uid"]
    if request.method=="POST":
        name=request.form.get("name","").strip()
        if name:
            db.session.add(Router(owner_id=uid,name=name,model=request.form.get("model","MikroTik L009"),host=request.form.get("host",""))); db.session.commit(); flash("Routeur ajouté.","success")
        return redirect("/routers")
    rows=Router.query.filter_by(owner_id=uid).all()
    return page("""<h2>Mes routeurs MikroTik</h2><div class="row g-3"><div class="col-md-5"><div class="card p-4"><form method="post"><label>Nom du site</label><input class="form-control mb-2" name="name" required><label>Modèle</label><input class="form-control mb-2" name="model" value="MikroTik L009"><label>Adresse IP / DNS (facultatif)</label><input class="form-control mb-3" name="host"><button class="btn btn-primary">Ajouter</button></form></div></div><div class="col-md-7"><div class="card p-3">{% for r in rows %}<p>{{r.name}} — {{r.model}} — {{r.host}}</p>{% else %}<p>Aucun routeur enregistré.</p>{% endfor %}<a href="/mikrotik-script" class="btn btn-outline-primary">Télécharger le script de base (.rsc)</a></div></div></div>""",rows=rows)

@app.route("/mikrotik-script")
@login_required
def mikrotik_script():
    lines = [
"# LIBERTY TELECOM MANAGER - base HotSpot RouterOS v7",
"# Sauvegarder le routeur et adapter l'interface avant utilisation.",
"# Script illustratif : ne configure pas le WAN et ne réinitialise rien.",
"/ip pool add name=liberty-pool ranges=10.20.0.10-10.20.0.250",
"/ip address add address=10.20.0.1/24 interface=bridge comment=\"LIBERTY HOTSPOT - adapter bridge\"",
"/ip dhcp-server network add address=10.20.0.0/24 gateway=10.20.0.1 dns-server=10.20.0.1",
"/ip dns set allow-remote-requests=yes",
"/ip hotspot profile add name=liberty-profile hotspot-address=10.20.0.1 dns-name=wifi.liberty",
"/ip hotspot add name=liberty-hotspot interface=bridge address-pool=liberty-pool profile=liberty-profile disabled=no",
"/ip hotspot user profile add name=liberty-1h session-timeout=1h",
"/ip hotspot user profile add name=liberty-24h session-timeout=24h",
"# Attention : session-timeout limite une session et ne garantit pas l'expiration",
"# calendaire depuis la toute première connexion. Module avancé à développer."
]
    return Response("\\n".join(lines),mimetype="text/plain",headers={"Content-Disposition":"attachment; filename=liberty-mikrotik-base.rsc"})

@app.route("/help")
@login_required
def help_page():
    return page("""<h2>Guide MikroTik</h2><div class="card p-4"><ol><li>Faites une sauvegarde de votre routeur.</li><li>Vérifiez RouterOS v7 et le nom de l'interface LAN/bridge.</li><li>Téléchargez le fichier .rsc depuis la page Routeurs.</li><li>Adaptez l'interface et le réseau à votre installation avant import.</li><li>Faites vérifier le script par un technicien avant exécution.</li></ol><div class="alert alert-danger">N'exposez jamais l'API MikroTik directement sur Internet. Ne partagez pas le mot de passe administrateur.</div><b>Pas encore actif :</b> connexion distante automatique, paiements Mobile Money, impression PDF/thermique et expiration calendaire à la première connexion.</div>""")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
