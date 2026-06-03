from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "sigfe_2026"

FACTURAS_FILE = "data/facturas.json"
USUARIOS_FILE = "data/usuarios.json"

IVA = 0.19
DESCUENTO = 0.01


# =========================
# UTILIDADES
# =========================

def cargar_facturas():
    if not os.path.exists(FACTURAS_FILE):
        return []

    try:
        with open(FACTURAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def guardar_facturas(facturas):
    with open(FACTURAS_FILE, "w", encoding="utf-8") as f:
        json.dump(facturas, f, indent=4, ensure_ascii=False)


def cargar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        return []

    try:
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)


# =========================
# INICIO
# =========================

@app.route("/")
def inicio():
    return render_template("index.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        cedula = request.form["cedula"]
        clave = request.form["clave"]

        usuarios = cargar_usuarios()

        for usuario in usuarios:

            if usuario["cedula"] == cedula and usuario["clave"] == clave:

                session["cedula"] = usuario["cedula"]

                return redirect(url_for("dashboard"))

        return redirect(url_for("registro"))

    return render_template("login.html")


# =========================
# REGISTRO
# =========================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nuevo_usuario = {
            "cedula": request.form["cedula"],
            "nombre": request.form["nombre"],
            "apellido": request.form["apellido"],
            "telefono": request.form["telefono"],
            "correo": request.form["correo"],
            "clave": request.form["clave"]
        }

        usuarios = cargar_usuarios()
        usuarios.append(nuevo_usuario)

        guardar_usuarios(usuarios)

        return redirect(url_for("login"))

    return render_template("registro.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "cedula" not in session:
        return redirect(url_for("login"))

    facturas = [
        f for f in cargar_facturas()
        if f.get("cedula") == session["cedula"]
    ]

    total_facturas = len(facturas)

    total_gastado = sum(float(f["total_final"]) for f in facturas)
    total_descuento = sum(float(f["descuento"]) for f in facturas)

    conteo_tiendas = {}

    for factura in facturas:
        tienda = factura["tienda"]
        conteo_tiendas[tienda] = conteo_tiendas.get(tienda, 0) + 1

    tienda_favorita = max(conteo_tiendas, key=conteo_tiendas.get) if conteo_tiendas else "-"

    promedio = total_gastado / total_facturas if total_facturas > 0 else 0

    return render_template(
        "dashboard.html",
        total_facturas=total_facturas,
        total_gastado=round(total_gastado, 2),
        total_descuento=round(total_descuento, 2),
        tienda_favorita=tienda_favorita,
        promedio=round(promedio, 2)
    )

# =========================
# REGISTRAR FACTURA
# =========================

@app.route("/factura", methods=["GET", "POST"])
def factura():

    if request.method == "POST":

        numero = request.form["numero"]
        tienda = request.form["tienda"]
        total = float(request.form["total"])

        base = total / (1 + IVA)
        iva = total - base
        descuento = total * DESCUENTO
        total_final = total - descuento

        nueva_factura = {
            "cedula": session["cedula"],
            "numero": numero,
            "tienda": tienda,
            "total": total,
            "base": round(base, 2),
            "iva": round(iva, 2),
            "descuento": round(descuento, 2),
            "total_final": round(total_final, 2),
            "favorita": False
        }

        facturas = cargar_facturas()
        facturas.append(nueva_factura)

        guardar_facturas(facturas)

        return redirect(url_for("facturas"))

    return render_template("factura.html")


# =========================
# FACTURAS
# =========================

@app.route("/facturas")
def facturas():

    if "cedula" not in session:
        return redirect(url_for("login"))

    buscar = request.args.get("buscar", "")

    lista = [
        f for f in cargar_facturas()
        if f.get("cedula") == session["cedula"]
    ]

    if buscar:

        lista = [
            f for f in lista
            if buscar in str(f["numero"])
        ]

    return render_template(
        "facturas.html",
        facturas=lista
    )

# =========================
# ELIMINAR FACTURA
# =========================

@app.route("/eliminar/<int:index>")
def eliminar(index):

    if "cedula" not in session:
        return redirect(url_for("login"))

    todas = cargar_facturas()

    mias = [
        f for f in todas
        if f.get("cedula") == session["cedula"]
    ]

    if 0 <= index < len(mias):

        factura_eliminar = mias[index]

        todas.remove(factura_eliminar)

        guardar_facturas(todas)

    return redirect(url_for("facturas"))

# =========================
# FAVORITA ⭐
# =========================

@app.route("/favorita/<int:index>")
def favorita(index):

    facturas = cargar_facturas()

    if 0 <= index < len(facturas):

        actual = facturas[index].get("favorita", False)
        facturas[index]["favorita"] = not actual

        guardar_facturas(facturas)

    return redirect(url_for("facturas"))


# =========================
# PERFIL
# =========================

@app.route("/perfil")
def perfil():

    if "cedula" not in session:
        return redirect(url_for("login"))

    usuarios = cargar_usuarios()

    usuario = None

    for u in usuarios:

        if u["cedula"] == session["cedula"]:
            usuario = u
            break

    return render_template(
        "perfil.html",
        usuario=usuario
    )


# =========================
# AYUDA
# =========================

@app.route("/ayuda")
def ayuda():

    preguntas = [
        {"pregunta": "¿Cómo registro una factura?", "respuesta": "Ingresa a Registrar Factura y guarda."},
        {"pregunta": "¿Cómo elimino una factura?", "respuesta": "En Facturas presiona eliminar."},
        {"pregunta": "¿Dónde veo estadísticas?", "respuesta": "En el dashboard."}
    ]

    return render_template("ayuda.html", preguntas=preguntas)


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(FACTURAS_FILE):
        with open(FACTURAS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    if not os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    app.run(debug=True)