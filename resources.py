import inspect
import json
from collections import OrderedDict
from models import Ad, session
from aiohttp.http_exceptions import HttpBadRequest
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from aiohttp.web import Request, Response
from aiohttp.web_urldispatcher import UrlDispatcher

DEFAULT_METHODS = ('GET', 'POST', 'PATCH', 'DELETE')


class RestEndpoint:
    def __init__(self):
        self.methods = {}

        for method_name in DEFAULT_METHODS:
            method = getattr(self, method_name.lower(), None)
            if method:
                self.register_method(method_name, method)

    def register_method(self, method_name, method):
        self.methods[method_name.upper()] = method

    async def dispatch(self, request: Request):
        method = self.methods.get(request.method.upper())
        if not method:
            raise HTTPMethodNotAllowed('', DEFAULT_METHODS)

        wanted_args = list(inspect.signature(method).parameters.keys())
        available_args = request.match_info.copy()
        available_args.update({'request': request})

        unsatisfied_args = set(wanted_args) - set(available_args.keys())
        if unsatisfied_args:
            # Expected match info that doesn't exist
            raise HttpBadRequest('')

        return await method(**{arg_name: available_args[arg_name] for arg_name in wanted_args})


class CollectionEndpoint(RestEndpoint):
    def __init__(self, resource):
        super().__init__()
        self.resource = resource

    async def get(self) -> Response:
        data = []

        ads = session.query(Ad).all()
        for instance in self.resource.collection.values():
            data.append(self.resource.render(instance))
        data = self.resource.encode(data)
        return Response(status=200, body=self.resource.encode({
            'ads': [
                {'id': ad.id, 'title': ad.title, 'description': ad.description,
                 'created_at': ad.created_at, 'author': ad.author}

                for ad in session.query(Ad)

            ]
        }), content_type='application/json')

    async def post(self, request):
        data = await request.json()
        ad = Ad(title=data['title'], description=data['description'], created_at=data['created_at'],
                    author=data['author'])
        session.add(ad)
        session.commit()

        return Response(status=201, body=self.resource.encode(
                {'id': ad.id, 'title': ad.title, 'description': ad.description,
                 'created_at': ad.created_at, 'author': ad.author}
        ), content_type='application/json')


class InstanceEndpoint(RestEndpoint):
    def __init__(self, resource):
        super().__init__()
        self.resource = resource

    async def get(self, instance_id):
        instance = session.query(Ad).filter(Ad.id == instance_id).first()
        if not instance:
            return Response(status=404, body=json.dumps({'not found': 404}), content_type='application/json')
        data = self.resource.render_and_encode(instance)
        return Response(status=200, body=data, content_type='application/json')

    async def patch(self, request, instance_id):

        data = await request.json()

        ad = session.query(Ad).filter(Ad.id == instance_id).first()
        if 'title' in data:
            ad.title = data['title']
        if 'description' in data:
            ad.description = data['description']
        if 'created_at' in data:
            ad.created_at = data['created_at']
        if 'author' in data:
            ad.author = data['author']
        session.add(ad)
        session.commit()

        return Response(status=201, body=self.resource.render_and_encode(ad),
                        content_type='application/json')

    async def delete(self, instance_id):
        ad = session.query(Ad).filter(Ad.id == instance_id).first()
        if not ad:
            return Response(status=404, text="ad {} doesn't exist".format(id))
        session.delete(ad)
        session.commit()
        return Response(status=204)


class RestResource:
    def __init__(self, ads, factory, collection, properties, id_field):
        self.ads = ads
        self.factory = factory
        self.collection = collection
        self.properties = properties
        self.id_field = id_field

        self.collection_endpoint = CollectionEndpoint(self)
        self.instance_endpoint = InstanceEndpoint(self)

    def register(self, router: UrlDispatcher):
        router.add_route('*', '/{ads}'.format(ads=self.ads), self.collection_endpoint.dispatch)
        router.add_route('*', '/{ads}/{{instance_id}}'.format(ads=self.ads), self.instance_endpoint.dispatch)

    def render(self, instance):
        return OrderedDict((ads, getattr(instance, ads)) for ads in self.properties)

    @staticmethod
    def encode(data):
        return json.dumps(data, indent=4).encode('utf-8')

    def render_and_encode(self, instance):
        return self.encode(self.render(instance))
