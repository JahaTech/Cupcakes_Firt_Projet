import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, redirect, url_for
from flask import session
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"
# Caminho do arquivo XML
USER_FILE = "users.xml"

# Inicializa o arquivo XML se não existir
if not os.path.exists(USER_FILE):
    root = ET.Element("users")
    tree = ET.ElementTree(root)
    tree.write(USER_FILE)

# Função para salvar novo usuário no XML
def save_user_to_xml(username, password, email):
    tree = ET.parse(USER_FILE)
    root = tree.getroot()

    # Verificar se o usuário já existe
    for user in root.findall("user"):
        if user.find("username").text == username:
            return False  # Usuário já existe

    # Criar novo usuário
    user = ET.Element("user")
    ET.SubElement(user, "username").text = username
    ET.SubElement(user, "password").text = password
    ET.SubElement(user, "email").text = email

    root.append(user)
    tree.write(USER_FILE)
    return True

# Função para validar login
def validate_login(username, password):
    tree = ET.parse(USER_FILE)
    root = tree.getroot()

    for user in root.findall("user"):
        if user.find("username").text == username and user.find("password").text == password:
            return True
    return False

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if validate_login(username, password):
        return redirect(url_for("home"))
    else:
        return "Usuário ou senha inválidos. Tente novamente.", 401

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        new_username = request.form.get("new_username")
        new_password = request.form.get("new_password")
        email = request.form.get("email")

        if save_user_to_xml(new_username, new_password, email):
            return redirect(url_for("login_page"))
        else:
            return "Usuário já cadastrado. Tente um nome diferente.", 400

    return render_template("register.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/product/<int:product_id>")
def product_details(product_id):
    # Simulação de produtos (você pode integrar com um banco de dados no futuro)
    products = {
        1: {"name": "Chocolate", "price": 5.00, "description": "Delicioso cupcake de chocolate."},
        2: {"name": "Morango", "price": 5.50, "description": "Cupcake fresco com sabor de morango."},
        3: {"name": "Baunilha", "price": 6.00, "description": "Clássico cupcake de baunilha."}
    }

    product = products.get(product_id)
    if product:
        return render_template("product_details.html", product=product)
    else:
        return "Produto não encontrado.", 404

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
        product_name = request.form.get("product_name")
        product_price = float(request.form.get("product_price"))
        quantity = int(request.form.get("quantity", 1))

        # Inicializa o carrinho na sessão se ele não existir
        if "cart" not in session:
            session["cart"] = []

        # Verifica se o produto já está no carrinho
        cart = session["cart"]
        for item in cart:
            if item["product_name"] == product_name:
                item["quantity"] += quantity
                break
        else:
            # Adiciona um novo produto ao carrinho
            cart.append({
                "product_name": product_name,
                "product_price": product_price,
                "quantity": quantity
            })

        session["cart"] = cart
        return redirect("/cart")

@app.route("/cart")
def view_cart():
        cart = session.get("cart", [])
        total = sum(item["product_price"] * item["quantity"] for item in cart)
        return render_template("cart.html", cart=cart, total=total)

@app.route("/remove_item/<product_name>")
def remove_item(product_name):
        cart = session.get("cart", [])
        cart = [item for item in cart if item["product_name"] != product_name]
        session["cart"] = cart
        return redirect("/cart")

@app.route("/update_quantity", methods=["POST"])
def update_quantity():
        product_name = request.form.get("product_name")
        new_quantity = int(request.form.get("quantity", 1))

        cart = session.get("cart", [])
        for item in cart:
            if item["product_name"] == product_name:
                item["quantity"] = new_quantity
                break

        session["cart"] = cart
        return redirect("/cart")

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", [])
    total = sum(item["product_price"] * item["quantity"] for item in cart)

    if request.method == "POST":
        customer_name = request.form.get("customer_name")
        address = request.form.get("address")
        email = request.form.get("email")
        phone = request.form.get("phone")
        payment_method = request.form.get("payment_method")

        order = {
            "customer_name": customer_name,
            "address": address,
            "email": email,
            "phone": phone,
            "payment_method": payment_method,
            "cart": cart,
            "total": total,
            "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_order_to_history(order)
        session.pop("cart", None)
        session["order"] = order
        return redirect("/order_confirmation")

    return render_template("checkout.html", cart=cart, total=total)

@app.route("/order_confirmation")
def order_confirmation():
    order = session.get("order", {})
    if not order:
        return redirect("/")
    return render_template("order_confirmation.html", order=order)

# Função para salvar pedidos no arquivo
def save_order_to_history(order):
    try:
        with open("order_history.json", "r") as file:
            orders = json.load(file)
    except FileNotFoundError:
        orders = []
    orders.append(order)
    with open("order_history.json", "w") as file:
        json.dump(orders, file)

# Nova rota para histórico de pedidos
@app.route("/order_history")
def order_history():
    try:
        with open("order_history.json", "r") as file:
            orders = json.load(file)
    except FileNotFoundError:
        orders = []
    return render_template("order_history.html", orders=orders)

@app.route("/profile",  methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        print("Página acessada via POST")
    return render_template("profile.html", user={})

    # Verifica se o usuário está logado
    if "username" not in session:
        return redirect("/")  # Redireciona para login se não estiver logado

    # Carrega informações do usuário do arquivo XML
    username = session["username"]
    tree = ET.parse("users.xml")
    root = tree.getroot()

    user_data = {}
    for user in root.findall("user"):
        if user.find("username").text == username:
            user_data = {
                "username": username,
                "email": user.find("email").text,
                "phone": user.find("phone").text,
                "name": user.find("name").text,
            }
            break

    return render_template("profile.html", user=user_data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")  # Redireciona para login após sair

@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    # Carregar lista de cupcakes disponíveis
    cupcakes = ["Chocolate", "Baunilha", "Morango", "Red Velvet", "Limão"]

    if request.method == "POST":
        # Receber dados do formulário
        cupcake = request.form["cupcake"]
        rating = request.form["rating"]
        comment = request.form["comment"]

        # Salvar avaliação no arquivo XML
        tree = ET.parse("reviews.xml")
        root = tree.getroot()

        review = ET.Element("review")
        ET.SubElement(review, "cupcake").text = cupcake
        ET.SubElement(review, "rating").text = rating
        ET.SubElement(review, "comment").text = comment
        ET.SubElement(review, "user").text = session.get("username", "Anônimo")

        root.append(review)
        tree.write("reviews.xml")

        return redirect("/reviews")  # Recarrega a página para mostrar as novas avaliações

    # Carregar avaliações do XML
    reviews = []
    try:
        tree = ET.parse("reviews.xml")
        root = tree.getroot()
        for review in root.findall("review"):
            reviews.append({
                "cupcake": review.find("cupcake").text,
                "rating": review.find("rating").text,
                "comment": review.find("comment").text,
                "user": review.find("user").text,
            })
    except FileNotFoundError:
        # Cria o arquivo caso não exista
        root = ET.Element("reviews")
        tree = ET.ElementTree(root)
        tree.write("reviews.xml")

    return render_template("reviews.html", cupcakes=cupcakes, reviews=reviews)


if __name__ == "__main__":
    app.run(debug=True)
