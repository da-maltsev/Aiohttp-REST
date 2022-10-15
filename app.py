from aiohttp.web import Application, run_app

from resources import RestResource
from models import Ad

ads = {}
app = Application()
person_resource = RestResource('ads', Ad, ads, ('title', 'description', 'created_at', 'author'), 'title')
person_resource.register(app.router)

if __name__ == '__main__':
    run_app(app)
