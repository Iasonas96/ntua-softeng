import pytest
from app.models import User
from tests.utils import *
from tests import data
import json


class TestBasic(object):

    @staticmethod
    def user1_token():
        return User.query.filter(User.username == data.users[1]['username']).first().token

    @staticmethod
    def user1():
        return data.users[1]

    @pytest.mark.parametrize("user_data", data.users)
    def test_register(self, client, user_data):
        rv = client.post(url_for('/register'))
        assert rv.status_code == 400
        
        rv = client.post(url_for('/register'), data=user_data)
        assert rv.status_code == 200
        assert User.query.filter(User.username == user_data['username']).first() is not None
        assert User.query.filter(User.username == user_data['username']).first().verify_password(user_data['password'])
        assert User.query.filter(User.username == user_data['username']).first().is_admin is False
        assert User.query.filter(User.username == user_data['username']).first().token is None

        rv = client.post(url_for('/register'), data=user_data)
        assert rv.status_code == 400

    def test_login(self, client):
        rv = client.post(url_for('/login'))
        assert rv.status_code == 400

        rv = client.post(url_for('/login'), data=self.user1())
        assert rv.status_code == 200
        assert rv.json['token'] == User.query.filter(User.username == data.users[1]['username']).first().token

    @pytest.mark.parametrize("product_data", data.products)
    def test_add_product(self, client, product_data):
        rv = client.post(
            url_for('/products'),
            headers=auth_header(self.user1_token()),
            data=product_data
        )
        assert rv.status_code == 200
        valid_response(product_data, rv.json)

    def test_list_products(self, client):
        rv = client.get(
            url_for('/products'),
            query_string={
                'start': 0,
                'count': 10,
                'status': 'ACTIVE',
                'sort': 'id|ASC'
            },
            headers=auth_header(self.user1_token())
        )

        assert rv.status_code == 200
        assert rv.json['start'] == 0
        assert rv.json['count'] == 10
        assert rv.json['total'] == 2
        assert len(rv.json['products']) == 2
        for i, product in enumerate(data.products):
            valid_response(product, rv.json['products'][i])

    def test_update_product(self, client):
        prod1upd = data.products[0].copy()
        prod1upd.update({
            "name": 'bar-foo',
            "description": '4217a'
        })

        rv = client.put(
            url_for("/products/1"),
            headers=auth_header(self.user1_token()),
            data=prod1upd
        )

        assert rv.status_code == 200
        valid_response(prod1upd, rv.json)

    def test_get_product(self, client):
        rv = client.get(
            url_for("/products/2"),
            headers=auth_header(self.user1_token())
        )

        assert rv.status_code == 200
        valid_response(data.products[1], rv.json)

    def test_patch_product(self, client):
        prod2patch = data.products[1].copy()
        prod2patch.update({'tags': ['nope']})
        rv = client.patch(
            url_for("/products/2"),
            headers=auth_header(self.user1_token()),
            data={'tags': prod2patch['tags']}
        )

        assert rv.status_code == 200
        valid_response(prod2patch, rv.json)

    def test_delete_product(self, client):
        rv = client.delete(
            url_for("/products/2"),
            headers=auth_header(self.user1_token())
        )

        assert rv.status_code == 200
        assert rv.json['message'] == "OK"

    @pytest.mark.parametrize("shop_data", data.shops)
    def test_add_shop(self, client, shop_data):
        rv = client.post(
            url_for('/shops'),
            headers=auth_header(self.user1_token()),
            data=shop_data
        )

        assert rv.status_code == 200
        valid_response(shop_data, rv.json)

    def test_list_shops(self, client):
        rv = client.get(
            url_for('/shops'),
            query_string={
                'start': 0,
                'count': 10,
                'status': 'ACTIVE',
                'sort': 'id|ASC'
            },
            headers=auth_header(self.user1_token())
        )

        assert rv.status_code == 200
        assert rv.json['start'] == 0
        assert rv.json['count'] == 10
        assert rv.json['total'] == 2
        assert len(rv.json['shops']) == 2
        for i, shop_data in enumerate(data.shops):
            valid_response(shop_data, rv.json['shops'][i])

    def test_update_shop(self, client):
        shop1upd = data.shops[0].copy()
        shop1upd.update({
            "name": 'baz-foo',
            "lng": 420
        })

        rv = client.put(
            url_for("/shops/1"),
            headers=auth_header(self.user1_token()),
            data=shop1upd
        )

        assert rv.status_code == 200
        valid_response(shop1upd, rv.json)

    def test_get_shop(self, client):
        rv = client.get(
            url_for("/shops/2"),
            headers=auth_header(self.user1_token())
        )

        assert rv.status_code == 200
        valid_response(data.shops[1], rv.json)

    def test_patch_shop(self, client):
        shop2patch = data.shops[1].copy()
        shop2patch.update({'lat': 99})
        rv = client.patch(
            url_for("/shops/2"),
            headers=auth_header(self.user1_token()),
            data={'lat': shop2patch['lat']}
        )

        assert rv.status_code == 200
        valid_response(shop2patch, rv.json)

    def test_delete_shop(self, client):
        rv = client.delete(
            url_for("/shops/2"),
            headers=auth_header(self.user1_token())
        )

        assert rv.status_code == 200
        assert rv.json['message'] == "OK"

    def test_logout(self, client):

        rv = client.post(url_for('/logout'))
        assert rv.status_code == 403

        rv = client.post(url_for('/logout'), headers=auth_header(self.user1_token()))

        assert rv.status_code == 200
        assert not self.user1_token()
        assert rv.json['message'] == "OK"


with open('test-data.json') as f:
        RDATA = json.load(f)


@pytest.mark.usefixtures('root')
class TestRobot(object):
    token = None
    productIds = []
    shopIds = []

    def test_login(self, client):
        rv = client.post(url_for('/login'), data={
            'username': 'root',
            'password': 'root'
        })
        assert rv.status_code == 200
        assert rv.json['token'] == self.root_token()
        TestRobot.token = rv.json['token']

    @staticmethod
    def root_token():
        return User.query.filter(User.username == 'root').first().token

    @pytest.mark.parametrize("product", RDATA['products'])
    def test_post_product(self, client, product):
        rv = client.post(
            url_for('/products'),
            headers=auth_header(TestRobot.token),
            data=product
        )
        assert rv.status_code == 200
        valid_response(product, rv.json)
        assert not rv.json['withdrawn']
        TestRobot.productIds.append(rv.json['id'])

    @pytest.mark.parametrize("query", RDATA['products_queries'])
    def test_get_product(self, client, query):
        rv = client.get(
            url_for('/products'),
            query_string=query,
            headers=auth_header(TestRobot.token)
        )
        assert rv.status_code == 200
        assert rv.json['start'] == 0
        assert rv.json['total'] == len(query['results'])
        assert query['results'] == [x['name'] for x in rv.json['products']]

    @pytest.mark.parametrize("shop", RDATA['shops'])
    def test_post_shop(self, client, shop):
        rv = client.post(
            url_for('/shops'),
            headers=auth_header(TestRobot.token),
            data=shop
        )
        assert rv.status_code == 200
        valid_response(shop, rv.json)
        assert not rv.json['withdrawn']
        TestRobot.shopIds.append(rv.json['id'])

    @pytest.mark.parametrize("query", RDATA['shops_queries'])
    def test_get_shops(self, client, query):
        rv = client.get(
            url_for('/shops'),
            query_string=query,
            headers=auth_header(TestRobot.token)
        )
        assert rv.status_code == 200
        assert rv.json['start'] == 0
        assert rv.json['total'] == len(query['results'])
        assert query['results'] == [x['name'] for x in rv.json['shops']]

    @pytest.mark.parametrize("price", RDATA['prices'])
    def test_post_price(self, client, price):
        price['productId'] = TestRobot.productIds[price['productIndex']]
        price['shopId'] = TestRobot.productIds[price['shopIndex']]
        rv = client.post(
            url_for('/prices'),
            headers=auth_header(TestRobot.token),
            data=price
        )
        assert rv.status_code == 200
        for pr in rv.json['prices']:
            assert pr['price'] == price['price']
            assert pr['shopId'] == price['shopId']
            assert pr['productId'] == price['productId']

    @pytest.mark.parametrize("query", RDATA['prices_queries'])
    def test_get_shops(self, client, query):
        query['shops'] = [TestRobot.shopIds[x] for x in query['shopIndexes']]
        query['products'] = [TestRobot.productIds[x] for x in query['productIndexes']]
        rv = client.get(
            url_for('/prices'),
            query_string=query,
            headers=auth_header(TestRobot.token)
        )
        assert rv.status_code == 200
        assert rv.json['start'] == query['results']['start']
        assert rv.json['count'] == query['results']['count']
        assert rv.json['total'] == query['results']['total']
        for resp, real in zip(rv.json['prices'], query['results']['prices']):
            assert resp['price'] == real['price']
            assert resp['date'] == real['date']
            assert resp['shopId'] == TestRobot.shopIds[real['shopIndex']]
            assert resp['productId'] == TestRobot.shopIds[real['productIndex']]

    def test_logout(self, client):
        rv = client.post(
            url_for('/logout'),
            headers=auth_header(TestRobot.token)
        )
        assert rv.status_code == 200
        assert not self.root_token()
