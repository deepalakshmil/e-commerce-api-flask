from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from sqlalchemy import Column, String, ForeignKey, Table, select
from typing import List,Optional
from marshmallow import ValidationError,fields
from datetime import date



# initialize Flask App
app= Flask(__name__)

## MySQL database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:welcomesql1@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ECHO'] = True

# Creating our Base Model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class = Base)
db.init_app(app) 
ma = Marshmallow(app)


####   =============== MODELS ===================   ####

# Custormer Model

class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(primary_key= True)
    name: Mapped[str] = mapped_column(db.String(250), nullable= False)
    email: Mapped[str] = mapped_column(db.String(250),unique= True)
    address: Mapped[str] = mapped_column(db.String(300))
    
    # This relates one Customer to many Orders.
    orders: Mapped[List["Orders"]] = db.relationship(back_populates='customer')


# Association Table

order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)


#Orders Model

class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable= False)
    # A foreign key constraint is a key used to link two tables together.
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customer.id'))

     #creating a many-to-one relationship to Customer table
    customer: Mapped['Customer'] = db.relationship(back_populates='orders')

     #creating a many-to-many relationship to Products through or association table order_product
    products: Mapped[List['Products']] = db.relationship(secondary=order_product, back_populates="orders")


#Products Model

class Products(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(255), nullable=False )
    price: Mapped[float] = mapped_column(db.Float, nullable=False)

     #creating a many-to-many relationship to Orders through or association table order_product
    orders: Mapped[List['Orders']] = db.relationship(secondary=order_product, back_populates="products")


#### ======================= SCHEMAS =================== ####

#Define Customer Schema
class CustomerSchema(ma.SQLAlchemyAutoSchema): 
    class Meta:
        model = Customer

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Products

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Orders
        include_fk = True #Need this because Auto Schemas don't automatically recognize foreign keys (customer_id)


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many= True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

@app.route('/')
def home():
    return "Weclome to our E-commerce API Appliction"


#### ======================= API ROUTES --- Customer CRUD Operations ========================== ####

#Get all customers using a GET method
@app.route("/customers", methods = ['GET'])

def get_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars()  #Exectute query, and convert row objects into scalar objects (python useable)
    customers = result.all()  #packs objects into a list
    return customers_schema.jsonify(customers)


#Get Specific customer using GET method and dynamic route
@app.route("/customers/<int:id>", methods=['GET'])

def get_customer(id):
    
    query = select(Customer).where(Customer.id == id)
    result = db.session.execute(query).scalars().first() #first() grabs the first object return

    if result is None:
        return jsonify({"Error": "Customer not found"}), 404
    
    return customer_schema.jsonify(result)


#Creating customers with POST request
@app.route('/customers', methods=["POST"])
def add_customer():

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], address=customer_data['address'])
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({"Message": "New Customer added successfully",
                    "customer": customer_schema.dump(new_customer)}), 201


# Update the customers details using with PUT request
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    print("customer id", id)
    customer = db.session.get(Customer, id)
    print("customer id", id)

    if not customer:
        return jsonify({"message": "Invalid customer id"}), 400
    
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.address = customer_data['address']

    db.session.commit()
    # return customer_schema.jsonify(customer), 200

    return jsonify({"Message": "Update the Customer Details Successfully",
                   "customer": customer_schema.dump(customer)}), 200

# Delete the customer details using with DELETE request
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_user(id):
    customer = db.session.get(Customer, id)

    if not customer:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"succefully deleted customer {id}"}), 200


#=============== API ROUTES: Products CRUD Operations==================

#Creating Products with POST request
@app.route('/products', methods=['POST'])
def create_product(): 

    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Products(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"Messages": "New Product added!",
                    "product": product_schema.dump(new_product)}), 201


# Get all Products using a GET method
@app.route("/products", methods=['GET'])
def get_products():

    query = select(Products)
    result = db.session.execute(query).scalars() #Exectute query, and convert row objects into scalar objects (python useable)
    products = result.all() #packs objects into a list
    return products_schema.jsonify(products)
    

#Get Specific Products using GET method and dynamic route
@app.route("/products/<int:id>",methods= ['GET'])
def get_product(id):
    
    query = select(Products).where(Products.id == id)
    result = db.session.execute(query).scalars().first()

    if result is None:
        return jsonify({"Error" : "Product not found"}), 404
    
    return product_schema.jsonify(result)

# Update the Products details using with PUT request
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    print("customer id", id)
    product = db.session.get(Products, id)
    print("customer id", id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    try:
        product_data = product_schema.load(request.json)
        print("customer data",product_data)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()

    return jsonify({"Message": "Update the Product Details Successfully",
                   "product": product_schema.dump(product)}), 200

# Delete the customer details using with DELETE request
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Products, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"succefully deleted product {id}"}), 200

#=============== API ROUTES: Orders CRUD Operations==================

#CREATE an ORDER with POST request
@app.route('/orders', methods=['POST'])
def add_order():
    
    try:       
        order_data = order_schema.load(request.json)        
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # Retrieve the customer by its id.
    customer = db.session.get(Customer, order_data['customer_id'])
    
    # Check if the customer exists.
    if customer:
        new_order = Orders(order_date=order_data['order_date'], customer_id = order_data['customer_id'])

        db.session.add(new_order)
        db.session.commit()

        return jsonify({"Message": "New Order Placed!",
                        "order": order_schema.dump(new_order)}), 201
    else:
        return jsonify({"message": "Invalid customer id"}), 400


# Get all Products using a GET method
@app.route("/orders", methods=['GET'])
def get_orders():

    query = select(Orders)
    result = db.session.execute(query).scalars() #Exectute query, and convert row objects into scalar objects (python useable)
    orders = result.all() #packs objects into a list
    return orders_schema.jsonify(orders)
    

#Get Specific Products using GET method and dynamic route
@app.route("/orders/<int:id>",methods= ['GET'])
def get_order(id):
    
    query = select(Orders).where(Orders.id == id)
    result = db.session.execute(query).scalars().first()

    if result is None:
        return jsonify({"Error" : "Order not found"}), 404
    
    return order_schema.jsonify(result)


# Update the Order details using with PUT request
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product(order_id, product_id):
    order = db.session.get(Orders, order_id) #can use .get when querying using Primary Key
    product = db.session.get(Products, product_id)

    if order and product: #check to see if both exist
        if product not in order.products: #Ensure the product is not already on the order
            order.products.append(product) #create relationship from order to product
            db.session.commit() #commit changes to db
            return jsonify({"Message": "Successfully added item to order."}), 200
        else:#Product is in order.products
            return jsonify({"Message": "Item is already included in this order."}), 400
    else:#order or product does not exist
        return jsonify({"Message": "Invalid order id or product id."}), 400


# Delete the product from an order using with DELETE request
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def delete_order_product(order_id, product_id):
    order = db.session.get(Orders, order_id)
    product = db.session.get(Products, product_id)

    if order and product:
        if product not in order.products:
         return jsonify({"message": "Invalid product id"}), 400
        else:
            db.session.delete(product)
            db.session.commit()
            return jsonify({"message": f"succefully deleted the order id is: {order_id} and the product id is :{product_id}"}), 200
    else:
        return jsonify({"Message": "Invalid order id or product id."}), 400


# Get all Orders for a Customer using a GET method
@app.route("/orders/customer/<int:id>", methods=['GET'])
def get_customer_orders(id):

   customer=db.session.get(Customer, id) 
   return orders_schema.jsonify(customer.orders), 200 


# Get all Products for an Order using a GET method
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_product(order_id):
    order = db.session.get(Orders, order_id)
    return products_schema.jsonify(order.products), 200 


if __name__ == "__main__":

    with app.app_context():
    #  db.drop_all()
     db.create_all()
    
    app.run(debug=True)