from distutils.util import strtobool
from webbrowser import get

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
import yaml
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.viewsets import ModelViewSet
from yaml import Loader, FullLoader
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from json import loads as load_json
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, \
    Contact, ConfirmEmailToken, User
from backend.serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderItemSerializer, OrderSerializer, ContactSerializer
from backend.signals import new_user_registered, new_order
from backend.filters import ProductInfoFilter


class PartnerUpdate(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content
                print(type(stream))
                data = yaml.load(stream, Loader=FullLoader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class RegisterUser(APIView):

    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        required_data = ['first_name', 'last_name', 'email', 'password', 'position', 'company', ]
        accepted = True
        for key in required_data:
            if key not in request.data:
                accepted = False

        if accepted:
            errors = {}

            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.data._mutable = True
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    new_user_registered.send(sender=self.__class__, user_id=user.id)
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Wrong Data'})


class ConfirmUser(APIView):

    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):

        required_data = ['email', 'confirm_token']
        accepted = True
        for key in required_data:
            if key not in request.data:
                accepted = False

        if accepted:

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['confirm_token']
                                                     ).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                # email = request.data.get('email')
                # user = User.objects.filter(email=email).first()
                # if user.type == 'shop':
                #     Shop.objects.create(user=user, name=user.company)
                status = {'Status': 'Your email confirmed!'}
                status_code = 200
            else:
                status = {'Status': 'Wrong email or confirm_token'}
                status_code = 400
        else:
            status = {'Status': 'You need to send email and confirm_token'}
            status_code = 400

        return JsonResponse(status, status=status_code)


class UserView(APIView):

    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': 'You are not logged in'}, status=403)

        serializer = UserSerializer(request.user)
        return JsonResponse(serializer.data)


class LoginUser(APIView):

    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        required_data = ['email', 'password']
        accepted = True
        for key in required_data:
            if key not in request.data:
                accepted = False

        if accepted:

            user = authenticate(request,
                                username=request.data['email'],
                                password=request.data['password']
                                )

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    status = {'Status': "logged in", "Token": token.key}
                    status_code = 200

            else:
                status = {'Status': 'Log in failed, check email and password'}
                status_code = 400

        else:
            status = {'Status': 'Log in failed, email and password are needed'}
            status_code = 400

        return JsonResponse(status, status=status_code)


class CategoryViewSet(ModelViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopViewSet(ModelViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Shop.objects.all().filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoViewSet(ModelViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductInfoFilter


class CartView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        cart = Order.objects.filter(
            user_id=request.user.id,
            state='basket'
        ).prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(cart, many=True)
        data = {'data': serializer.data}
        status_code = 200
        return JsonResponse(data, status=status_code)

    def post(self, request):

        positions = request.data.get('positions')
        if positions:
            try:
                positions_dict = load_json(positions)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Wrong request'})
                data = {'Status': 'Wrong request'}
                status_code = 400
            else:
                cart, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                errors = []
                data = {'Status': 'Error occurred'}
                status_code = 400
                for order_position in positions_dict:
                    product_quantity = ProductInfo.objects.filter(id=order_position['product_info']).first().quantity

                    if order_position['quantity'] > product_quantity:
                        error = f"""Add {order_position["product_info"]} failed:
                                    position {order_position["product_info"]} quantity is less than you added.
                                    Please check quantity
                                """
                        errors.append(error)
                    else:
                        order_position.update({'order': cart.id})
                        serializer = OrderItemSerializer(data=order_position)
                        if serializer.is_valid():
                            try:
                                serializer.save()
                                data = {'Status': 'OK'}
                                status_code = 201
                            except IntegrityError as error:
                                data = {'Status': str(error)}
                                status_code = 400

                        else:
                            data = {'Status': serializer.errors}
                            status_code = 400
                            break
                    if errors:
                        data['errors'] = errors

        else:
            data = {'Status': 'Wrong data'}
            status_code = 400
        return JsonResponse(data, status=status_code)

    def delete(self, request):
        positions = request.data.get('positions')
        if positions:
            positions_list = positions.split(',')
            cart, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in positions_list:
                if order_item_id.isdigit():
                    position = OrderItem.objects.filter(order_id=cart.id, id=order_item_id).first()
                    if position:
                        position.delete()
                        objects_deleted = True
                    else:
                        pass

            if objects_deleted:
                data = {'Status': 'Objects deleted'}
                status_code = 200
            else:
                data = {'Status': 'Nothing is deleted'}
                status_code = 200
        else:
            data = {'Status': 'Wrong data'}
            status_code = 400
        return JsonResponse(data, status=status_code)

    def put(self, request):
        objects = request.data.get('positions')
        if objects:
            try:
                objects_dict = load_json(objects)
                cart, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                for order_item in objects_dict:
                    if type(order_item['product_info']) == int and type(order_item['quantity']) == int:

                        OrderItem.objects.filter(order_id=cart.id, id=order_item['product_info']).update(
                            quantity=order_item['quantity'])
                        data = {'Status': 'quantity changed'}
                        status_code = 200
            except ValueError:
                data = {'Status': 'Wrong data'}
                status_code = 400
        else:
            data = {'Status': 'Wrong data'}
            status_code = 400

        return JsonResponse(data, status=status_code)


class PartnerState(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.type != 'shop':
            data = {'Status': 'Only shops can do it'}
            status_code = 403
        else:
            shop = request.user.shop
            serializer = ShopSerializer(shop)
            data = serializer.data
            status_code = 200
        return JsonResponse(data, status=status_code)

    def post(self, request):

        if request.user.type != 'shop':
            data = {'Status': 'Only shops can do it'}
            status_code = 403
        else:
            state = request.data.get('state')
            if state:
                try:
                    Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                    data = {'Status': 'OK'}
                    status_code = 200
                except ValueError as error:
                    data = {'Status': str(error)}
                    status_code = 200
            else:
                data = {'Status': 'Wrong data'}
                status_code = 400
        return JsonResponse(data, status=status_code)


class PartnerOrders(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.type != 'shop':
            data = {'Status': 'Only shops can do it'}
            status_code = 403
        else:
            order = Order.objects.filter(
                ordered_items__product_info__shop__user_id=request.user.id).exclude(state='basket').prefetch_related(
                'ordered_items__product_info__product__category',
                'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
                total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

            serializer = OrderSerializer(order, many=True)
            data = {'data': serializer.data}
            status_code = 200
        return JsonResponse(data, status=status_code)


class ContactView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contacts, many=True)
        data = {'data': serializer.data}
        status_code = 200
        return JsonResponse(data, status=status_code)

    def post(self, request):

        required_data = ['city', 'street', 'phone']
        accepted = True
        for key in required_data:
            if key not in request.data:
                accepted = False
        if accepted:
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                data = {'data': 'Address added successfully'}
                status_code = 201
            else:
                data = {'data': serializer.errors}
                status_code = 400
        else:
            data = {'data': f'Wrong data. Required fields: {required_data}'}
            status_code = 400

        return JsonResponse(data, status=status_code)

    def delete(self, request):
        objects = request.data.get('items')
        if objects:
            addresses = objects.split(',')
            query = Contact.objects.filter(user_id=request.user.id, id__in=addresses)
            if not query:
                data = {'data': 'addresses are not deleted. Check addresses id'}
                status_code = 400
            else:
                str_query = [str(instance) for instance in query]
                query.delete()
                serializer = ContactSerializer(data=query)
                if serializer.is_valid():
                    serializer.save()
                data = {'data': {'deleted_addresses': str_query}}
                status_code = 200
        else:
            data = {'data': 'Wrong data. Required fields: items'}
            status_code = 400
        return JsonResponse(data, status=status_code)

    def put(self, request):

        id = request.data.get('id', None)
        if id:
            if id.isdigit():
                contact = Contact.objects.filter(id=id, user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact, data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        data = {'data': 'Address changed successfully'}
                        status_code = 200
                    else:
                        data = {'data': serializer.errors}
                        status_code = 400
                else:
                    data = {'data': 'Wrong data. No contact found with such id'}
                    status_code = 400
            else:
                data = {'data': 'Wrong data. id must be digit'}
                status_code = 400
        else:
            data = {'data': 'Wrong data. Required data : id.'}
            status_code = 400

        return JsonResponse(data, status=status_code)


class OrderView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        order = Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        data = {'data': serializer.data}
        status_code = 200
        return JsonResponse(data, status=status_code)

    def post(self, request):
        required_data = ['id', 'contact']
        if not request.user.is_authenticated:
            data = {'Status': 'Log in required'}
            status_code = 401
        else:
            accepted = True
            for key in required_data:
                if key not in request.data:
                    accepted = False
            if accepted:
                id = request.data.get('id', None)
                if id.isdigit():
                    try:

                        is_updated = Order.objects.filter(
                            user_id=request.user.id, id=id).update(
                            contact_id=request.data['contact'],
                            state='new')
                        if is_updated:
                            order = Order.objects.filter(user_id=request.user.id, id=id).first()
                            user_id = request.user.id
                            new_order.send(sender=self.__class__, order=order, user_id=user_id)
                            data = {'data': 'Order created'}
                            status_code = 201
                    except IntegrityError as error:
                        data = {'data': str(error)}
                        status_code = 400
                else:
                    data = {'data': 'id must be digit'}
                    status_code = 400
            else:
                data = {'Status': 'Wrong data'}
                status_code = 400

        return JsonResponse(data, status=status_code)
