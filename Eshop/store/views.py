from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models.product import *
from .models.Cart import Cart
from .models.Category import *
from .models.customer import Customer 
from django.views import View
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from django.http import JsonResponse
from django.conf import settings

load_dotenv()
stripe.api_key = "sk_test_51NcB...actual_key"
stripe.api_key = settings.STRIPE_SECRET_KEY



# Stripe Webhook
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    # Process events
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        cart = Cart.objects.filter(stripe_session_id=payment_intent['id']).first()
        if cart:
            cart.status = 'paid'
            cart.save()
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        cart = Cart.objects.filter(stripe_session_id=payment_intent['id']).first()
        if cart:
            cart.status = 'failed'
            cart.save()

    return HttpResponse(status=200)

# Checkout View to create Stripe session
import stripe

stripe.api_key = 'your_stripe_secret_key'

class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        try:
            # Assuming the price is passed as a floating point value (e.g., 89900.00)
            price_in_dollars = 89900.00
            
            # Convert the price to cents (integer)
            amount_in_cents = int(price_in_dollars * 100)

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Product Name',
                            },
                            'unit_amount': amount_in_cents,  # Amount in cents
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/success/'),
                cancel_url=request.build_absolute_uri('/cancel/'),
            )

            return redirect(session.url, code=303)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


def index(request):
    products = None
    categories = Category.get_all_categories()
    category_id = request.GET.get('category')
    query = request.GET.get('search')
    
    # Get the cart count for logged-in users
    cart_count = 0
    if request.session.get('user_id'):  # Check if the user is logged in
        customer = Customer.objects.get(id=request.session['user_id'])
        cart_count = Cart.objects.filter(customer=customer).count()  # Get the number of items in the cart

    if category_id:
        products = Product.get_all_products_by_categoryid(category_id)
    elif query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.get_all_products()

    data = {
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
    }

    return render(request, 'index.html', data)

# Signup View
def signup(request):
    if request.method == "POST":
        # Get the form data
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if email already exists
        if Customer.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered. Please log in.")
            return redirect('signup')

        # Hash the password
        hashed_password = make_password(password)

        # Create and save the customer
        customer = Customer(first_name=first_name, last_name=last_name, phone=phone, email=email, password=hashed_password)
        customer.save()

        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')

    return render(request, 'signup.html')

# Login View
def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate customer
        customer = Customer.objects.filter(email=email).first()
        if customer:
            if check_password(password, customer.password):  # Check hashed password
                # Store customer details in session
                request.session['user_id'] = customer.id
                request.session['user_name'] = customer.first_name
                messages.success(request, f"Welcome {customer.first_name}!")
                return redirect('index')
            else:
                messages.error(request, "Invalid password. Please try again.")
        else:
            messages.error(request, "Invalid email. Please try again.")

    return render(request, 'login.html')

# Logout View
def logout(request):
    # Clear the session
    request.session.clear()
    messages.success(request, "You have been logged out.")
    return redirect('login')

# Add to Cart View
def add_to_cart(request, product_id):
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in first!")
        return redirect('login')

    # Get the logged-in user
    customer = Customer.objects.get(id=request.session['user_id'])

    try:
        # Get the product to add to the cart
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product does not exist.")
        return redirect('index')

    # Check if the product is already in the cart
    cart_item, created = Cart.objects.get_or_create(customer=customer, product=product)

    if not created:
        # If the item exists, update the quantity
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Added one more {product.name} to your cart.")
    else:
        messages.success(request, f"Added {product.name} to your cart.")

    return redirect('index')

# View Cart
def view_cart(request):
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in first!")
        return redirect('login')

    customer = Customer.objects.get(id=request.session['user_id'])
    cart_items = Cart.objects.filter(customer=customer)

    total_price = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

# Remove Item from Cart
def remove_from_cart(request, cart_item_id):
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in first!")
        return redirect('login')

    customer = Customer.objects.get(id=request.session['user_id'])
    
    try:
        cart_item = Cart.objects.get(id=cart_item_id, customer=customer)
        cart_item.delete()
        messages.success(request, "Product removed from the cart.")
    except Cart.DoesNotExist:
        messages.error(request, "Item not found in your cart.")

    return redirect('view_cart')

# Stripe Checkout View
class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, "You need to log in first!")
            return redirect('login')

        customer = Customer.objects.get(id=request.session['user_id'])
        cart_items = Cart.objects.filter(customer=customer)

        total_amount = sum(item.total_price() for item in cart_items)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.product.name,
                        },
                        'unit_amount': item.product.price * 100,  # Convert to cents
                    },
                    'quantity': item.quantity,
                }
                for item in cart_items
            ],
            mode='payment',
            success_url=request.build_absolute_uri('/payment-success/'),
            cancel_url=request.build_absolute_uri('/payment-cancelled/'),
        )

        # Store the stripe session ID in the cart
        for item in cart_items:
            item.stripe_session_id = session.id
            item.save()

        return redirect(session.url, code=303)

# Payment Success View
class PaymentSuccessView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'payment_success.html')

# Payment Cancelled View
class PaymentCancelledView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'payment_cancelled.html')
