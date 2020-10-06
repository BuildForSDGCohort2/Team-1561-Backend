from flask import request, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, RadioField, FloatField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_wtf.file import FileField, FileAllowed
from flask_babel import _, lazy_gettext as _l
from app.models import User, Cart, Product, Category, ProductCategory


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class addProductForm(FlaskForm):
    category = SelectField('Category:', coerce=int, id='select_category')
    sku = IntegerField('Product SKU:', validators=[DataRequired()])
    productName = StringField('Product Name:', validators=[DataRequired()])
    productDescription = TextAreaField('Product Description:', validators=[DataRequired()])
    productPrice = FloatField('Product Price:', validators=[DataRequired()])
    productQuantity = IntegerField('Product Quantity:', validators=[DataRequired()])
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')


def getAllProducts():
    itemData = Product.query.join(ProductCategory, Product.productid == ProductCategory.productid) \
        .add_columns(Product.productid, Product.product_name, Product.discounted_price, Product.description,
                     Product.image, Product.quantity) \
        .join(Category, Category.categoryid == ProductCategory.categoryid) \
        .order_by(Category.categoryid.desc()) \
        .all()
    return itemData


def getCategoryDetails():
    itemData = Category.query.join(ProductCategory, Category.categoryid == ProductCategory.categoryid) \
        .join(Product, Product.productid == ProductCategory.productid) \
        .order_by(Category.categoryid.desc()) \
        .distinct(Category.categoryid) \
        .all()
    return itemData

class addCategoryForm(FlaskForm):
    category_name = StringField('Category Name', validators=[DataRequired()])
    submit = SubmitField('Save')

def getusercartdetails():
    userId = User.query.with_entities(User.userid).filter(User.email == session['email']).first()

    productsincart = Product.query.join(Cart, Product.productid == Cart.productid) \
        .add_columns(Product.productid, Product.product_name, Product.discounted_price, Cart.quantity, Product.image) \
        .add_columns(Product.discounted_price * Cart.quantity).filter(
        Cart.userid == userId)
    totalsum = 0

    for row in productsincart:
        totalsum += row[6]

    tax = ("%.2f" % (.06 * float(totalsum)))

    totalsum = float("%.2f" % (1.06 * float(totalsum)))
    return (productsincart, totalsum, tax)


def getLoginUserDetails():
    productCountinCartForGivenUser = 0

    
    #userid, firstName = User.query.with_entities(User.id, User.username).filter(
           # User.email == session['email']).first()

    productCountinCart = []

        # for Cart in Cart.query.filter(Cart.userId == userId).distinct(Products.productId):
    for cart in Cart.query.filter(Cart.userid == User.id).all():
        productCountinCart.append(cart.productid)
        productCountinCartForGivenUser = len(productCountinCart)

    return (productCountinCartForGivenUser)

def massageItemData(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(6):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans
