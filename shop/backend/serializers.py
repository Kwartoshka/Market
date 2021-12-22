from rest_framework import serializers

from backend.models import Contact, User, Category, Shop, Product, ProductParameter, ProductInfo, OrderItem, Order


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):

    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = '__all__'


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = '__all__'


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    product_parameters = ProductParameterSerializer(many=True)

    class Meta:

        model = ProductInfo
        fields = ('id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:

        model = OrderItem
        fields = '__all__'


class OrderItemCreateSerializer(OrderItemSerializer):
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):

    ordered_items = OrderItemCreateSerializer(read_only=True, many=True)
    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:

        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'total_sum', 'contact',)
