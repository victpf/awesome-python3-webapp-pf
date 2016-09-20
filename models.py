from backup_Async_orm_metaclass import Model, StringField, TextField, FloatField, IntegerField, BooleanField
from backup_Async_orm_metaclass import execute,create_pool,destory_pool
import asyncio
import aiomysql
import logging
import time,uuid

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    passwd = StringField(column_type='varchar(50)')
    admin = BooleanField()
    name = StringField(column_type='varchar(50)')
    image = StringField(column_type='varchar(500)')
    created_at = FloatField(default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    user_image = StringField(column_type='varchar(500)')
    name = StringField(column_type='varchar(50)')
    summary = StringField(column_type='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    blog_id = StringField(column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    user_image = StringField(column_type='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)
#这里边如果只定义一个test函数而没有后面的loop代码，那么这个函数实际上是不会执行的，他只会创建这个u实例，必须使用event_loop来执行这个task
async def test():
    await create_pool(loop,user = 'root',password = 'songj883',db = 'test1',host = '127.0.0.1')
    u = User(id=79,email='victpf@xxx.com',passwd='cw819142',admin=True,name='pf3',image='image9')
    await u.save()
    await destory_pool()

async def blog_test():
    await create_pool(loop,user = 'root',password = 'songj883',db = 'test1',host = '127.0.0.1')
    u = Blog(id=78,user_id='pf',user_name='Duola32',user_image='blog_image',name='bmp',summary='this is the first one',content='xxxxxxxxxxxxxxxxxx')
    await u.save()
    await destory_pool()

async def blog_comment_test():
    await create_pool(loop,user = 'root',password = 'songj883',db = 'test1',host = '127.0.0.1')
    u = Comment(id=77,blog_id='First blog',user_id='pf',user_name='Duola32',user_image='blog_image',name='bmp',content='xxxxxxxxxxxxxxxxxx')
    await u.save()
    await destory_pool()

loop = asyncio.get_event_loop()
tasks=[blog_comment_test(),blog_test(),test()]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()

