from datetime import datetime
from flask import render_template, flash, redirect, url_for, abort, request, \
    jsonify, current_app, send_from_directory
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
from werkzeug.utils import secure_filename
from app.main.forms import *
from app.models import User, Post, Product, Category, ProductCategory
from app.main import bp
import secrets, os,imghdr





@bp.route('/')
@bp.route('/index')
def index():
    itemData = Product.query.join(ProductCategory, Product.productid == ProductCategory.productid) \
        .add_columns(Product.productid, Product.product_name,Product.regular_price, Product.discounted_price, Product.description,
                     Product.image, Product.quantity) \
        .join(Category, Category.categoryid == ProductCategory.categoryid) \
        .order_by(Category.categoryid.desc()) \
        .all()

    productCountinKartForGivenUser = getLoginUserDetails()
    allProductDetails = getAllProducts()
    allProductsMassagedDetails = massageItemData(allProductDetails)
    categoryData = getCategoryDetails()
    files = os.listdir(current_app.config['UPLOAD_PATH'])
    return render_template('index.html', title=_('Home'), files=files, itemData=itemData, itemDat=allProductsMassagedDetails, 
                           productCountinKartForGivenUser=productCountinKartForGivenUser,
                           categoryData=categoryData)


@bp.route('/dashboard')
@login_required
def explore():
    
        
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('dashboard.html', title=_('Dashboard'), 
                           posts=posts, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)

@bp.route('/product/new', methods=['GET', 'POST'])
def addProduct():
    form = addProductForm()
    form.category.choices = [(row.categoryid, row.category_name) for row in Category.query.all()]
    #product_icon = "" #safer way in case the image is not included in the form
    if form.validate_on_submit():
        uploaded_file = request.files['image']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
                abort(400)
        uploaded_file.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))
        product = Product(sku=form.sku.data, product_name=form.productName.data, description=form.productDescription.data, image=filename, quantity=form.productQuantity.data, discounted_price=15, product_rating=0, product_review=" ", regular_price=form.productPrice.data)

        db.session.add(product)
        db.session.commit()
        product_category = ProductCategory(categoryid=form.category.data, productid=product.productid)
        db.session.add(product_category)
        db.session.commit()
        flash(_('Product is now live!'))
        return redirect(url_for('main.explore'))
    return render_template('addProduct.html', title=_('Add Product'),
                           form=form)

@bp.route('/cart')
def cart():
    loggedIn, firstName, productCountinKartForGivenUser = getLoginUserDetails()
    cartdetails, totalsum, tax = getusercartdetails();
    return render_template("cart.html", cartData=cartdetails,
                               productCountinKartForGivenUser=productCountinKartForGivenUser, loggedIn=loggedIn,
                               firstName=firstName, totalsum=totalsum, tax=tax)


@bp.route('/category/new', methods=['GET', 'POST'])
def addCategory():
    form = addCategoryForm()
    if form.validate_on_submit():
        category = Category(category_name=form.category_name.data)
        db.session.add(category)
        db.session.commit()
        flash(_('Category, added successfully.'))
        return redirect(url_for('main.addCategory'))
    return render_template("addCategory.html", form=form)

@bp.route('/displayCategory')
def displayCategory():
    loggedIn, firstName, noOfItems = getLoginUserDetails()
    categoryId = request.args.get("categoryId")

    productDetailsByCategoryId = Product.query.join(ProductCategory, Product.productid == ProductCategory.productid) \
        .add_columns(Product.productid, Product.product_name, Product.regular_price, Product.discounted_price,
                     Product.image) \
        .join(Category, Category.categoryid == ProductCategory.categoryid) \
        .filter(Category.categoryid == int(categoryId)) \
        .add_columns(Category.category_name) \
        .all()

    categoryName = productDetailsByCategoryId[0].category_name
    data = massageItemData(productDetailsByCategoryId)
    return render_template('displayCategory.html', data=data, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryName=categoryName)
   


def upload_files():
    uploaded_file = request.files['image']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            abort(400)
        uploaded_file.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))

def validate_image(stream):
    header = stream.read(512)  # 512 bytes should be enough for a header check
    stream.seek(0)  # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

@bp.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(current_app.config['UPLOAD_PATH'], filename)

